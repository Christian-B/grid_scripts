import argparse
import brenninc_utils
import HTSeq
import itertools

_default_qual_scale = "phred"


def head(path, sequences=100,  outputdir=None,
         qual_scale=_default_qual_scale):
    extra = "_head" + str(sequences)
    new_path = brenninc_utils.create_new_file(path, extra, outputdir=outputdir,
                                              gzipped=False)
    fastq_iterator = HTSeq.FastqReader(path, qual_scale)
    with open(new_path, 'w') as headFile:
        for sequence in itertools.islice(fastq_iterator, sequences):
            sequence.write_to_fastq_file(headFile)


def makehead(path, sequences=100, outputdir=None,
             qual_scale=_default_qual_scale):
    files = brenninc_utils.find_files(path, ["fastq", "fastq.gz"])
    for afile in files:
        head(path=afile, sequences=sequences, outputdir=outputdir,
             qual_scale=qual_scale)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outputdirectory",
                        help="Path to where output should be written to. "
                        "If no directpry supplied head files written "
                        "in same directory as input"
                        "Default is None ",
                        default=None)
    parser.add_argument("fastq",
                        help="Path to fastq file or "
                        "directory of with fastq files. "
                        "File specified can have any file exension. "
                        "For directories only files with "
                        "'.fastq' or 'fastq.gz' will be read. "
                        "Files ending in '.gz' "
                        "will automatically be unzipped. ")
    parser.add_argument("-s", "--sequences",
                        type=int,
                        help="Number of sequences to he included in the head "
                        "Default is 100",
                        default=100)
    parser.add_argument("-q", "--qual_scale",
                        help="Quals scale used for fastq files. "
                        #"No effect of fasta file. "
                        "Default is " + _default_qual_scale,
                        default=_default_qual_scale)
    args = parser.parse_args()
    print args
    makehead(args.fastq, sequences=args.sequences,
             outputdir=args.outputdirectory,
             qual_scale=args.qual_scale)
