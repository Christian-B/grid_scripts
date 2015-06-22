import brenninc_utils
import os
import unittest


class create_new_file_tester(unittest.TestCase):

    def test(self):
        create = brenninc_utils.create_new_file
        self.assertEqual(create("test", "_more"), "test_more")
        self.assertEqual(create("test.txt", "_more"), "test_more.txt")
        self.assertEqual(create("test.txt.gz", "_more"), "test_more.txt.gz")
        self.assertEqual(create("test.txt.gz", "_more", gzipped=True),
                         "test_more.txt.gz")
        self.assertEqual(create("test.txt.gz", "_more", outputdir="", gzipped=True),
                         "test_more.txt.gz")
        self.assertEqual(create("test.txt.gz", "_more", extension="csv", gzipped=True),
                         "test_more.csv.gz")
        self.assertEqual(create("test.txt.gz", "_more", gzipped=False),
                         "test_more.txt")
        self.assertEqual(create("/temp/demo/test", "_more"),
                         "/temp/demo/test_more")
        self.assertEqual(create("/temp/demo/test.txt", "_more"),
                         "/temp/demo/test_more.txt")
        self.assertEqual(create("/temp/demo/test.txt", "_more", extension="csv"),
                         "/temp/demo/test_more.csv")
        self.assertEqual(create("/temp/demo/test.txt", "_more", extension=".csv"),
                         "/temp/demo/test_more.csv")
        self.assertEqual(create("/temp/demo/test.txt.gz", "_more"),
                         "/temp/demo/test_more.txt.gz")
        self.assertEqual(create("test", "_more", "../newfolder/"),
                         "../newfolder/test_more")
        self.assertEqual(create("test.txt", "_more", "../newfolder/"),
                         "../newfolder/test_more.txt")
        self.assertEqual(create("test", "_more", "../newfolder"),
                         "../newfolder/test_more")
        self.assertEqual(create("test.txt", "_more", "../newfolder"),
                         "../newfolder/test_more.txt")
        self.assertEqual(create("test.txt", "_more", "../newfolder",
                                gzipped=True),
                         "../newfolder/test_more.txt.gz")
        self.assertEqual(create("test.txt", "_more", "../newfolder",
                                gzipped=False),
                         "../newfolder/test_more.txt")
        self.assertEqual(create("test.txt.gz", "_more", "../newfolder"),
                         "../newfolder/test_more.txt.gz")
        self.assertEqual(create("~/temp/demo/test", "_more", "../newfolder"),
                         "../newfolder/test_more")
        self.assertEqual(create("~/temp/demo/test.txt", "_more",
                                "../newfolder"),
                         "../newfolder/test_more.txt")
        self.assertEqual(create("~/temp/demo/test.txt.gz", "_more",
                                "../newfolder"),
                         "../newfolder/test_more.txt.gz")

def check_files_for_ending(file_list, ending):
    for a_file in file_list:
        if a_file.endswith(ending):
            return True
    return False         

class find_files_tester(unittest.TestCase):

 
    def test_all(self):
        fileList = brenninc_utils.find_files(os.getcwd())
        found = check_files_for_ending(sorted(fileList), "brenninc_utils_test.py")
        self.assertTrue(found)
        
    def test_txt(self):
        fileList = brenninc_utils.find_files(os.getcwd(), extensions="txt")
        found = check_files_for_ending(fileList, "brenninc_utils_test.py")
        self.assertFalse(found)

    def test_txt_py(self):
        fileList = brenninc_utils.find_files(os.getcwd(), extensions=["txt", ".py"])
        found = check_files_for_ending(fileList, "brenninc_utils_test.py")
        self.assertTrue(found)

    def test_parent(self):
        parent = os.path.dirname(os.getcwd())
        fileList = brenninc_utils.find_files(parent)
        found = check_files_for_ending(fileList, "brenninc_utils_test.py")
        self.assertFalse(found)

    def test_parent_recursive(self):
        parent = os.path.dirname(os.getcwd())
        fileList = brenninc_utils.find_files(parent, recursive=True)
        found = check_files_for_ending(fileList, "brenninc_utils_test.py")
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
