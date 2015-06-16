import brenninc_utils
import unittest


class create_new_file_tester(unittest.TestCase):

    def test(self):
        create = brenninc_utils.create_new_file
        self.assertEqual(create("test", "_more"), "test_more")
        self.assertEqual(create("test.txt", "_more"), "test_more.txt")
        self.assertEqual(create("test.txt.gz", "_more"), "test_more.txt.gz")
        self.assertEqual(create("test.txt.gz", "_more", gzipped=True),
                         "test_more.txt.gz")
        self.assertEqual(create("test.txt.gz", "_more", gzipped=False),
                         "test_more.txt")
        self.assertEqual(create("/temp/demo/test", "_more"),
                         "/temp/demo/test_more")
        self.assertEqual(create("/temp/demo/test.txt", "_more"),
                         "/temp/demo/test_more.txt")
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

if __name__ == '__main__':
    unittest.main()
