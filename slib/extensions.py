import string

class StringWrapper:
    def __init__(self, aString):
        self.value = aString

    def cutPrefix(self, aString):
        if self.value.startswith(aString):
            return self.value[len(aString):]
        else:
            return self.value
