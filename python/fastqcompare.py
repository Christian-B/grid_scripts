import argparse
import brenninc_utils
import brenninc_comp_counter
import collections
import HTSeq
import os

_default_qual_scale = "phred"


class EOF():
    def __init__(self):
        self.name = "EOF"


class Comparer(brenninc_comp_counter.Comparer):

    def __init__(self, original_fastq, trimmed_fastq, unpaired_fastq,
                 shorter_file, dropped_file,
                 outputdir=os.getcwd(),
                 qual_scale=_default_qual_scale):
        original_reader = HTSeq.FastqReader(original_fastq, qual_scale)
        original_iterator = original_reader.__iter__()
        trimmed_reader = HTSeq.FastqReader(trimmed_fastq, qual_scale)
        trimmed_iterator = trimmed_reader.__iter__()
        unpaired_reader = HTSeq.FastqReader(unpaired_fastq, qual_scale)
        unpaired_iterator = unpaired_reader.__iter__()
        brenninc_comp_counter.Comparer.__init__(self, original_iterator,
                                                trimmed_iterator,
                                                unpaired_iterator)
        self.shorter = collections.Counter()
        self.same = 0
        self.update_factor = 100000
        self.shorter_file = shorter_file
        self.dropped_file = dropped_file

    @staticmethod
    def nextOrEOF(peeker):
        try:
            return peeker.next()
        except StopIteration:
            return EOF()

    @staticmethod
    def notEOF(value):
        return value.name != "EOF"

    @staticmethod
    def match(valueA, valueB):
        return valueA.name == valueB.name

    def update(self):
        print self.value1_count,
        print self.same,
        print "%.2f" % (self.same*100.0/self.value1_count),
        shorter = sum(self.shorter.values())
        print shorter,
        print "%.2f" % (shorter*100.0/self.value1_count),
        print self.only1,
        print "%.2f" % (self.only1*100.0/self.value1_count),
        print self.in1and3,
        print "%.2f" % (self.in1and3*100.0/self.value1_count),
        print self.all3, self.only2, self.only3

    """
    def tripleMatch(self, value1, value2, value3):
        self.all3 += 1
    """

    def matchWithTwo(self, value1, value2):
        if len(value2.seq) < len(value1.seq):
            key = (len(value1.seq), len(value2.seq))
            self.shorter[key] += 1
            self.shorter_file.write(value1.name)
            self.shorter_file.write(" , ")
            self.shorter_file.write(str(len(value1.seq)))
            self.shorter_file.write(" , ")
            self.shorter_file.write(str(len(value2.seq)))
            self.shorter_file.write("\n")
        else:
            self.same += 1

    """
    def matchWithThree(self, value1, value3):
        self.in1and3 += 1
    """

    def unmatchedOne(self, value1):
        self.only1 += 1
        self.dropped_file.write(value1.name)
        self.dropped_file.write("\n")

    """
    def unmatchedTwo(self, value2):
        self.only2 += 1

    def unmatchedThree(self, value3):
        self.only3 += 1
    """

    def finalize(self):
        print "Only 1:", self.only1
        print "Only 2:", self.only2
        print "Only 3:", self.only3
        print "In 1 = 2:", self.same
        print "In 1 > 2:", sum(self.shorter.values())
        print "In 1+3:", self.in1and3
        print "all 3:", self.all3
        #File close done by brenninc_utils.create_new_file

    def print_shorter(self, path=None):
        with brenninc_utils.smart_open(path) as stream:
            for key in sorted(self.shorter):
                stream.write(str(key))
                stream.write(" ")
                stream.write(str(self.shorter[key]))
                stream.write("\n")


def compare(original_fastq, trimmed_fastq, unpaired_fastq,
            outputdir=os.getcwd(), qual_scale=_default_qual_scale):

    shorter_path = brenninc_utils.create_new_file(original_fastq, "_shorter",
                                                  outputdir=outputdir,
                                                  gzipped=False)
    dropped_path = brenninc_utils.create_new_file(original_fastq, "_dropped",
                                                  outputdir=outputdir,
                                                  gzipped=False)
    short_count_path = brenninc_utils.create_new_file(original_fastq,
                                                      "_short_count",
                                                      outputdir=outputdir,
                                                      gzipped=False)
    with open(shorter_path, "w") as shorter_file:
        with open(dropped_path, "w") as dropped_file:
            comparer = Comparer(original_fastq, trimmed_fastq, unpaired_fastq,
                                shorter_file, dropped_file,
                                outputdir=outputdir, qual_scale=qual_scale)
            comparer.do_compare()
            comparer.print_shorter(short_count_path)

if __name__ == '__main__':
    #compare("example_data/GR1_HY_Trex1_ACAGTG_R1_head100.fastq",
    #        "example_data/GR1_HY_Trex1_ACAGTG_R1_head100._trimmed.fastq",
    #        "example_data/GR1_HY_Trex1_ACAGTG_R1_head100._unpaired.fastq",
    #        "example_data")

    #compare("example_data/GR1_HY_Trex1_ACAGTG_R1.fastq.gz",
    #        "example_data/GR1_HY_Trex1_ACAGTG_R1._trimmed.fastq.gz",
    #        "example_data/GR1_HY_Trex1_ACAGTG_R1._unpaired.fastq.gz",
    #"example_data")

    parser = argparse.ArgumentParser()
    parser.add_argument('original',
                        help='Original file input into trimmomatic')
    parser.add_argument('trimmed',
                        help='Trimmed file input from trimmomatic')
    parser.add_argument('unpaired',
                        help='Unpaired file from trimmomatic')
    parser.add_argument("-o", "--outputdirectory",
                        help="Path to where output should be written to. "
                        "Default is current directpory",
                        default=None)
    parser.add_argument("-q", "--qual_scale",
                        help="Quals scale used for fastq files. "
                        #"No effect of fasta file. "
                        "Default is " + _default_qual_scale,
                        default=_default_qual_scale)
    args = parser.parse_args()
    print args
    compare(args.original, args.trimmed, args.unpaired,
            outputdir=args.outputdirectory,
            qual_scale=args.qual_scale)
