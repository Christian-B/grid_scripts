import argparse
import brenninc_utils
import collections
import HTSeq
import os

def count_single_file(bam_file, handle):
    print "counting alignments in " + bam_file
    alignment_iterator = HTSeq.BAM_Reader(bam_file)
    all_count = 0
    unaligned_count = 0
    chrom_counter = collections.Counter()
    for alignment in alignment_iterator:
        all_count += 1
        if alignment.iv is None:
            unaligned_count += 1
        else:            
            chrom_counter[alignment.iv.chrom] += 1
    handle.write("Summary for " + bam_file + "\n")
    handle.write("Chrom".rjust(15) + "count".rjust(12) + "\n")
    for chrom in sorted(chrom_counter):  
        handle.write(chrom.rjust(15) + "{0:12d}".format(chrom_counter[chrom]) + "\n")
    handle.write("Unaligned".rjust(15) + "{0:12d}".format(unaligned_count) + "\n")
    handle.write("Total".rjust(15) + "{0:12d}".format(all_count) + "\n")

def count_alignments(path=os.getcwd(), output_file=None):
    files = brenninc_utils.find_files(path, ['bam', 'bam.gz'])
    with brenninc_utils.smart_open(output_file) as handle:
        for bam_file in files:
            count_single_file(bam_file, handle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outputfile",
                        help="Path to where output should be written to. "
                        "If it is a direct a count.txt file will be created"
                        "Default is to use standard output only",
                        default=None)
    parser.add_argument("bam",
                        help="Path to bam file or "
                        "directory of with bam files. "
                        "File specified can have any file exension. "
                        "For directories on files with '.bam' or 'bam.gz' "
                        "will be read. "
                        "Files ending in '.gz' "
                        "will automatically be unzipped. ")

    #group = parser.add_mutually_exclusive_group()
    #group.add_argument('-a', action='store_true')
    #group.add_argument('-b', action='store_true')

    args = parser.parse_args()
    print args
    count_alignments(path=args.bam, output_file=args.outputfile)
