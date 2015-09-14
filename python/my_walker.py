import filecmp
import optparse  #using optparse as hydra still python 2.6
import os
import re
import shutil

def expanderuser(path):
    if path.startswith("~"):
        return os.path.expanduser("~") + path[1:]
    return path

"""
Name Checker methods
All should take a two parameters
    root is the directory
    name will be without the path
Should return:
    True if the file/directory with this name should be used
    False if the file/directory should be ignored
"""

#Could be used to ignore all subdirectories or all files
def approve_none(root, name, verbose=False):
    return False

def approve_all(root, name, verbose=False):
    return True

def print_size(root, name, verbose=False):
    path = os.path.join(root, name)
    print path, "has size", os.path.getsize(path)

class RegexChecker:
    def __init__(self, regexes=[".*"]):
        self.patterns = []
        for regex in regexes:
            self.patterns.append(re.compile(regex))    

    def approve_name(self, root, name, verbose=False):
        for pattern in self.patterns:
            if pattern.search(name):
                return True
        return False    
        
class DirectoryLister:
    def __init__(self, list_file, ignore_regexes=[], required_files=[], check_path=None, list_path=None):
        self.ignore_patterns = []
        for regex in ignore_regexes:
            self.ignore_patterns.append(re.compile(regex))
        self.required_files = required_files        
        self.check_path = check_path
        self.list_path = list_path
        if self.check_path:
            self.check_path = expanderuser(self.check_path)
            if not self.list_path:
                raise Exception ("if check_path is specified a list_path is required")
            else:
                if self.list_path.startswith("~"):
                    raise Exception ("Do not use ~ in list_path")
        else:        
            if self.list_path:
                raise Exception ("if list_path is specified a check_path is required")
        self.list_file = expanderuser(list_file)
        try:        
            afile = open(list_file, 'w')
            afile.close()       
        except Exception as e:
            print e
            raise Exception ("Unable to open file: "+ list_file)                
            

    def list_directory(self, root, name, verbose=True):
        for pattern in self.ignore_patterns:
            if pattern.search(name):
                #Ignore directory and its children
                return False
        path = os.path.join(root, name)                         
        for required_file in self.required_files:
            required_path = os.path.join(path, required_file)         
            if not os.path.exists(required_path):
                #Ignore directory but check its children!
                print "ignoring",path,"as it is missing",required_file 
                return True
        if self.check_path:
            if path.startswith(self.check_path):
                path = self.list_path + path[len(self.check_path):]
        with open(self.list_file, 'a') as f:
            f.write(path)
            f.write("\n")
        return True
            
    
class Copier:
    def __init__(self, endings_mappings, target_parent=os.getcwd()):
        self.target_parent = expanderuser(target_parent)
        if not os.path.isdir(self.target_parent):
            if os.path.isfile(self.target_parent):
                raise Exception ("target_parent: " + self.target_parent + " is a file.")
            grand_parent = os.path.dirname(os.path.normpath(self.target_parent))
            print grand_parent
            if os.path.isdir(grand_parent):  
                os.mkdir(self.target_parent, 0755);
            if not os.path.isdir(self.target_parent):
                raise Exception ("target_parent: " + target_parent + " does not exist.")                
        self.endings_mappings = {}
        try:
            if len(endings_mappings) == 0:
                raise Exception ("endings_mappings may not be empty")                
        except Exception as e:
            print e
            raise Exception ("endings_mappings must be a dictionary")                
        for (regex, file_name) in endings_mappings.items():
            pattern = re.compile(regex)
            self.endings_mappings[pattern] = file_name
            
    def act_on_files(self, old_path, new_path, verbose=True):
        if os.path.exists(new_path):
            if filecmp.cmp(new_path, old_path):
                print "ignoring existing",new_path
            else:
                raise Exception ("Unwilling to overwrite: " + new_path + " with " + old_path)                
        else:               
            shutil.copy2(old_path, new_path)
        return True

    def file_action(self, root, name, verbose=True):
        for (pattern, file_name) in self.endings_mappings.items():
            match = pattern.search(name)
            if match:
                prefix = name[:match.start()]
                if len(prefix) == 0:
                    raise Exception ("Ending regex: " + pattern.pattern + " was found at start of " + name )
                newdir = os.path.join(self.target_parent, prefix)
                if not os.path.isdir(newdir):
                    os.mkdir(newdir)
                oldpath = os.path.join(root, name)
                newpath = os.path.join(newdir, file_name)
                return self.act_on_files(oldpath, newpath, verbose)
        print "no match found for",name
      
class Linker(Copier):
    def act_on_files(self, old_path, new_path, verbose=True):
        if os.path.exists(new_path):
            with open (new_path, "r") as old_file:
                old_link = old_file.read().replace('\n', '')
            if old_link != old_path:
                raise Exception ("Unwilling overwrite: " + new_path + 
                                 " with " + old_path + 
                                 " it currently points to " + old_link)
        with open(new_path, 'w') as f:
            f.write(old_path)
        if verbose:
            print old_path, "recorded at",new_path
        return True
      
      
"""
Walker method
Inputs are:
source Parent directory to be walked through
use_directory method to check subdirectoies should be used
    approve_all (default) cause all children(recurisive) to be walked
    approve_none ignores all child directories
use_file method check that all files will be passed to file_action
    approve_all (default) cause all files to be used
file_action method processes each file
    print_size (default) just prints the path and size
onerror is a function is underlying os.listdir fails
followlinks would allow following symbolic links
    WARNING Be aware that setting followlinks to True can lead to infinite recursion if a link points to a parent directory of itself. 
    walk() does not keep track of the directories it visited already.
"""
def do_walk(source=os.getcwd(), directory_action=approve_all, file_action=print_size, onerror=None, followlinks=False, verbose=True):
    source = expanderuser(source)
    #Must be topdown=True otherwise walk will process subdirectories before checking them
    for root, dirs, files in os.walk(source, topdown=True, onerror=onerror, followlinks=followlinks):
        print root, len(dirs), len(files)
        dirs_clone = dirs[:]
        for sub in dirs_clone:
            if not directory_action(root, sub, verbose=verbose):
                if verbose:
                    print "skipping directory", os.path.join(root, sub)
                dirs.remove(sub)
        # do something cool with each file    
        for name in files:
            file_action(root, name, verbose=verbose)


def demo():
    source = "/mnt/fls01-bcf01/ngsdata/Analysis/2015/hiseq/150821_SN700511R_0296_AC7M2RACXX_analysis/Tovah_Shaw/fastqs/"
    target = "/mnt/mr01-home01/mbaxecb2/scratch/workflow"
    directory_checker = RegexChecker(["^M"])
    #ls -alcopier = Copier({".py$":"code.py"},"~/temp")
    copier = Linker({"R1_001.fast":"left.link", "R2_001.fast":"right.link"},target)
    do_walk(source=source, directory_action=approve_all, file_action=copier.file_action, verbose=True)
    
    lister = DirectoryLister(list_file="thelist.txt",required_files=["left.link","right.link"]) #, check_path="~/temp", list_path="/Junk")
    do_walk(source="~/temp/william_data", directory_action=lister.list_directory, file_action=approve_none, verbose=True)


def count_lines(file_name):
    lines = 0
    with open(file_name) as the_file:
        for line in the_file:
            lines += 1
    return lines      
      
        
def write_loop_block(new_file, directory_list):
    count = count_lines(directory_list)
    new_file.write("#$ -t 1-")
    new_file.write(str(count))
    new_file.write("\n")
    new_file.write("DIRECTORY=`sed -n \"${SGE_TASK_ID}p\" ")
    new_file.write(directory_list)
    new_file.write("`\n")
    new_file.write("\n")

        
def update_script(script, new_script, directory_list):
    directory_line_found = False
    with open(script) as old_file:
        with open(new_script,'w') as new_file:
            for line in old_file:
                if line.startswith("DIRECTORY="):
                    if directory_line_found:
                        raise Exception("qsub_file: " + script + " has two lines that start with DIRECTORY=")
                    else:
                        write_loop_block(new_file, directory_list)
                        directory_line_found = True
                else:    
                    new_file.write(line)
    if not directory_line_found:
        raise Exception("qsub_file: " + script + " has no line that start with DIRECTORY=")


if __name__ == '__main__':
    usage = "usage: %prog [options] arg1 arg2"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-p", "--parent", dest="parent", action="store", type="string", 
                  help="parent directory of the sub directories to hold the runs")
    parser.add_option("-d", "--directory_list", dest="directory_list", action="store", type="string",
                  help="file to hold the list of directories")
    parser.add_option("-q", "--qsub_script", dest="qsub_script", action="store", type="string",
                  help="qsub script to be switched to batch.  "
                       "This script should have a line which starts with DIRECTORY= " 
                       "This line will be replaced with a loop for each directory in directory_list")                  
    parser.add_option("-b", "--batch_script", dest="batch_script", action="store", type="string",
                  help="Locatin to write batch qsub script to. "
                       "Default is Tbatch_script + \"_batch\" ")                  
    parser.add_option("-f", "--file_pattern", dest="file_list", action="append", type="string",
                  help="Regex to find file and name to give the new file. "
                       "Format is regex:name if source specified. "
                       "Format is name if source not specified (regex: is ignored)"
                       "Multiple values allowed.")               
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                  help="If set will generate output of what the tool is doing.")               
    group = optparse.OptionGroup(parser, "Find files group",
                    "If source is not specified the other optios are ignored.  "
                    "Requires parent value to be set too!")
    group.add_option("-s", "--source", dest="source", action="store", type="string", 
                  help="source directory that holds the raw data files. "
                       "If omitted the assumtion is the parent directory already has the required subdirectories")
    group.add_option("-c", "--copy", action="store_true", dest="copy", default=False,
                  help="If set will copy the original file to the new location. Other just the path to the original file is saved.")               
    parser.add_option_group(group)              
    (options, args) = parser.parse_args()
    if options.file_list == None:
        options.file_list = ["R1_001.fast:left.link","R2_001.fast:right.link"]

    endings_mappings = None
    required_files = None
    if options.source:
        print "source"
        endings_mappings = {}
        for file_option in options.file_list:
            parts = file_option.split(":")
            if len(parts) != 2:
                raise Exception("file_pattern " + file_option + " not in the expected regex:name format")
            endings_mappings[parts[0]] = parts[1]                        
        required_files = endings_mappings.values()
    elif options.parent:
        print "parent"
        required_files = []
        for file_option in options.file_list:
            print file_option
            parts = file_option.split(":")
            if len(parts) == 1:
                required_files.append(parts[0])
            elif len(parts) == 2:
                required_files.append(parts[1])   
            else:     
                raise Exception("file_pattern " + file_option + " has more than one : in it.")
        print required_files    
                     
    if options.source:
        if not options.parent:
            raise Exception("source parameter provided but parent parameter missing")            
        if options.copy:    
            copier = Copier(endings_mappings,options.parent)
            if options.verbose:
                print "Coping files from", options.source, "to", options.parent
        else:
            copier = Linker(endings_mappings, options.parent)
            if options.verbose:
                print "linking files from", options.source, "in", options.parent
        if options.verbose:
            print "Using the file mappings:"
            print endings_mappings
        do_walk(source=options.source, directory_action=approve_all, file_action=copier.file_action, verbose=True)
    else:
        if options.verbose:
            print "Skipping copy/link step as no source parameter provided", endings_mappings
    if options.verbose:
        print
        
   
    if options.parent:
        if options.directory_list:
            if options.verbose:
                print "Writing list of directories in", options.parent, "to", options.directory_list
                print "Only directories that have all these files are included:"
                print required_files
            lister = DirectoryLister(list_file=options.directory_list,required_files=required_files) #, check_path="~/temp", list_path="/Junk")
            do_walk(source=options.parent, directory_action=lister.list_directory, file_action=approve_none, verbose=True)
        else:
            if options.verbose:
                print "Skipping directory list as no directory_list parameter provided"
    else:
        if options.verbose:
            print "Skipping directory list step as no parent parameter provided"
    if options.verbose:
        print  
            

    if options.directory_list:          
        if options.qsub_script:
            if options.batch_script:
                batch = options.batch_script
            else:
                batch = options.qsub_script + "_batch"
            update_script(options.qsub_script, batch, options.directory_list)    
            if options.verbose:
                print "Wrote new batch script to", batch
                print "Based on squb_script", options.qsub_script
                print "Using directoory_list", options.directory_list
        else:
            if options.verbose:
                print "Skipping batch script creation as no qsub_script parameter provided"
    else:
        if options.verbose:
            print "Skipping batch script creation as no directory_list parameter provided"
            
        

