import argparse
import brenninc_utils
import heapq
import HTSeq
import os

_default_qual_scale = "phred"
_batch_size = 1000000


class SortingByName():

    def __init__(self, sequence):
        self.sequence = sequence

    def __lt__(self, other):
        return self.sequence.name < other.sequence.name

    def __str__(self):
        return self.sequence.name


def wrap_sequence(filename):
    fastq_iterator = HTSeq.FastqReader(filename).__iter__()
    while True:
        yield SortingByName(fastq_iterator.next())


class Sorter():

    def __init__(self, fastq_file, qual_scale=_default_qual_scale):
        self.fastq_file = fastq_file
        self.qual_scale = qual_scale
        self.batch_number = 0
        self.sorting = False

    def sort(self, outputdir=None):
        if self.sorting:
            raise Exception("Illegal double call to sort")
        self.sorting = True
        self.outputdir = outputdir
        fastq_iterator = HTSeq.FastqReader(self.fastq_file, self.qual_scale)
        sequences = []
        for sequence in fastq_iterator:
            sequences.append(sequence)
            if len(sequences) % _batch_size == 0:
                self.batch_number += 1
                self._sort_and_save(sequences)
                sequences = []
        if len(sequences) % _batch_size != 0:
            if self.batch_number > 0:
                self.batch_number += 1
            self._sort_and_save(sequences)
        if self.batch_number > 0:
            self._merge_sorts()
        self.sorting = False

    def _sort_and_save(self, sequences):
        print "sorting", len(sequences)
        sequences.sort(key=lambda sequence: sequence.name)
        if self.batch_number == 0:
            extra = "_sorted"
        else:
            extra = "_batch" + str(self.batch_number)
        new_path = brenninc_utils.create_new_file(self.fastq_file, extra,
                                                  outputdir=self.outputdir,
                                                  gzipped=False)
        print "writing to", new_path,
        with open(new_path, 'w') as sorted_file:
            for sequence in sequences:
                sequence.write_to_fastq_file(sorted_file)
        print "done"

    def _merge_sorts(self):
        iterators = []
        for i in range(1, self.batch_number):
            extra = "_batch" + str(i)
            new_path = brenninc_utils.create_new_file(self.fastq_file, extra,
                                                      outputdir=self.outputdir,
                                                      gzipped=False)
            iterable = wrap_sequence(new_path)
            iterators.append(iterable)
        big = heapq.merge(*iterators)
        extra = "_sorted"
        new_path = brenninc_utils.create_new_file(self.fastq_file, extra,
                                                  outputdir=self.outputdir,
                                                  gzipped=False)
        print "writing to", new_path
        with open(new_path, 'w') as sorted_file:
            for wrapper in big:
                wrapper.sequence.write_to_fastq_file(sorted_file)
        print "done"

        for i in range(1, self.batch_number):
            extra = "_batch" + str(i)
            new_path = brenninc_utils.create_new_file(self.fastq_file, extra,
                                                      outputdir=self.outputdir,
                                                      gzipped=False)
            os.remove(new_path)


def sort(fastq_file, qual_scale=_default_qual_scale, outputdir=None):
    sorter = Sorter(fastq_file, qual_scale=qual_scale)
    sorter.sort(outputdir=outputdir)


def pathsort(path, outputdir=None, qual_scale=_default_qual_scale):
    files = brenninc_utils.find_files(path, ["fastq", "fastq.gz"])
    for afile in files:
        sort(fastq_file=afile, outputdir=outputdir, qual_scale=qual_scale)

if __name__ == '__main__':
    #sorter = Sorter("example_data/GR1_HY_Trex1_ACAGTG_R1_head100.fastq")
    #sorter = Sorter("example_data/GR1_HY_Trex1_ACAGTG_R1.fastq.gz")
    #sorter.sort()
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outputdirectory",
                        help="Path to where output should be written to. "
                        "If no directpry sorted files written "
                        "in same directory as input"
                        "Default is None ",
                        default=None)
    parser.add_argument("fastq",
                        help="Path to fastq file or "
                        "directory of with fastq files. "
                        "File specified can have any file exension. "
                        "For directories only files with '.fastq' or "
                        "'fastq.gz' "
                        #"Fasta file '.fasta' or 'fasta.gz' work too.
                        "will be read. "
                        "Files ending in '.gz' "
                        "will automatically be unzipped. ")
    parser.add_argument("-q", "--qual_scale",
                        help="Quals scale used for fastq files. "
                        #"No effect of fasta file. "
                        "Default is " + _default_qual_scale,
                        default=_default_qual_scale)
    args = parser.parse_args()
    print args
    pathsort(args.fastq,
             outputdir=args.outputdirectory,
             qual_scale=args.qual_scale)
