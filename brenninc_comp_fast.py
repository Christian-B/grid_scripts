import brenninc_comp_counter


class EOF():
    def __init__(self):
        self.name = "EOF"


class Comparer(brenninc_comp_counter.Comparer):

    def __init__(self, iterator1, iterator2, iterator3):
        brenninc_comp_counter.Comparer.__init__(self, iterator1, iterator2,
                                                iterator3)
        self.update_factor = 100000

    @staticmethod
    def nextOrEOF(peeker):
        try:
            return peeker.next()
        except StopIteration:
            return EOF()

    @staticmethod
    def notEOF(value):
        return value.name != "EOF"

    @staticmethod
    def match(valueA, valueB):
        return valueA.name == valueB.name

    """
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

    def finalize(self):
        print "Only 1:", self.only1
        print "Only 2:", self.only2
        print "Only 3:", self.only3
        print "In 1+2:", self.in1and2
        print "In 1+3:", self.in1and3
        print "all 3:", self.all3
    """
