import argparse
import HTSeq
import itertools
import numpy
import os


def find_files(directory):
    #print "directory",directory
    if directory.startswith("~"):
        home = os.path.expanduser("~")
        directory = home + "/" + directory[1:]
    files = []
    for filename in os.listdir(directory):
        index = filename.find(".")
        if index > 0:
            extension = filename[index+1:]
            if extension in ['fastq', 'fastq.gz']:
                files.append(directory + "/" + filename)
    return files


#alternative values for qual_scale are "solexa" or "solexa-old"
def summary(fastq_file, qual_scale="phred"):
    fastq_iterator = HTSeq.FastqReader(fastq_file, qual_scale)

    for sequence in itertools.islice(fastq_iterator, 1):
        qualsum = numpy.zeros(len(sequence), numpy.int)
        counts = numpy.zeros((len(sequence), 5), numpy.int)
    nsequence = 0
    for sequence in fastq_iterator:
        qualsum += sequence.qual
        nsequence += 1
        sequence.add_bases_to_count_array(counts)

    return (qualsum / float(nsequence), counts)


def qualLine(avgQual):
    result = ""
    for avg in avgQual:
        result += '{0:2d} '.format(int(round(avg)))
    return result


def percentLine(counts):
    result = ""
    for pos_counts in counts:
        total = sum(pos_counts)
        top = max(pos_counts)
        top_percent = top * 100 / total
        result += '{0:2d} '.format(int(round(top_percent)))
    return result


def doSummaries(directory=os.getcwd(), outputdir=os.getcwd()):
    files = find_files(directory)
    with open(outputdir+'/qualities.txt', 'w') as qualitiesFile:
        with open(outputdir+'/percents.txt', 'w') as precentFile:
            for afile in files:
                print afile
                avgQual, counts = summary(afile, "solexa")
                line = qualLine(avgQual)
                print line
                qualitiesFile.write(line)
                qualitiesFile.write("  ")
                qualitiesFile.write(afile)
                qualitiesFile.write("\n")
                line = percentLine(counts)
                print line
                precentFile.write(line)
                precentFile.write("  ")
                precentFile.write(afile)
                precentFile.write("\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory",
                        help="Directory to find files in. "
                        "Default is currentl directory",
                        default=os.getcwd())
    parser.add_argument("-o", "--outputdir",
                        help="Directory to write output to. "
                        "Default is current directory",
                        default=os.getcwd())
    args = parser.parse_args()
    print args
    doSummaries(directory=args.directory,
                outputdir=args.outputdir)
