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
Creates a new file by inserting the extra into the old path.
Splits the path into dirname, filename and extensions
Returns outputdir + filename + extra + extensions + gzipbit

Where dirname is everything up to the last "/" or "\\"
filename is everything after the the last "/" or "\\" until the first "."
extensions is everthing after the file name except a possible '.gz' end
gzipbit depends on the setting of gzipped and is the original ends with '.gz'

If outputdir is None dirname is used for outputdir
IE the new file is in the same directory as the old one
"""


def create_new_file(path, extra, outputdir=None, gzipped=None):
    slash_index = path.rfind("/")
    if slash_index < 0:
        #Try windows divisor
        slash_index = path.rfind("\\")
    if slash_index < 0:
        #Ok no directory part
        slash_index = 0
    else:
        #skip the slash. Will add back later just once
        slash_index += 1    
    dot_index = path.find(".",slash_index)      
    if dot_index < 0:
        #Ok no extension
        dot_index = len(path)    
    if path.lower().endswith(".gz"):
        end_pos = len(path) -3
        end_bit = ".gz"
    else:
        end_pos = len(path)
        end_bit = ""
    if gzipped is not None:
        if gzipped:
            end_bit = ".gz"
        else:
            end_bit = ""                    
    if outputdir is None:    
        result = path[:dot_index]
    else:
        if (outputdir.endswith("/") or outputdir.endswith("\\")):
            #remove the slash will add back later just once
            outputdir = outputdir[:-1]
        result = outputdir + "/" + path[slash_index:dot_index]
    result += extra + path[dot_index:end_pos] + end_bit
    return os.path.expanduser(result)

"""
Returns the handle of a file to write to.
Will overwrite an existing file
Takes care of closing the file (if applicable) at the end.

If not file name is provided returns a handle wrapping standard out
"""


@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        try:
            fh = open(filename, 'w')
        except IOError as e:
            print >> sys.stderr, "error opening", filename
            print "error opening", filename
            print >> sys.stderr, "I/O error({0}): {1}".format(e.errno, e.strerror)
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            print >> sys.stderr, "Expected to find file at", os.path.abspath(filename)
            print "Expected to find file at", os.path.abspath(filename)
            if os.path.isdir(filename):
                print >> sys.stderr, "expected a file but received a directory"
                print "expected a file but received a directory" 
            else:
                directory = os.path.abspath(os.path.dirname(filename))
                if os.path.isdir(filename):
                    print >> sys.stderr, "Check the write permissions for", directory
                    print "Check the write permissions for", directory
                else:
                    print >> sys.stderr, "directory", directory, "does not exists"    
                    print "directory", directory, "does not exists"    
            raise e        
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
    try:    
        with smart_open("notHereI_hope/nothere.txt") as bad:
            f.write("oops")
    except IOError as e:
        print "good io error thrown"
        
        
def demo_create_new_file():
    #print create_new_file("test","_more")
    #print create_new_file("test.txt","_more")
    #print create_new_file("test.txt.gz","_more")
    #print create_new_file("test.txt.gz","_more", gzipped=True)
    #print create_new_file("test.txt.gz","_more", gzipped=False)
    #print create_new_file("~/temp/demo/test","_more")
    #print create_new_file("~/temp/demo/test.txt","_more")
    #print create_new_file("~/temp/demo/test.txt.gz","_more")
    print create_new_file("test","_more","../newfolder")
    #print create_new_file("test.txt","_more","../newfolder")
    #print create_new_file("test.txt","_more","../newfolder", gzipped=True)
    #print create_new_file("test.txt","_more","../newfolder", gzipped=False)
    #print create_new_file("test.txt.gz","_more","../newfolder")
    #print create_new_file("~/temp/demo/test","_more","../newfolder")
    #print create_new_file("~/temp/demo/test.txt","_more","../newfolder")
    #print create_new_file("~/temp/demo/test.txt.gz","_more","../newfolder")
   
    
if __name__ == '__main__':
    demo_find_files()
    demo_smart_open()
    demo_create_new_file()
