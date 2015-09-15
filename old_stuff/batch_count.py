import brenninc_utils
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


def get_features(gff_filename, is_stranded, feature_type, id_attribute,
                 quiet):
    features = HTSeq.GenomicArrayOfSets("auto", is_stranded)
    counts = {}

    gff = HTSeq.GFF_Reader(gff_filename)
    i = 0
    try:
        for f in gff:
            if f.type == feature_type:
                try:
                    feature_id = f.attr[id_attribute]
                except KeyError:
                    raise ValueError("Feature %s does not contain a '%s' "
                                     "attribute" % (f.name, id_attribute))
                if is_stranded and f.iv.strand == ".":
                    raise ValueError("Feature %s at %s does not have strand "
                                     "information but you are running "
                                     "htseq-count in stranded mode. "
                                     "Use '--stranded=no'." %
                                     (f.name, f.iv))
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
        sys.stderr.write("Warning: No features of type '%s' found.\n" %
                         feature_type)

    return features, counts


def detect_sam_type(filename):
    if filename.endswith(".bam"):
        return "bam"
    if filename.endswith(".sam"):
        return "sam"
    if filename.endswith(".sam.gz"):
        return "sam"
    raise Exception("Unable to autodected type from extension of", filename)


def count_reads(sam_filename, features, counts, samtype, order, forward,
                reverse, overlap_mode, quiet, minaqual, samout, directory):

    def write_to_samout(r, assignment):
        if samoutfile is None:
            return
        if not pe_mode:
            r = (r,)
        for read in r:
            if read is not None:
                samoutfile.write(read.original_sam_line.rstrip() +
                                 "\tXF:Z:" + assignment + "\n")

    if samout != "":
        samoutfile = open(samout, "w")
    else:
        samoutfile = None

    if samtype is None:
        samtype = detect_sam_type(sam_filename)

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
        sys.stderr.write("Error occured when reading beginning "
                         "of SAM/BAM file.\n")
        raise

    try:
        if pe_mode:
            if order == "name":
                read_seq = HTSeq.pair_SAM_alignments(read_seq)
            elif order == "pos":
                read_seq = HTSeq.pair_SAM_alignments_with_buffer(read_seq)
            else:
                raise ValueError("Illegal order specified.")
        if forward:
            empty_forward = 0
            ambiguous_forward = 0
            counts_forward = copy.copy(counts)
        if reverse:
            empty_reverse = 0
            ambiguous_reverse = 0
            counts_reverse = copy.copy(counts)
        notaligned = 0
        lowqual = 0
        nonunique = 0
        i = 0
        for r in read_seq:
            if i > 0 and i % 100000 == 0 and not quiet:
                sys.stderr.write("%d SAM alignment record%s processed.\n" %
                                 (i, "s" if not pe_mode else " pairs"))

            i += 1
            if not pe_mode:
                if not r.aligned:
                    notaligned += 1
                    write_to_samout(r, "__not_aligned")
                    continue
                try:
                    if r.optional_field("NH") > 1:
                        nonunique += 1
                        write_to_samout(r, "__alignment_not_unique")
                        continue
                except KeyError:
                    pass
                if r.aQual < minaqual:
                    lowqual += 1
                    write_to_samout(r, "__too_low_aQual")
                    continue
                if forward:
                    iv_seq_for = (co.ref_iv for co in r.cigar
                                  if co.type == "M" and co.size > 0)
                if reverse:
                    iv_seq_rev = (invert_strand(co.ref_iv) for co in r.cigar
                                  if co.type == "M" and co.size > 0)
            else:
                if r[0] is not None and r[0].aligned:
                    if forward:
                        iv_seq_for = (co.ref_iv for co in r[0].cigar
                                      if co.type == "M" and co.size > 0)
                    if reverse:
                        iv_seq_rev = (invert_strand(co.ref_iv) for co in
                                      r[0].cigar if co.type == "M"
                                      and co.size > 0)
                else:
                    iv_seq_rev = tuple()
                    iv_seq_for = tuple()
                if r[1] is not None and r[1].aligned:
                    if forward:
                        iv_seq_for = (itertools.chain(iv_seq_for,
                                      (invert_strand(co.ref_iv)
                                       for co in r[1].cigar if co.type == "M"
                                       and co.size > 0)))
                    if reverse:
                        iv_seq_rev = itertools.chain(iv_seq_rev, (co.ref_iv
                                                     for co in r[1].cigar
                                                     if co.type == "M"
                                                     and co.size > 0))
                else:
                    if (r[0] is None) or not (r[0].aligned):
                        write_to_samout(r, "__not_aligned")
                        notaligned += 1
                        continue
                try:
                    if ((r[0] is not None and r[0].optional_field("NH") > 1)
                            or (r[1] is not None and
                                r[1].optional_field("NH") > 1)):
                        nonunique += 1
                        write_to_samout(r, "__alignment_not_unique")
                        continue
                except KeyError:
                    pass
                if ((r[0] and r[0].aQual < minaqual) or
                        (r[1] and r[1].aQual < minaqual)):
                    lowqual += 1
                    write_to_samout(r, "__too_low_aQual")
                    continue

            try:
                if overlap_mode == "union":
                    if forward:
                        fs_for = set()
                        for iv in iv_seq_for:
                            if iv.chrom not in features.chrom_vectors:
                                raise UnknownChrom
                            for iv2, fs2 in features[iv].steps():
                                fs_for = fs_for.union(fs2)
                    if reverse:
                        fs_rev = set()
                        for iv in iv_seq_rev:
                            if iv.chrom not in features.chrom_vectors:
                                raise UnknownChrom
                            for iv2, fs2 in features[iv].steps():
                                fs_rev = fs_rev.union(fs2)
                elif (overlap_mode == "intersection-strict" or
                        overlap_mode == "intersection-nonempty"):
                    if forward:
                        fs_for = None
                        for iv in iv_seq_for:
                            if iv.chrom not in features.chrom_vectors:
                                raise UnknownChrom
                            for iv2, fs2 in features[iv].steps():
                                if len(fs2) > 0 or \
                                        overlap_mode == "intersection-strict":
                                    if fs_for is None:
                                        fs_for = fs2.copy()
                                    else:
                                        fs_for = fs_for.intersection(fs2)
                    if reverse:
                        fs_reverse = None
                        for iv in iv_seq_rev:
                            if iv.chrom not in features.chrom_vectors:
                                raise UnknownChrom
                            for iv2, fs2 in features[iv].steps():
                                if len(fs2) > 0 or \
                                        overlap_mode == "intersection-strict":
                                    if fs_rev is None:
                                        fs_rev = fs2.copy()
                                    else:
                                        fs_rev = fs_rev.intersection(fs2)
                else:
                    sys.exit("Illegal overlap mode.")
                if forward:
                    if fs_for is None or len(fs_for) == 0:
                        write_to_samout(r, "__no_feature")
                        empty_forward += 1
                    elif len(fs_for) > 1:
                        write_to_samout(r, "__ambiguous[" +
                                        '+'.join(fs_for) + "]")
                        ambiguous_forward += 1
                    else:
                        write_to_samout(r, list(fs_for)[0])
                        counts_forward[list(fs_for)[0]] += 1
                if reverse:
                    if fs_reverse is None or len(fs_rev) == 0:
                        write_to_samout(r, "__no_feature")
                        empty_reverse += 1
                    elif len(fs_reverse) > 1:
                        write_to_samout(r, "__ambiguous[" +
                                        '+'.join(fs_rev) + "]")
                        ambiguous_reverse += 1
                    else:
                        write_to_samout(r, list(fs_rev)[0])
                        counts_reverse[list(fs_rev)[0]] += 1
            except UnknownChrom:
                write_to_samout(r, "__no_feature")
                empty_forward += 1
                empty_reverse += 1

    except:
        sys.stderr.write("Error occured when processing SAM input (%s):\n" %
                         read_seq_file.get_line_number_string())
        raise

    if not quiet:
        sys.stderr.write("%d SAM %s processed.\n" %
                         (i, "alignments "
                          if not pe_mode else "alignment pairs"))

    if samoutfile is not None:
        samoutfile.close()

    if forward:
        output = brenninc_utils.create_new_file(sam_filename,
                                                "_forward_count",
                                                outputdir=directory,
                                                extension="txt",
                                                gzipped=False)
        used_features_count = 0
        used_features_sum = 0
        print "Forward written to", output
        with open(output, "w") as output_file:
            for fn in sorted(counts_forward.keys()):
                output_file.write("%s\t%d\n" % (fn, counts_forward[fn]))
                used_features_count += 1
                used_features_sum += counts_forward[fn]
            output_file.write("__no_feature\t%d\n" % empty_forward)
            output_file.write("__ambiguous\t%d\n" % ambiguous_forward)
            output_file.write("__too_low_aQual\t%d\n" % lowqual)
            output_file.write("__not_aligned\t%d\n" % notaligned)
            output_file.write("__alignment_not_unique\t%d\n" % nonunique)
        print "Forward features with alignment\t%d" % used_features_count
        print "Forward alignments asigned to feature\t%d" % used_features_sum
        print "__forward_no_feature\t%d" % empty_forward
        print "__forward_ambiguous\t%d" % ambiguous_forward
    if reverse:
        output = brenninc_utils.create_new_file(sam_filename,
                                                "_reverse_count",
                                                outputdir=directory,
                                                extension="txt",
                                                gzipped=False)
        used_features_count = 0
        used_features_sum = 0
        print "Reverse written to", output
        with open(output, "w") as output_file:
            for fn in sorted(counts_reverse.keys()):
                output.write("%s\t%d\n" % (fn, counts_reverse[fn]))
                used_features_count += 1
                used_features_sum += counts_reverse[fn]
            output_file.write("__no_feature\t%d\n" % empty_reverse)
            output_file.write("__ambiguous\t%d\n" % ambiguous_reverse)
            output_file.write("__too_low_aQual\t%d\n" % lowqual)
            output_file.write("__not_aligned\t%d\n" % notaligned)
            output_file.write("__alignment_not_unique\t%d\n" % nonunique)
        print "Reverse features with alignment\t%d" % used_features_count
        print "Reverse alignments asigned to feature\t%d" % used_features_sum
        print "__reverse_no_feature\t%d" % empty_reverse
        print "__reverse_ambiguous\t%d" % ambiguous_reverse
    print "__too_low_aQual\t%d" % lowqual
    print "__not_aligned\t%d" % notaligned
    print "__alignment_not_unique\t%d" % nonunique


def count_reads_in_features(sam_filename, gff_filename, samtype, order,
                            stranded, overlap_mode, feature_type,
                            id_attribute, quiet, minaqual, samout, directory):
    forward = stranded in ["yes", "both"]
    reverse = stranded in ["reverse", "both"]
    is_stranded = stranded != "NO"
    if samout != "" and stranded == "both":
        raise Exception("Output SAM alignment records not supported "
                        "for stranded 'both'")
    if samtype == "bam":
        extensions = [".bam"]
    elif samtype == "sam":
        extensions = [".sam", ".sam.gz"]
    else:
        extensions = [".bam", ".sam", ".sam.gz"]
    files = brenninc_utils.find_files(sam_filename, extensions=extensions,
                                      recursive=True)
    features, counts = get_features(gff_filename, is_stranded, feature_type,
                                    id_attribute, quiet)
    for a_file in files:
        if samout == "auto":
            samout_file = brenninc_utils.create_new_file(sam_filename,
                                                         "_annotated",
                                                         outputdir=directory,
                                                         extension="sam",
                                                         gzipped=False)
        else:
            samout_file = samout
        print "counting", a_file
        count_reads(a_file, features, counts, samtype, order, forward, reverse,
                    overlap_mode, quiet, minaqual, samout_file, directory)


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
