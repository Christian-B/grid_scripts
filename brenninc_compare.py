import brenninc_peeker


class Comparer():

    def __init__(self, iterator1, iterator2, iterator3):
        self.peeker1 = brenninc_peeker.Peeker(iterator1)
        self.peeker2 = brenninc_peeker.Peeker(iterator2)
        self.peeker3 = brenninc_peeker.Peeker(iterator3)
        self.update_factor = 10
        self.value1_count = 0

    @staticmethod
    def nextOrEOF(peeker):
        raise NotImplementedError

    @staticmethod
    def notEOF(value):
        raise NotImplementedError

    @staticmethod
    def match(valueA, valueB):
        raise NotImplementedError

    def tripleMatch(self, value1, value2, value3):
        raise NotImplementedError

    def matchWithTwo(self, value1, value2):
        raise NotImplementedError

    def matchWithThree(self, value1, value3):
        raise NotImplementedError

    def unmatchedOne(self, value1):
        raise NotImplementedError

    def unmatchedTwo(self, value2):
        raise NotImplementedError

    def unmatchedThree(self, value3):
        raise NotImplementedError

    def finalize(self):
        raise NotImplementedError

    def update(self):
        pass

    def getValue1(self):
        self.value1_count += 1
        if self.value1_count % self.update_factor == 0:
            self.update()
        return self.peeker1.next()

    def do_compare(self):
        value1 = self.peeker1.next()
        value2 = self.nextOrEOF(self.peeker2)
        value3 = self.nextOrEOF(self.peeker3)

        while True:
            #print value1, value2, value3
            if self.match(value1, value2):
                if self.match(value2, value3):
                    self.tripleMatch(value1, value2, value3)
                    value3 = self.nextOrEOF(self.peeker3)
                else:
                    self.matchWithTwo(value1, value2)
                value2 = self.nextOrEOF(self.peeker2)
                try:
                    value1 = self.getValue1()
                except StopIteration:
                    break
            elif self.match(value1, value3):
                #As failed 1 = 2 test not a triple match
                self.matchWithThree(value1, value3)
                try:
                    value1 = self.getValue1()
                except StopIteration:
                    break
                value3 = self.nextOrEOF(self.peeker3)
            else:
                list2 = self.peeker2.look_ahead_array(10)
                list3 = self.peeker3.look_ahead_array(10)
                if value1 not in list2 and value1 not in list3:
                    self.unmatchedOne(value1)
                    try:
                        value1 = self.getValue1()
                    except StopIteration:
                        break
                else:
                    found = False
                    list1 = self.peeker1.look_ahead_array(10)
                    if self.notEOF(value2) and value2 not in list1:
                        self.unmatchedTwo(value2)
                        value2 = self.nextOrEOF(self.peeker2)
                        found = True
                    if self.notEOF(value3) and value3 not in list1:
                        self.unmatchedThree(value3)
                        value3 = self.nextOrEOF(self.peeker3)
                        found = True
                    if not found:
                        raise Exception("Matching Error",
                                        value1, value2, value3)

        while self.notEOF(value2):
            self.unmatchedTwo(value2)
            value2 = self.nextOrEOF(self.peeker2)
        while self.notEOF(value3):
            self.unmatchedThree(value3)
            value3 = self.nextOrEOF(self.peeker3)
        self.finalize()
