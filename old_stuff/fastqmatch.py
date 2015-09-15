import argparse
import brenninc_utils
import collections
import HTSeq
import numpy
import os
import sys

_default_qual_scale = "phred"


class EOF():
    def __init__(self):
        self.name = "EOF X"

def notEOF(value):
    return value.name != "EOF X"

def verify_pair(left,right):
    global len_count
    left_split = left.name.split()
    right_split= right.name.split()
    
    if left_split[0] != right_split[0]:
        raise Exception("mismatch", left.name, right.name)
    if left_split[1][1:] != right_split[1][1:]:
        raise Exception("mismatch", left.name, right.name)

l_original_it = None
l_trimmed_it = None
l_unpaired_it = None
r_original_it = None
r_trimmed_it = None
r_unpaired_it = None

l_original = None
r_original = None
l_trimmed = None
r_trimmed = None
l_unpaired = None
r_unpaired = None

def read_original():
    global l_original, r_original
    l_original = l_original_it.next()
    r_original = r_original_it.next()
    verify_pair(l_original, r_original)

def read_trimmed():
    global l_trimmed, r_trimmed
    try:
        l_trimmed = l_trimmed_it.next()
        lfound = True
    except StopIteration:
        lfound = False
        l_trimmed =  EOF()
    try:
        r_trimmed = r_trimmed_it.next()
        if not lfound:
            raise exception ("left trimmed shorter than right trimmed")
    except StopIteration:
        if lfound:
            raise exception ("left trimmed longer than right trimmed")
        l_trimmed =  EOF()
    verify_pair(l_trimmed, r_trimmed)

def nextOrEOF(iter):
    try:
        return iter.next()
    except StopIteration:
        return EOF()

def print_sorted(counter):
    count = 0
    the_sum = 0.0
    for key in sorted(counter):
        #print key, counter[key]
        count += counter[key]
        the_sum += key *counter[key]
    print the_sum/count 
        
def avg(array):
    return int(numpy.average(array))
    
def report_counter(counter, stream):
    for key in sorted(counter):
        stream.write(str(key))  
        stream.write(" ")  
        stream.write(str(counter[key]))
        stream.write("\n")
    
class Dropped():

    def __init__(self, name):
        self.name = name
        self.counter = 0

        self.qual_sum = 0

        self.qual_counts = collections.Counter()
            
    def record(self, original):
        self.counter += 1
        avg_qual = numpy.average(original.qual)
        self.qual_sum += avg_qual
        self.qual_counts[int(avg_qual)] += 1
  
    def summary(self):
        print self.name.rjust(15),
        print "{0:12d} {1:12d}".format(0, self.counter),
        print "{0:8.2f}".format(0),
        print "{0:8.2f}".format(self.qual_sum / self.counter),  
        print "{0:8.2f}".format(0)

    def report(self, stream):
        stream.write(self.name)
        stream.write("\n")  
        stream.write("Dropped ")  
        stream.write(str(self.counter))  
        stream.write("\n")  
        stream.write("Average Qualities \n")  
        report_counter(self.qual_counts, stream)

class Comparison():

    def __init__(self, name):
        self.name = name
        self.unchanged_counter = 0
        self.changed_counter = 0

        self.unchanged_qual_sum = 0
        self.original_qual_sum = 0
        self.changed_qual_sum = 0
        
        self.shorter_count = collections.Counter()    
        self.shorter_sum = 0.0

        self.unchanged_qual_counts = collections.Counter()
        self.original_qual_counts = collections.Counter()
        self.changed_qual_counts = collections.Counter()
            
    def compare(self, original, changed):
        if len(original.seq) == len(changed.seq):
            self.unchanged_counter += 1
            avg_qual = numpy.average(original.qual)
            self.unchanged_qual_sum += avg_qual
            self.unchanged_qual_counts[int(avg_qual)] += 1
        else:
            self.changed_counter += 1
            avg_qual = numpy.average(original.qual)
            self.original_qual_sum += avg_qual
            self.original_qual_counts[int(avg_qual)] += 1
            avg_qual = numpy.average(changed.qual)
            self.changed_qual_sum += avg_qual
            self.changed_qual_counts[int(avg_qual)] += 1
            key = len(original.seq) - len(changed.seq)
            self.shorter_sum += key
            self.shorter_count[key] += 1

    def summary(self):
        print self.name.rjust(15),
        print "{0:12d} {1:12d}".format(self.unchanged_counter, self.changed_counter),
        print "{0:8.2f}".format(self.unchanged_qual_sum / self.unchanged_counter),
        print "{0:8.2f}".format(self.original_qual_sum / self.changed_counter),
        print "{0:8.2f}".format(self.changed_qual_sum / self.changed_counter),  
        print "{0:8.2f}".format(self.shorter_sum / self.changed_counter)
        
    def report(self, stream):
        stream.write(self.name)
        stream.write("\n")  
        stream.write("Unchanged ")  
        stream.write(str(self.unchanged_counter))  
        stream.write("\n")  
        stream.write("Average Qualities \n")  
        report_counter(self.unchanged_qual_counts, stream)
        stream.write("changed ")  
        stream.write(str(self.changed_counter))  
        stream.write("\n")  
        stream.write("Original Average Qualities \n")  
        report_counter(self.original_qual_counts, stream)
        stream.write("New Average Qualities \n")  
        report_counter(self.changed_qual_counts, stream)
        stream.write("Amount Sequence was shortened by\n")  
        report_counter(self.changed_qual_counts, stream)    
         
def matcher(left_fastq, left_trimmed, left_unpaired, 
            right_fastq, right_trimmed, right_unpaired,
            qual_scale=_default_qual_scale):
    global l_original_it, l_trimmed_it, l_unpaired_it
    global r_original_it, r_trimmed_it, r_unpaired_it
    l_original_it = HTSeq.FastqReader(left_fastq, qual_scale).__iter__()
    l_trimmed_it = HTSeq.FastqReader(left_trimmed, qual_scale).__iter__()
    l_unpaired_it = HTSeq.FastqReader(left_unpaired, qual_scale).__iter__()
    r_original_it = HTSeq.FastqReader(right_fastq, qual_scale).__iter__()
    r_trimmed_it = HTSeq.FastqReader(right_trimmed, qual_scale).__iter__()
    r_unpaired_it = HTSeq.FastqReader(right_unpaired, qual_scale).__iter__()

    read_original()
    read_trimmed()
    l_unpaired = nextOrEOF(l_unpaired_it)
    r_unpaired = nextOrEOF(r_unpaired_it)

    left_trimmed = Comparison("Left Trimmed")
    right_trimmed = Comparison("Right Trimmed")
    left_unpaired = Comparison("Left Unpaired")
    right_unpaired = Comparison("Right Unpaired")
    left_dropped = Dropped("Left Dropped")
    right_dropped = Dropped("Right Dropped")
    count = 0
    
    while True:
        count+= 1
        if l_original.name == l_trimmed.name:
            left_trimmed.compare (l_original,l_trimmed)
            right_trimmed.compare (r_original,r_trimmed)
            read_trimmed()                
        else:
            if l_original.name == l_unpaired.name:
                left_unpaired.compare (l_original,l_unpaired)
                if r_original.name == r_unpaired.name:
                    right_unpaired.compare (r_original,r_unpaired)
                    r_unpaired = nextOrEOF(r_unpaired_it)   
                else:
                    right_dropped.record(r_original)
                l_unpaired = nextOrEOF(l_unpaired_it)
            else:   
                left_dropped.record(l_original)
                if r_original.name == r_unpaired.name:
                    right_unpaired.compare (r_original,r_unpaired)
                    r_unpaired = nextOrEOF(r_unpaired_it)                    
                else:
                    right_dropped.record(r_original)
        try:
            read_original()
        except StopIteration:
            break
    
        #if both_dropped_count > 10: print 1/0            
        if count % 100000 == 0:
            print "name               unchanged      changed   unQual   chQual  newQual     lenD"
            left_trimmed.summary()
            right_trimmed.summary()
            left_unpaired.summary()
            right_unpaired.summary()
            left_dropped.summary()
            right_dropped.summary()

    with brenninc_utils.smart_open("../local_data/GR1_HY_Trex1_ACAGTG_summary") as stream:
        left_trimmed.summary()
        right_trimmed.summary()
        left_unpaired.summary()
        right_unpaired.summary()
        left_dropped.summary()
        right_dropped.summary()
        left_trimmed.report(stream)
        right_trimmed.report(stream)
        left_unpaired.report(stream)
        right_unpaired.report(stream)
        left_dropped.report(stream)
        right_dropped.report(stream)
    print "Deatils written to ", "../local_data/GR1_HY_Trex1_ACAGTG_summary"
    
    if notEOF(l_trimmed):
        raise Exception("trimmed not finished")   
    if notEOF(l_unpaired):
        raise Exception("left unpaired not finished")   
    if notEOF(r_unpaired):
        raise Exception("right unpaired not finished")   

if __name__ == '__main__':

    matcher("../local_data/GR1_HY_Trex1_ACAGTG_R1.fastq.gz",
            "../local_data/GR1_HY_Trex1_ACAGTG_R1._trimmed.fastq.gz",
            "../local_data/GR1_HY_Trex1_ACAGTG_R1._unpaired.fastq.gz",
            "../local_data/GR1_HY_Trex1_ACAGTG_R2.fastq.gz",
            "../local_data/GR1_HY_Trex1_ACAGTG_R2._trimmed.fastq.gz",
            "../local_data/GR1_HY_Trex1_ACAGTG_R2._unpaired.fastq.gz")   

