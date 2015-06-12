import brenninc_compare


class Comparer(brenninc_compare.Comparer):

    def __init__(self, iterator1, iterator2, iterator3):
        brenninc_compare.Comparer.__init__(self, iterator1,
                                           iterator2, iterator3)
        self.only1 = 0
        self.only2 = 0
        self.only3 = 0
        self.in1and2 = 0
        self.in1and3 = 0
        self.all3 = 0

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
        self.all3 += 1

    def matchWithTwo(self, value1, value2):
        self.in1and2 += 1

    def matchWithThree(self, value1, value3):
        self.in1and3 += 1

    def unmatchedOne(self, value1):
        self.only1 += 1

    def unmatchedTwo(self, value2):
        self.only2 += 1

    def unmatchedThree(self, value3):
        self.only3 += 1

    def update(self):
        print self.value1_count,
        print self.only1,
        print "%.2f" % (self.only1*100.0/self.value1_count),
        print self.in1and2,
        print "%.2f" % (self.in1and2*100.0/self.value1_count),
        print self.in1and3,
        print "%.2f" % (self.in1and3*100.0/self.value1_count),
        print self.all3, self.only2, self.only3

    def finalize(self):
        print "Only 1:", self.only1
        print "Only 2:", self.only2
        print "Only 3:", self.only3
        print "In 1+2:", self.in1and2
        print "In 1+3:", self.in1and3
        print "all 3:", self.all3
