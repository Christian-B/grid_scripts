import argparse
import brenninc_utils
import HTSeq
import itertools
import numpy
import os

_default_qual_scale = "phred"

def head(fastqs, outputs, sequences=100, qual_scale=_default_qual_scale):
    if len(fastq) != len(output):
        raise ValueError("Length of fastq and output parameters must match")
    for (i, fastq) in enumerate(fastqs):    
        fastq_iterator = HTSeq.FastqReader(fastq, qual_scale)
        with open(outputs[i], 'w') as headFile:
            for sequence in itertools.islice( fastq_iterator, sequences):
                sequence.write_to_fastq_file(headFile)
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--fastq",
                        action='append',
                        help="Paths to fastq file. "
                        "Multiple values allowed but there must be the same "
                        "number of 'fastq' as 'output' files. "
                        "File specified can have any file exension. "
                        "Files ending in '.gz' "
                        "will automatically be unzipped. ")
    parser.add_argument("--output",
                        action='append',
                        help="Paths to where each output should be written. "
                        "Multiple values allowed but there must be the same "
                        "number of 'fastq' as 'output' files. ")
    parser.add_argument("-s", "--sequences",
                        type=int,
                        help="Number of sequences to he included in the head "
                        "Single value will be applied to all  output files "
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
             output=args.output,
             qual_scale=args.qual_scale)

