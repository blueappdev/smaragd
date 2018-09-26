#!/usr/bin/env python

# tonel.py

import sys
import string
import StringIO

class TonelParser:
    def decodeStream(self, aStream)
        self.stream = aStream
        self.nextCharacter()
        return self.process()

    def process(self):
        self.skipSeparators()

    def nextCharacter(self):
        self.currentCharacter = self.stream.read(1)
        self.classifyCharacter()

    def classifyCharacter(self):



    def skipSeparators(self):
        while self.currentCharacter.isspace():
            self.nextCharacter()


def load(aStream):
    return TonelParser().decodeStream(aStream)


def loadf(aFilename):
    print aFilename
    stream = open(aFilename)
    result = load(stream)
    stream.close()
    return result

if __name__ == "__main__":
    print "tonel"
    for each in sys.argv[1:]:
        loadf(each)

