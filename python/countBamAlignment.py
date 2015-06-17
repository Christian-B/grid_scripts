import argparse
import brenninc_utils
import HTSeq
import os


def count_single_file(bam_file, handle):
    print "counting alignments in " + sam_file
    alignment_iterator = HTSeq.BAM_Reader(bsam_file)
    count = 0
    for alignment in alignment_iterator:
        count += 1
    handle.write(str(count) + "  " + bam_file + "\n")


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
                        "directory of with sam files. "
                        "File specified can have any file exension. "
                        "For directories on files with '.bam' or 'bam.gz' "
                        "will be read. "
                        "Files ending in '.gz' "
                        "will automatically be unzipped. ")

    args = parser.parse_args()
    print args
    count_alignments(path=args.bam, output_file=args.outputfile)
