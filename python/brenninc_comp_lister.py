import brenninc_compare


class Comparer(brenninc_compare.Comparer):

    def __init__(self, iterator1, iterator2, iterator3):
        brenninc_compare.Comparer.__init__(self,
                                           iterator1, iterator2, iterator3)
        self.only1 = []
        self.only2 = []
        self.only3 = []
        self.in1and2 = []
        self.in1and3 = []
        self.all3 = []

    @staticmethod
    def nextOrEOF(peeker):
        try:
            return peeker.next()
        except StopIteration:
            return "EOF"

    @staticmethod
    def notEOF(value):
        return value != "EOF"

    @staticmethod
    def match(valueA, valueB):
        return valueA == valueB

    def tripleMatch(self, value1, value2, value3):
        self.all3.append(value3)

    def matchWithTwo(self, value1, value2):
        self.in1and2.append(value1)

    def matchWithThree(self, value1, value3):
        self.in1and3.append(value1)

    def unmatchedOne(self, value1):
        self.only1.append(value1)

    def unmatchedTwo(self, value2):
        self.only2.append(value2)

    def unmatchedThree(self, value3):
        self.only3.append(value3)

    def finalize(self):
        print "1:", self.only1
        print "2:", self.only2
        print "3:", self.only3
        print "1-2:", self.in1and2
        print "1-3:", self.in1and3
        print "all3:", self.all3
