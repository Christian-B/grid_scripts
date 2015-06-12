import argparse
import brenninc_utils
import heapq
import HTSeq
import itertools
import numpy
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


if __name__ == '__main__':
    #sorter = Sorter("example_data/GR1_HY_Trex1_ACAGTG_R1_head100.fastq")
    sorter = Sorter("example_data/GR1_HY_Trex1_ACAGTG_R1.fastq.gz")
    sorter.sort()
