import contextlib
import os
import sys


"""
Converts a path into a list of files.
If the path is a directory
    It returns the list of files with the expected extensions
    An error is thrown is no file found
Else
    A single list with the path is returned
    Here the extension is ignored
"""


#If no extensions provided all files are returned
#Here extensions are assumed to be all lower case
def find_files(directory, extensions=None):
    #print "directory",directory
    if directory.startswith("~"):
        home = os.path.expanduser("~")
        directory = home + "/" + directory[1:]
    files = []
    if os.path.isdir(directory):
        if extensions is None:
            for filename in os.listdir(directory):
                files.append(directory + "/" + filename)
            if len(files) < 1:
                raise Exception("No files found in " + directory)
        else:
            for filename in os.listdir(directory):
                if has_extension(filename, extensions):
                    files.append(directory + "/" + filename)
            if len(files) < 1:
                raise Exception("No files found with extensions " +
                                extensions + " in " + directory)
    else:  # assume it is a file
        #Accept even if not extected extension
        files.append(directory)
    return files


#Here extensions are assumed to be all lower case
def has_extension(path, extensions):
    lower = path.lower()
    for extension in extensions:
        if lower.endswith(extension):
            return True
    return False


def demo_find_files():
    print "All files"
    print find_files(os.getcwd(), extensions=None)
    print "python"
    print find_files(os.getcwd(), extensions=["py"])
    print "text and python"
    print find_files(os.getcwd(), extensions=["txt", ".py"])


"""
Returns the handle of a file to write to.
Will overwrite an existing file
Takes care of closing the file (if applicable) at the end.

If not file name is provided returns a handle wrapping standard out
"""


@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


def demo_smart_open():
    with smart_open("test.txt") as f:
        f.write("This is a test\n")
        print "second test"
        f.write("good bye\n")
    print "closed"
    try:
        f.write("not good\n")
    except:
        print "good"


if __name__ == '__main__':
    demo_find_files()
    demo_smart_open()
