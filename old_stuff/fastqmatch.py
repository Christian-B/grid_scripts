import argparse
import brenninc_utils
import brenninc_comp_counter
import collections
import HTSeq
import os
import sys

_default_qual_scale = "phred"


len_count = 0

def match(left,right):
    global len_count
    left_split = left.name.split()
    right_split= right.name.split()
    
    if left_split[0] != right_split[0]:
        print "mismatch"
        print left.name
        print right.name
        sys.exit(0)
    if left_split[1][1:] != right_split[1][1:]:
        print "mismatch"
        print left.name
        print right.name
        sys.exit(0)
    if len(left.seq) != len(right.seq):
        len_count += 1
        """
        print "len difference"
        print left.name
        print left
        print right.name
        print right
        sys.exit(0)
        """

def matcher(left_fastq, right_fastq, qual_scale=_default_qual_scale):
    left_reader = HTSeq.FastqReader(left_fastq, qual_scale)
    left_iterator = left_reader.__iter__()
    right_reader = HTSeq.FastqReader(right_fastq, qual_scale)
    right_iterator = right_reader.__iter__()
    count = 0;
    
    while True:
        left = left_iterator.next()
        right = right_iterator.next()
        count += 1
        if count % 100000 == 0:
            print count, len_count,  len_count*100.0/count
        match(left, right)    
    
    
if __name__ == '__main__':

    matcher("example_data/GR1_HY_Trex1_ACAGTG_R1.fastq.gz",
          "example_data/GR1_HY_Trex1_ACAGTG_R2.fastq.gz")     
    
    

