import argparse
import os
import shlex
import subprocess


def find_files(directory, extensions):
    if directory.startswith("~"):
        home = os.path.expanduser("~")
        directory = home + "/" + directory[1:]
    if extensions:
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
        files.append(directory + "/" + filename)
    return files


def make_batch_bash(files, simple_bash,  paired_files=None,
                    outputdir=os.getcwd()):
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
                    if paired_files:
                        batch_file.write("SECOND_PATH=(\n")
                        for file in paired_files:
                            batch_file.write(file + "\n")
                        batch_file.write(")" + "\n")
                elif line.startswith("inputpath=$"):
                    batch_file.write("INDEX=$((SGE_TASK_ID-1))\n")
                    batch_file.write("inputpath=${INPUT_PATH[$INDEX]}\n")
                elif line.startswith("outputdir=$"):
                    batch_file.write("outputdir=" + outputdir + "\n")
                elif line.startswith("secondpath=$"):
                    batch_file.write("INDEX=$((SGE_TASK_ID-1))\n")
                    batch_file.write("secondpath=${SECOND_PATH[$INDEX]}\n")
                else:
                    batch_file.write(line)
    return batch_bash


def pair_finder(files, left_end="R1", right_end="R2"):
    extensions = []
    file_names = []
    for full_file in files:
        slash_index = full_file.rfind("/")
        dot_index = full_file.find(".", slash_index)
        if dot_index == -1:
            dot_index = len(full_file)
        extension = full_file[dot_index+1:]
        file_name = full_file[slash_index+1:dot_index]
        extensions.append(extension)
        file_names.append(file_name)
    pairs = []
    for left in range(0, len(files)):
        if file_names[left].endswith(left_end):
            left_front = file_names[left][:-(len(left_end))]
            for right in range(0, len(files)):
                if file_names[right].endswith(right_end):
                    right_front = file_names[right][:-(len(right_end))]
                    if left_front == right_front:
                        pairs.append((files[left], files[right]))
    return pairs


def extend_and_submit(script,
                      extensions=None,
                      directory=os.getcwd(),
                      outputdir=os.getcwd(),
                      pairends=None):
    files = find_files(directory, extensions)
    if pairends:
        ends = pairends.split(",")
        pairs = pair_finder(files, left_end=ends[0], right_end=ends[1])
        left = [x[0] for x in pairs]
        right = [x[1] for x in pairs]
        batch_bash = make_batch_bash(left, script, paired_files=right,
                                     outputdir=outputdir)
    else:
        batch_bash = make_batch_bash(files, script, outputdir=outputdir)
    command_line = "qsub " + batch_bash
    #command_line = "cat " + batch_bash
    args = shlex.split(command_line)
    print args
    print subprocess.call(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory",
                        help="Directory to find files in. "
                        "Default is currentl directory",
                        default=os.getcwd())
    parser.add_argument("-e", "--extension", action='append',
                        help="Adds an extension to look for. "
                        "Default is all files.",
                        default=[])
    parser.add_argument("-o", "--outputdir",
                        help="Directory to write output to. "
                        "Default is current directory",
                        default=os.getcwd())
    parser.add_argument("-p", "--pairends",
                        help="The Unique part of the names of file pairs. "
                        "This will be two values seperated by a comma "
                        "but without spacing. "
                        "For example 'R1,R2'",
                        default=None)
    parser.add_argument("script",
                        help="The script to extend and then submit to qsub. "
                        "Note sumbitted script will appended with '_batch '"
                        "This will overwrite existing file",
                        default=None)
    args = parser.parse_args()

    print args
    extend_and_submit(args.script,
                      extensions=args.extension,
                      directory=args.directory,
                      outputdir=args.outputdir,
                      pairends=args.pairends)
