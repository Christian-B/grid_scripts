import brenninc_utils
import contextlib
import copy
import HTSeq
import itertools
import optparse
import os.path
import sys
import traceback
import warnings


class UnknownChrom(Exception):
    pass


def invert_strand(iv):
    iv2 = iv.copy()
    if iv2.strand == "+":
        iv2.strand = "-"
    elif iv2.strand == "-":
        iv2.strand = "+"
    else:
        raise ValueError("Illegal strand")
    return iv2


def get_features(gff_filename, stranded, feature_type, id_attribute, quiet):

    features = HTSeq.GenomicArrayOfSets("auto", stranded != "no")
    counts = {}

    gff = HTSeq.GFF_Reader(gff_filename)
    i = 0
    try:
        for f in gff:
            if f.type == feature_type:
                try:
                    feature_id = f.attr[id_attribute]
                except KeyError:
                    msg = "Feature %s does not contain a '%s' attribute"
                    msg = msg % (f.name, id_attribute)
                    raise ValueError(msg)
            if stranded != "no" and f.iv.strand == ".":
                msg = ("Feature %s at %s does not have strand information "
                       "but you are running htseq-count in stranded mode. "
                       "Use '--stranded=no'.") % (f.name, f.iv)
                raise ValueError(msg)
            features[f.iv] += feature_id
            counts[f.attr[id_attribute]] = 0
            i += 1
            if i % 100000 == 0 and not quiet:
                sys.stderr.write("%d GFF lines processed.\n" % i)
    except:
        sys.stderr.write("Error occured when processing GFF file (%s):\n" %
                         gff.get_line_number_string())
        raise

    if not quiet:
        sys.stderr.write("%d GFF lines processed.\n" % i)

    if len(counts) == 0:
        raise Exception("No features of type '%s' found.\n" % feature_type)

    return (features, counts)


@contextlib.contextmanager
def open_sam(sam_filename, samtype):

    if samtype == "sam":
        SAM_or_BAM_Reader = HTSeq.SAM_Reader
    elif samtype == "bam":
        SAM_or_BAM_Reader = HTSeq.BAM_Reader
    else:
        raise ValueError("Unknown input format %s specified." % samtype)

    try:
        if sam_filename != "-":
            read_seq_file = SAM_or_BAM_Reader(sam_filename)
            read_seq = read_seq_file
            first_read = iter(read_seq).next()
        else:
            read_seq_file = SAM_or_BAM_Reader(sys.stdin)
            read_seq_iter = iter(read_seq_file)
            first_read = read_seq_iter.next()
            read_seq = itertools.chain([first_read], read_seq_iter)
        pe_mode = first_read.paired_end
    except:
        msg = "Error occured when reading beginning of SAM/BAM file.\n"
        sys.stderr.write(msg)
        raise

    try:
        yield (pe_mode, read_seq)
    except:
        sys.stderr.write("Error occured when processing SAM input (%s):\n" %
                         read_seq_file.get_line_number_string())
        raise


@contextlib.contextmanager
def get_write_to_samout(samout, pe_mode):
    samoutfile = None

    def ignore(r, assignment):
        pass

    def single_write_to_samout(read, assignment):
        if read is not None:
            samoutfile.write(read.original_sam_line.rstrip() +
                             "\tXF:Z:" + assignment + "\n")

    def paired_write_to_samout(r, assignment):
        for read in r:
            if read is not None:
                samoutfile.write(read.original_sam_line.rstrip() +
                                 "\tXF:Z:" + assignment + "\n")
    try:
        if samout == "":
            yield ignore
        else:
            samoutfile = open(samout, "w")
            if pe_mode:
                yield paired_write_to_samout
            else:
                yield single_write_to_samout
    finally:
        if samoutfile is not None:
            samoutfile.close()

def get_write_to_samout_function(samout, pe_mode):

    samoutfile = samout
    
    def ignore(r, assignment):
        pass

    def single_write_to_samout(read, assignment):
        if read is not None:
            samoutfile.write(read.original_sam_line.rstrip() +
                             "\tXF:Z:" + assignment + "\n")

    def paired_write_to_samout(r, assignment):
        for read in r:
            if read is not None:
                samoutfile.write(read.original_sam_line.rstrip() +
                                 "\tXF:Z:" + assignment + "\n")
    if samout is None:
        return ignore
    else:
        if pe_mode:
            return paired_write_to_samout
        else:
            return single_write_to_samout

class IV_Counter():

    def __init__(self, features, counts, write_to_samout, direction, output_stream, output_file):
        self.empty = 0
        self.ambiguous = 0
        self.notaligned = 0
        self.lowqual = 0
        self.nonunique = 0
        self.counts = copy.copy(counts)
        self.features = features
        self.write_to_samout = write_to_samout
        self.direction = direction
        self.output_stream = output_stream 
        self.output_file = output_file

    def not_aligned(self, read):
        self.notaligned += 1
        self.write_to_samout(read, "__not_aligned")

    def not_unique(self, read):
        self.nonunique += 1
        self.write_to_samout(read, "__alignment_not_unique")

    def too_low_quality(self, read):
        self.lowqual += 1
        self.write_to_samout(read, "__too_low_aQual")

    #def forward_count(self, iv_seq, read):
    #def reverse_count(self, iv_seq, read):
    #def _get_fs(self, iv_seq, read):

    def _count_fs(self, fs, read):
        if fs is None or len(fs) == 0:
            self.write_to_samout(read, "__no_feature")
            self.empty += 1
        elif len(fs) > 1:
            self.write_to_samout(read, "__ambiguous[" + '+'.join(fs) + "]")
            self.ambiguous += 1
        else:
            self.write_to_samout(read, list(fs)[0])
            self.counts[list(fs)[0]] += 1
 
    def results(self):
        print  self.direction, "written to", self.output_file 
        used_features_count = 0
        used_features_sum = 0
        for fn in sorted(self.counts.keys()):
            if self.counts[fn] > 0:
                used_features_count += 1
                used_features_sum += self.counts[fn]
            self.output_stream.write("%s\t%d\n" % (fn, self.counts[fn]))
        self.output_stream.write("__no_feature\t%d\n" % self.empty)
        self.output_stream.write("__ambiguous\t%d\n" % self.ambiguous)
        self.output_stream.write("__too_low_aQual\t%d\n" % self.lowqual)
        self.output_stream.write("__not_aligned\t%d\n" % self.notaligned)
        self.output_stream.write("__alignment_not_unique\t%d\n" % self.nonunique)
        print "__no_feature\t%d" % self.empty
        print "__ambiguous\t%d" % self.ambiguous
        print "__too_low_aQual\t%d" % self.lowqual
        print "__not_aligned\t%d" % self.notaligned
        print "__alignment_not_unique\t%d" % self.nonunique
        print "features with alignment\t%d" % used_features_count
        print "alignments asigned to feature\t%d" % used_features_sum


class Forward_IV_Counter(IV_Counter):

    def forward_count(self, iv_seq, read):
        fs = self._get_fs(iv_seq, read)
        self._count_fs(fs, read)

    def reverse_count(self, iv_seq, read):
        pass

class Reverse_IV_Counter(IV_Counter):

    def forward_count(self, iv_seq, read):
        pass

    def reverse_count(self, iv_seq, read):
        fs = self._get_fs(iv_seq, read)
        self._count_fs(fs, read)

class Both_IV_Counter():

    def __init__(self, forward, reverse):
        self.forward = forward
        self.reverse = reverse

    def not_aligned(self, read):
        self.forward.not_aligned(read)
        self.reverse.not_aligned(read)

    def not_unique(self, read):
        self.forward.not_unique(read)
        self.reverse.not_unique(read)

    def too_low_quality(self, read):
        self.forward.too_low_quality(read)
        self.reverse.too_low_quality(read)

    def forward_count(self, iv_seq, read):
        self.forward.forward_count(iv_seq, read)
        
    def reverse_count(self, iv_seq, read):
        self.reverse.reverse_count(iv_seq, read)

    def results(self):
        self.forward.results()
        self.reverse.results()


class FS_Union():
   def _get_fs(self, iv_seq, read):
        fs = set()
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout(read, "__no_feature")
                self.empty += 1
            for iv2, fs2 in self.features[iv].steps():
                fs = fs.union(fs2)
        return fs


class FS_Strict(IV_Counter):
    def _get_fs(self, iv_seq, read):
        fs = None
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout(read, "__no_feature")
                self.empty += 1
            for iv2, fs2 in self.features[iv].steps():
                if fs is None:
                    fs = fs2.copy()
                else:
                    fs = fs.intersection(fs2)
        return fs


class FS_Nonempty(IV_Counter):
    def _get_fs(self, iv_seq, read):
        fs = None
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout(read, "__no_feature")
                self.empty += 1
            for iv2, fs2 in self.features[iv].steps():
                if len(fs2) > 0:
                    if fs is None:
                        fs = fs2.copy()
                    else:
                        fs = fs.intersection(fs2)
        return fs

class Forward_Union_IV_Counter(Forward_IV_Counter, FS_Union):
    pass
    
class Forward_Strict_IV_Counter(Forward_IV_Counter, FS_Strict):
    pass

class Forward_Nonempty_IV_Counter(Forward_IV_Counter, FS_Nonempty):
    pass

class Reverse_Union_IV_Counter(Reverse_IV_Counter, FS_Union):
    pass
    
class Reverse_Strict_IV_Counter(Reverse_IV_Counter, FS_Strict):
    pass

class Reverse_Nonempty_IV_Counter(Reverse_IV_Counter, FS_Nonempty):
    pass


@contextlib.contextmanager
def iv_counter_factory(features, counts, mode, stranded,
                       forward_output_file, reverse_output_file, 
                       forward_samout, reverse_samout, pe_mode):
    forward_sam_file = None
    reverse_sam_file = None
    forward_output_stream = None
    reverse_output_stream = None
    try:
        if stranded in ["yes", "no", "both"]:
            if forward_samout != "":
                forward_sam_file = open(forward_samout, "w")              
            write_to_samout = forward_sam_func = get_write_to_samout_function(forward_sam_file, pe_mode)
            forward_output_stream = open(forward_output_file, "w")       
            if mode == "union":
                forward = Forward_Union_IV_Counter(features, counts, write_to_samout, "forward", forward_output_stream, forward_output_file)
            elif mode == "intersection-strict":
                forward = Forward_Strict_IV_Counter_Strict(features, counts, write_to_samout, "forward", forward_output_stream, forward_output_file)
            elif mode == "intersection-nonempty":
                forward =  Forward_Nonempty_IV_Counter_Nonempty(features, counts, write_to_samout, "forward", forward_output_stream, forward_output_file)
            else:  
                sys.exit("Illegal overlap mode: " + mode)
        if stranded in ["reverse", "both"]:
            if reverse_samout != "":
                reverse_sam_file = open(reverse_samout, "w")              
            write_to_samout = get_write_to_samout_function(reverse_sam_file, pe_mode)                 
            reverse_output_stream = open(reverse_output_file, "w")       
            if mode == "union":
                reverse = Reverse_Union_IV_Counter(features, counts, write_to_samout, "reverse", reverse_output_stream, reverse_output_file)
            elif mode == "intersection-strict":
                reverse = Reverse_Strict_IV_Counter_Strict(features, counts, write_to_samout, "reverse", reverse_output_stream, reverse_output_file)
            elif mode == "intersection-nonempty":
                reverse =  Reverse_Nonempty_IV_Counter_Nonempty(features, counts, write_to_samout, "reverse", reverse_output_stream, reverse_output_file)
            else:  
                sys.exit("Illegal overlap mode: " + mode)
        if stranded in ["yes", "no"]:
            yield forward
        elif stranded == "reverse":
            yield reverse
        elif stranded == "both":
            yield Both_IV_Counter(forward, reverse)    
        else:
            sys.exit("Illegal stranded: " + stranded)
    finally: 
        if forward_sam_file is not None:
            forward_sam_file.close()
        if reverse_sam_file is not None:
            reverse_sam_file.close()
        if forward_output_stream is not None:
            forward_output_stream.close()
        if reverse_output_stream is not None:
            reverse_output_stream.close()

def count_reads_single(read_seq, counter, order, quiet, minaqual):
    i = 0
    for r in read_seq:
        if i > 0 and i % 100000 == 0 and not quiet:
            sys.stderr.write("%d SAM alignment records processed.\n" % (i))
        i += 1
        if not r.aligned:
            counter.not_aligned(r)
            continue
        try:
            if r.optional_field("NH") > 1:
                counter.not_unique(r)
                continue
        except KeyError:
            pass
        if r.aQual < minaqual:
            counter.too_low_quality(r)
            continue

        iv_seq = (co.ref_iv for co in r.cigar
                  if co.type == "M" and co.size > 0)
        counter.forward_count(iv_seq, r)
        iv_seq = (invert_strand(co.ref_iv) for co in r.cigar 
                  if co.type == "M" and co.size > 0)
        counter.reverse_count(iv_seq, r)

    if not quiet:
        sys.stderr.write("%d SAM alignments processed.\n" % (i))

def count_reads_paired(read_seq, counter, order, quiet, minaqual):

    if order == "name":
        read_seq = HTSeq.pair_SAM_alignments(read_seq)
    elif order == "pos":
        read_seq = HTSeq.pair_SAM_alignments_with_buffer(read_seq)
    else:
        raise ValueError("Illegal order specified.")

    i = 0
    for r in read_seq:
        if i > 0 and i % 100000 == 0 and not quiet:
            msg = "%d SAM alignment record pairs processed.\n" % (i)
            sys.stderr.write(msg)

        i += 1
        if r[0] is not None and r[0].aligned:
            forward_iv_seq = (co.ref_iv for co in r[0].cigar
                              if co.type == "M" and co.size > 0)
            reverse_iv_seq = (invert_strand(co.ref_iv) for co in r[0].cigar
                              if co.type == "M" and co.size > 0)
        else:
            forward_iv_seq = tuple()
            reverse_iv_seq = tuple()
        if r[1] is not None and r[1].aligned:
            rest = (invert_strand(co.ref_iv) for co in r[1].cigar
                    if co.type == "M" and co.size > 0)
            forward_iv_seq = itertools.chain(forward_iv_seq, rest)
            rest = (co.ref_iv for co in r[1].cigar
                    if co.type == "M" and co.size > 0)
            reverse_iv_seq = itertools.chain(reverse_iv_seq, rest)
        else:
            if (r[0] is None) or not (r[0].aligned):
                counter.not_aligned(r)
                continue
        try:
            if (r[0] is not None and r[0].optional_field("NH") > 1) or \
                    (r[1] is not None and r[1].optional_field("NH") > 1):
                counter.non_unique(r)
                continue
        except KeyError:
            pass
        if (r[0] and r[0].aQual < minaqual) or \
                (r[1] and r[1].aQual < minaqual):
            forward_counter.too_low_quality(r)
            continue

        counter.forward_count(forward_iv_seq, r)
        counter.reverse_count(reverse_iv_seq, r)

    if not quiet:
        sys.stderr.write("%d SAM alignment pairs processed.\n" % (i))

def detect_sam_type(filename):
    if filename.endswith(".bam"):
        return "bam"
    if filename.endswith(".sam"):
        return "sam"
    if filename.endswith(".sam.gz"):
        return "sam"
    raise Exception("Unable to autodected type from extension of", filename)


def write_output(counter, original_filename, direction, directory):
    if counter is None:
        return
    output = brenninc_utils.create_new_file(original_filename,
                                            "_" + direction + "_count",
                                            outputdir=directory,
                                            extension="txt",
                                            gzipped=False)
    print direction, "written to", output
    with open(output, "w") as output_file:
        counter.results(output_file)


def count_reads_using_features(sam_filename, features, counts, samtype, order, stranded, 
                            overlap_mode, quiet, minaqual, samout, directory ):
    if samtype is None:
        samtype = detect_sam_type(sam_filename)
    create = brenninc_utils.create_new_file
    forward_output = create(sam_filename, "_forward_count",
                            outputdir=directory, extension="txt", 
                            gzipped=False)
    reverse_output = create(sam_filename, "_reverse_count",
                            outputdir=directory, extension="txt",
                            gzipped=False)
    if samout == "auto":
        forward_samout = create(sam_filename, "_forward_annotated",
                                outputdir=directory, extension="sam",
                                gzipped=False)
        reverse_samout = create(sam_filename, "_reverse_annotated",
                                outputdir=directory, extension="sam",
                                gzipped=False)
    else:
        forward_samout = samout                        
        reverse_samout = samout                        
    with open_sam(sam_filename, samtype) as (pe_mode, read_seq):
        with iv_counter_factory(features, counts, overlap_mode, stranded,
                                 forward_output, reverse_output, 
                                 forward_samout, reverse_samout, pe_mode) as counter:
            if pe_mode:
                pass
                #count_reads_paired(read_seq, forward_counter, reverse_counter, order, 
                #                   quiet, minaqual, write_to_samout )
            else:                
                count_reads_single(read_seq, counter, order, quiet, minaqual)
            counter.results()


def count_reads_in_features(sam_filename, gff_filename, samtype, order,
                            stranded, overlap_mode, feature_type,
                            id_attribute, quiet, minaqual, samout, directory):
    if samtype == "bam":
        extensions = [".bam"]
    elif samtype == "sam":
        extensions = [".sam", ".sam.gz"]
    else:
        extensions = [".bam", ".sam", ".sam.gz"]
    files = brenninc_utils.find_files(sam_filename, extensions=extensions,
                                      recursive=True)
    (features, counts) = get_features(gff_filename, stranded, feature_type,
                                      id_attribute, quiet)
    for a_file in files:
        print "counting", a_file
        count_reads_using_features(a_file, features, counts, samtype, order,
                                   stranded, overlap_mode, quiet, minaqual,
                                   samout, directory)


def main():
    usage = "%prog [options] alignment_file gff_file"
    description = ("This script takes an alignment file in SAM/BAM format "
                   "and a feature file in GFF format and calculates "
                   "for each feature the number of reads mapping to it. "
                   "Adapted from "
                   "w-huber.embl.de/users/anders/HTSeq/doc/count.html.")
    epilog = ("Written by Simon Anders (sanders@fs.tum.de), "
              "European Molecular Biology Laboratory (EMBL). (c) 2010. "
              "Adapted by Christian Brenninkmeijer, "
              "Univeristy of Manchester (c) 2015 "
              "Released under the terms of the GNU General Public License v3. "
              "Part of the 'HTSeq' framework, version ")
    epilog += str(HTSeq.__version__) + "."
    optParser = optparse.OptionParser(usage=usage,  description=description,
                                      epilog=epilog)

    help = ("type of <alignment_file> data, either 'sam' or 'bam' "
            "(default: autodetect)")
    optParser.add_option("-f", "--format", type="choice", dest="samtype",
                         choices=("sam", "bam"), default=None,
                         help=help)

    help = ("'pos' or 'name'. Sorting order of <alignment_file> "
            "(default: name). "
            "Paired-end sequencing data must be sorted either by position "
            "or by read name, and the sorting order must be specified. "
            "Ignored for single-end data.")
    optParser.add_option("-r", "--order", type="choice", dest="order",
                         choices=("pos", "name"), default="name",
                         help=help)

    help = ("whether the data is from a strand-specific assay. "
            "Specify 'yes', 'no', 'reverse', or 'both' "
            "(default: yes). "
            "'reverse' means 'yes' with reversed strand interpretation "
            "'both' meands do 'yes' and 'reversed'.")
    optParser.add_option("-s", "--stranded", type="choice", dest="stranded",
                         choices=("yes", "no", "reverse", "both"),
                         default="yes", help=help)

    help = ("skip all reads with alignment quality lower than the given "
            "minimum value (default: 10)")
    optParser.add_option("-a", "--minaqual", type="int", dest="minaqual",
                         default=10, help=help)

    help = ("feature type (3rd column in GFF file) to be used, "
            "all features of other type are ignored "
            "(default, suitable for Ensembl GTF files: exon)")
    optParser.add_option("-t", "--type", type="string", dest="featuretype",
                         default="exon", help=help)

    help = ("GFF attribute to be used as feature ID "
            "(default, suitable for Ensembl GTF files: gene_id)")
    optParser.add_option("-i", "--idattr", type="string", dest="idattr",
                         default="gene_id", help=help)

    help = ("mode to handle reads overlapping more than one feature "
            "choices: union, intersection-strict, intersection-nonempty; "
            "(default: union)")
    optParser.add_option("-m", "--mode", type="choice", dest="mode",
                         choices=("union", "intersection-strict",
                                  "intersection-nonempty"),
                         default="union", help=help)

    help = ("write out all SAM alignment records into an output "
            "SAM file called SAMOUT, "
            "annotating each line with its feature assignment "
            "(as an optional field with tag 'XF') "
            "A value of 'auto' will causee this/these files "
            "to be automatically created. "
            "Warning any value other than 'auto' is not supported "
            "with stranded='both' or with a directory of aligmnent files")
    optParser.add_option("-o", "--samout", type="string", dest="samout",
                         default="", help=help)

    help = ("Directory to write all output files to. "
            "All files will include the name of the input sam file "
            "plus a extra marker. "
            "Default is to write to the same directory as input.")
    optParser.add_option("-d", "--directory", type="string", dest="directory",
                         default="", help=help)

    optParser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                         help="suppress progress report")  # and warnings" )

    if len(sys.argv) == 1:
        optParser.print_help()
        sys.exit(1)

    (opts, args) = optParser.parse_args()

    if len(args) != 2:
        msg = ": Error: Please provide two arguments.\n"
        sys.stderr.write(sys.argv[0] + msg)
        sys.stderr.write("  Call with '-h' to get usage information.\n")
        sys.exit(1)

    warnings.showwarning = my_showwarning
    try:
        count_reads_in_features(args[0], args[1], opts.samtype, opts.order,
                                opts.stranded, opts.mode, opts.featuretype,
                                opts.idattr, opts.quiet, opts.minaqual,
                                opts.samout, opts.directory)
    except:
        sys.stderr.write("  %s\n" % str(sys.exc_info()[1]))
        code = os.path.basename(traceback.extract_tb(sys.exc_info()[2])[-1][0])
        sys.stderr.write("  [Exception type: %s, raised in %s:%d]\n" %
                         (sys.exc_info()[1].__class__.__name__,
                          code,
                          traceback.extract_tb(sys.exc_info()[2])[-1][1]))
        sys.exit(1)


def my_showwarning(message, category, filename, lineno=None, line=None):
    sys.stderr.write("Warning: %s\n" % message)

if __name__ == "__main__":
    main()