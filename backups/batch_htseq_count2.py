import contextlib
import copy
import sys, optparse, itertools, warnings, traceback, os.path

import HTSeq

class UnknownChrom( Exception ):
   pass
   
def invert_strand( iv ):
   iv2 = iv.copy()
   if iv2.strand == "+":
      iv2.strand = "-"
   elif iv2.strand == "-":
      iv2.strand = "+"
   else:
      raise ValueError, "Illegal strand"
   return iv2

def get_features(gff_filename, stranded, feature_type, id_attribute, quiet):
      
   features = HTSeq.GenomicArrayOfSets( "auto", stranded != "no" )     
   counts = {}
     
   gff = HTSeq.GFF_Reader( gff_filename )   
   i = 0
   try:
      for f in gff:
         if f.type == feature_type:
            try:
               feature_id = f.attr[ id_attribute ]
            except KeyError:
               raise ValueError, ( "Feature %s does not contain a '%s' attribute" % 
                  ( f.name, id_attribute ) )
            if stranded != "no" and f.iv.strand == ".":
               raise ValueError, ( "Feature %s at %s does not have strand information but you are "
                  "running htseq-count in stranded mode. Use '--stranded=no'." % 
                  ( f.name, f.iv ) )
            features[ f.iv ] += feature_id
            counts[ f.attr[ id_attribute ] ] = 0
         i += 1
         if i % 100000 == 0 and not quiet:
            sys.stderr.write( "%d GFF lines processed.\n" % i )
   except:
      sys.stderr.write( "Error occured when processing GFF file (%s):\n" % gff.get_line_number_string() )
      raise
      
   if not quiet:
      sys.stderr.write( "%d GFF lines processed.\n" % i )
      
   if len( counts ) == 0:
      raise Exception( "No features of type '%s' found.\n" % feature_type )
   
   return (features, counts)

@contextlib.contextmanager     
def open_sam(sam_filename, samtype):
      
    if samtype == "sam":
        SAM_or_BAM_Reader = HTSeq.SAM_Reader
    elif samtype == "bam":
        SAM_or_BAM_Reader = HTSeq.BAM_Reader
    else:
        raise ValueError, "Unknown input format %s specified." % samtype

    try:
        if sam_filename != "-":
            read_seq_file = SAM_or_BAM_Reader( sam_filename )
            read_seq = read_seq_file
            first_read = iter(read_seq).next()
        else:
            read_seq_file = SAM_or_BAM_Reader( sys.stdin )
            read_seq_iter = iter( read_seq_file )
            first_read = read_seq_iter.next()
            read_seq = itertools.chain( [ first_read ], read_seq_iter )
        pe_mode = first_read.paired_end
    except:
        sys.stderr.write( "Error occured when reading beginning of SAM/BAM file.\n" )
        raise

    try:
        yield (pe_mode,read_seq)
    except:
        sys.stderr.write( "Error occured when processing SAM input (%s):\n" % read_seq_file.get_line_number_string() )
        raise
 
@contextlib.contextmanager     
def get_write_to_samout(samout, pe_mode): 
    samoutfile = None
    def ignore(r, assignment):
        pass   

    def single_write_to_samout(read, assignment ):
        if read is not None:
            samoutfile.write(read.original_sam_line.rstrip() +
                             "\tXF:Z:" + assignment + "\n" )
      
    def paired_write_to_samout( r, assignment ):
        for read in r:
            if read is not None:
                samoutfile.write(read.original_sam_line.rstrip() +
                                 "\tXF:Z:" + assignment + "\n" )
    try:
        if samout == "":
            yield ignore
        else:       
            samoutfile = open( samout, "w" )
            if pe_mode:
                yield paired_write_to_samout
            else:
                yield single_write_to_samout    
    finally:
        if samoutfile is not None:
            samoutfile.close()

class IV_Counter():

    def __init__(self, features, counts, write_to_samout):
        self.empty = 0
        self.ambiguous = 0
        self.notaligned = 0
        self.lowqual = 0
        self.nonunique = 0
        self.counts = copy.copy(counts)
        self.features = features
        self.write_to_samout = write_to_samout

    def count(self,iv_seq, read):
        fs = self._get_fs(iv_seq, read)
        self._count_fs(fs, read)
 
    def _get_fs(self,iv_seq, read):
        fs = set()
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout( read, "__no_feature" )
                self.empty += 1
            for iv2, fs2 in self.features[ iv ].steps():
                fs = fs.union( fs2 )
        
    def _count_fs(self, fs, read):
        if fs is None or len( fs ) == 0:
            self.write_to_samout( read, "__no_feature" )
            self.empty += 1
        elif len( fs ) > 1:
            self.write_to_samout( read, "__ambiguous[" + '+'.join( fs ) + "]" )
            self.ambiguous += 1
        else:
            self.write_to_samout( read, list(fs)[0] )
            self.counts[ list(fs)[0] ] += 1

    def results(self):
        for fn in sorted( self.counts.keys() ):
            print "%s\t%d" % ( fn, self.counts[fn] )
        print "__no_feature\t%d" % self.empty
        print "__ambiguous\t%d" % self.ambiguous
        print "__too_low_aQual\t%d" % self.lowqual
        print "__not_aligned\t%d" % self.notaligned
        print "__alignment_not_unique\t%d" % self.nonunique

class IV_Counter_Strict(IV_Counter):
    def _get_fs(self,iv_seq, read):
        fs = None
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout( read, "__no_feature" )
                self.empty += 1
            for iv2, fs2 in self.features[ iv ].steps():
                if fs is None:
                    fs = fs2.copy()
                else:
                    fs = fs.intersection( fs2 )

class IV_Counter_Nonempty(IV_Counter):
    def _get_fs(self,iv_seq, read):
        fs = None
        for iv in iv_seq:
            if iv.chrom not in self.features.chrom_vectors:
                self.write_to_samout( read, "__no_feature" )
                self.empty += 1
            for iv2, fs2 in self.features[ iv ].steps():
                if len(fs2) > 0:
                    if fs is None:
                        fs = fs2.copy()
                    else:
                        fs = fs.intersection( fs2 )
          
def count_reads_single(read_seq, counter, order, stranded, 
      quiet, minaqual, write_to_samout ):
      
    i = 0   
    for r in read_seq:
        if i > 0 and i % 100000 == 0 and not quiet:
            sys.stderr.write( "%d SAM alignment record%s processed.\n" % ( i, "s" if not pe_mode else " pairs" ) )

        i += 1
        if not r.aligned:
            counter.notaligned += 1
            write_to_samout( r, "__not_aligned" )
            continue
        try:
            if r.optional_field( "NH" ) > 1:
                counter.nonunique += 1
                write_to_samout( r, "__alignment_not_unique" )
                continue
        except KeyError:
            pass
        if r.aQual < minaqual:
            counter.lowqual += 1
            write_to_samout( r, "__too_low_aQual" )
            continue
        if stranded != "reverse":
            iv_seq = ( co.ref_iv for co in r.cigar if co.type == "M" and co.size > 0 )
        else:
            iv_seq = ( invert_strand( co.ref_iv ) for co in r.cigar if co.type == "M" and co.size > 0 )            
         
        counter.count(iv_seq, r)
         
    #if not quiet:
    #    sys.stderr.write( "%d SAM %s processed.\n" % ( i, "alignments " if not pe_mode else "alignment pairs" ) )
         
def count_reads_paired(read_seq, counter, order, stranded, 
      quiet, minaqual, write_to_samout ):
      
    if order == "name":
        read_seq = HTSeq.pair_SAM_alignments( read_seq )
    elif order == "pos":
        read_seq = HTSeq.pair_SAM_alignments_with_buffer( read_seq )
    else:
        raise ValueError, "Illegal order specified."

    i = 0   
    for r in read_seq:
        if i > 0 and i % 100000 == 0 and not quiet:
            sys.stderr.write( "%d SAM alignment record%s processed.\n" % ( i, "s" if not pe_mode else " pairs" ) )

        i += 1
        if r[0] is not None and r[0].aligned:
            if stranded != "reverse":
                iv_seq = ( co.ref_iv for co in r[0].cigar if co.type == "M" and co.size > 0 )
            else:
                iv_seq = ( invert_strand( co.ref_iv ) for co in r[0].cigar if co.type == "M" and co.size > 0 )
        else:
            iv_seq = tuple()
        if r[1] is not None and r[1].aligned:            
            if stranded != "reverse":
                iv_seq = itertools.chain(iv_seq, 
                    ( invert_strand( co.ref_iv ) for co in r[1].cigar if co.type == "M" and co.size > 0 ) )
            else:
                iv_seq = itertools.chain( iv_seq, 
                    ( co.ref_iv for co in r[1].cigar if co.type == "M" and co.size > 0 ) )
        else:
            if ( r[0] is None ) or not ( r[0].aligned ):
                write_to_samout( r, "__not_aligned" )
                counter.notaligned += 1
                continue         
        try:
            if ( r[0] is not None and r[0].optional_field( "NH" ) > 1 ) or \
                     ( r[1] is not None and r[1].optional_field( "NH" ) > 1 ):
                counter.nonunique += 1
                write_to_samout( r, "__alignment_not_unique" )
                continue
        except KeyError:
            pass
        if ( r[0] and r[0].aQual < minaqual ) or ( r[1] and r[1].aQual < minaqual ):
            lowqual += 1
            write_to_samout( r, "__too_low_aQual" )
            continue         
        
        counter.count(iv_seq, r)
         
    if not quiet:
        sys.stderr.write( "%d SAM %s processed.\n" % ( i, "alignments " if not pe_mode else "alignment pairs" ) )

def main():
   
   optParser = optparse.OptionParser( 
      
      usage = "%prog [options] alignment_file gff_file",
      
      description=
         "This script takes an alignment file in SAM/BAM format and a " +
         "feature file in GFF format and calculates for each feature " +
         "the number of reads mapping to it. Adapted from " +
         "http://www-huber.embl.de/users/anders/HTSeq/doc/count.html." ,
         
      epilog = 
         "Written by Simon Anders (sanders@fs.tum.de), European Molecular Biology " +
         "Laboratory (EMBL). (c) 2010. " + 
         "Adapted by Christian Brenninkmeijer, Univeristy of Manchester (c) 2015 " + 
         "Released under the terms of the GNU General " +
         "Public License v3. Part of the 'HTSeq' framework, version %s." % HTSeq.__version__ )
         
   optParser.add_option( "-f", "--format", type="choice", dest="samtype",
      choices = ( "sam", "bam" ), default = "sam",
      help = "type of <alignment_file> data, either 'sam' or 'bam' (default: sam)" )

   optParser.add_option( "-r", "--order", type="choice", dest="order",
     choices=("pos", "name"), default="name",
     help = "'pos' or 'name'. Sorting order of <alignment_file> (default: name). Paired-end sequencing " +
        "data must be sorted either by position or by read name, and the sorting order " +
        "must be specified. Ignored for single-end data." )

   optParser.add_option( "-s", "--stranded", type="choice", dest="stranded",
     choices = ( "yes", "no", "reverse" ), default = "yes",
     help = "whether the data is from a strand-specific assay. Specify 'yes', " +
        "'no', or 'reverse' (default: yes). " +
        "'reverse' means 'yes' with reversed strand interpretation" )
      
   optParser.add_option( "-a", "--minaqual", type="int", dest="minaqual",
      default = 10,
      help = "skip all reads with alignment quality lower than the given " +
         "minimum value (default: 10)" )
      
   optParser.add_option( "-t", "--type", type="string", dest="featuretype",
      default = "exon", help = "feature type (3rd column in GFF file) to be used, " +
         "all features of other type are ignored (default, suitable for Ensembl " +
         "GTF files: exon)" )
         
   optParser.add_option( "-i", "--idattr", type="string", dest="idattr",
      default = "gene_id", help = "GFF attribute to be used as feature ID (default, " +
      "suitable for Ensembl GTF files: gene_id)" )

   optParser.add_option( "-m", "--mode", type="choice", dest="mode",
      choices = ( "union", "intersection-strict", "intersection-nonempty" ), 
      default = "union", help = "mode to handle reads overlapping more than one feature " +
         "(choices: union, intersection-strict, intersection-nonempty; default: union)" )
         
   optParser.add_option( "-o", "--samout", type="string", dest="samout",
      default = "", help = "write out all SAM alignment records into an output " +
      "SAM file called SAMOUT, annotating each line with its feature assignment " +
      "(as an optional field with tag 'XF')" )

   optParser.add_option( "-q", "--quiet", action="store_true", dest="quiet",
      help = "suppress progress report" ) # and warnings" )

   if len( sys.argv ) == 1:
      optParser.print_help()
      sys.exit(1)

   (opts, args) = optParser.parse_args()

   if len( args ) != 2:
      sys.stderr.write( sys.argv[0] + ": Error: Please provide two arguments.\n" )
      sys.stderr.write( "  Call with '-h' to get usage information.\n" )
      sys.exit( 1 )
      
   warnings.showwarning = my_showwarning
   try:
      (features, counts) = get_features(args[1],
                                        opts.stranded,
                                        opts.featuretype,
                                        opts.idattr,
                                        opts.quiet) 
      with open_sam(args[0], opts.samtype) as (pe_mode, read_seq):
          with get_write_to_samout(opts.samout, pe_mode) as write_to_samout:   
             if opts.mode == "union": 
                 iv_counter = IV_Counter(features, counts, write_to_samout)                                                          
             elif opts.mode == "intersection-strict":
                 iv_counter = IV_Counter_Strict(features, counts, write_to_samout)                                                          
             elif opts.mode == "intersection-nonempty":
                 iv_counter = IV_Counter_Nonempty(features, counts, write_to_samout)                                                          
             else:
                 sys.exit( "Illegal overlap mode." )

             if pe_mode:
                 count_reads_paired(read_seq, iv_counter, opts.order, opts.stranded, 
                             opts.quiet, opts.minaqual, write_to_samout )
             else:                
                 count_reads_single(read_seq, iv_counter, opts.order, opts.stranded, 
                             opts.quiet, opts.minaqual, write_to_samout )
             iv_counter.results()
   except:
      sys.stderr.write( "  %s\n" % str( sys.exc_info()[1] ) )
      sys.stderr.write( "  [Exception type: %s, raised in %s:%d]\n" % 
         ( sys.exc_info()[1].__class__.__name__, 
           os.path.basename(traceback.extract_tb( sys.exc_info()[2] )[-1][0]), 
           traceback.extract_tb( sys.exc_info()[2] )[-1][1] ) )
      sys.exit( 1 )

def my_showwarning( message, category, filename, lineno = None, line = None ):
   sys.stderr.write( "Warning: %s\n" % message )

if __name__ == "__main__":
   main()

