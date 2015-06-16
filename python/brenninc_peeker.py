class Peeker():

    def __init__(self, iterator):
        self.ahead = False
        self.peeked = []
        self.iterator = iterator

    def next(self):
        if self.ahead:
            result = self.peeked[0]
            if len(self.peeked) == 1:
                self.peeked = []
                self.ahead = False
            else:
                self.peeked = self.peeked[1:]
            return result
        else:
            return self.iterator.next()

    def look_ahead_array(self, count):
        for i in range(len(self.peeked), count):
            try:
                self.peeked.append(self.iterator.next())
            except StopIteration:
                break
        if len(self.peeked) > 0:
            self.ahead = True
        return self.peeked[:count]

    def skip(self, count):
        self.peeked = self.peeked[count:]
        if len(self.peeked) == 0:
            self.ahead = False

    def push_back(self, previous):
        self.ahead = True
        self.peeked = [previous] + self.peeked

    def look_ahead(self):
        result = self.iterator.next()
        self.peeked.append(result)
        self.ahead = True
        return result
