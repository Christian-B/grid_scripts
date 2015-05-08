#Test code for getting files in a directory and writing to a file

import os
from os.path import expanduser
import sys


def path_list(directory, extensions, output):
    with open(output, "w") as output_file:
        for filename in os.listdir(directory):
            index = filename.find(".")
            if index > 0:
                extension = filename[index+1:]
                if extension in extensions:
                    output_file.write(directory + "/" + filename + "\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        home = expanduser("~")
        directory = os.getcwd()
    #path_list(directory, ["fastq", "fastq.gz"], "files.txt")
    path_list(directory, ["zip"], "files.txt")
