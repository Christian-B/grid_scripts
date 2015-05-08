import argparse
import os
import shlex
import subprocess
import sys

def find_files(directory, extensions):
    print "directory",directory
    print "extensions",extensions
    if extensions:
        print "some"
        files = []
        for filename in os.listdir(directory):
            index = filename.find(".")
            if index > 0:
                extension = filename[index+1:]
                if extension in extensions:
                    files.append(directory + "/" + filename)
        return files
    else:
        return all_files(directory)

def all_files(directory):
    files = []
    for filename in os.listdir(directory):
        print filename
        files.append(directory + "/" + filename)
    return files                
    
def make_batch_bash(files, simple_bash, outputdir=os.getcwd()):
    batch_bash = simple_bash + "_batch"
    with open(simple_bash, "r") as simple_file:
        with open(batch_bash, "w") as batch_file:
            for line in simple_file:
                if line.startswith("#codestart"):
                    batch_file.write("#$ -t 1-" + str(len(files)) + "\n")
                    batch_file.write("INPUT_PATH=(\n")
                    for file in files:
                        batch_file.write(file + "\n")
                    batch_file.write(")" + "\n")
                elif line.startswith("inputpath=$"):
                    batch_file.write("INDEX=$((SGE_TASK_ID-1))\n")
                    batch_file.write("inputpath=${INPUT_PATH[$INDEX]}\n")
                elif line.startswith("outputdir=$"):
                    batch_file.write("outputdir=" + outputdir + "\n")                        
                else:
                    batch_file.write(line)
    return batch_bash                

def extend_and_submit(script, extensions=None, directory=os.getcwd()):
    files = find_files(directory, extensions)
    print files
    batch_bash = make_batch_bash(files,script)
    command_line = "qsub "+ batch_bash
    #command_line = "cat "+ batch_bash
    args = shlex.split(command_line)
    print args
    print subprocess.call(args) 
                
if __name__ == '__main__':
    parser = argparse.ArgumentParser()  
    parser.add_argument("-d","--directory", 
                        help="Directory to find files in. "
                        "Default is currentl directory", 
                        default=os.getcwd())
    parser.add_argument("-e","--extension", action='append',
                        help="Adds an extension to look for. "
                        "Default is all files.",
                        default=[])
    parser.add_argument("-o","--outputdir", 
                        help="Directory to write output to. "
                        "Default is current directory", 
                        default=os.getcwd())
    parser.add_argument("script", 
                        help="The script to extend and then submit to qsub. "
                        "Note sumbitted script will appended with '_batch '"
                        "This will overwrite existing file")
    args = parser.parse_args()                        
                        
    print args          
    extend_and_submit(args.script, extensions=args.extension, directory=args.directory)
    
