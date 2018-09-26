#!/usr/bin/env python

# Kernel.py

import sys
import string
import StringIO
import codecs
import os
import Configuration

class Object:
    def error(self, *args):
        print "error:", string.join(map(lambda each: repr(each), args), " ")
        sys.exit(1)

    def warn(self, *args):
        print "warn:", string.join(args, " ")

    def info(self, *args):
        if Configuration.sessionConfiguration.verboseFlag:
            print "info:", string.join(args, " ")

    def halt(self, *args):
        print "halt:", string.join(map(lambda each: repr(each), args), " ")
        sys.exit(1)

    def notYetImplemented(self):
        self.error("not yet implemented")

    def subclassResponsibility(self):
        self.error("subclassResponsibility");

    def trace(self, *args):
        if True:
            print "trace:", string.join(args, " ")

    def indentedPrint(self, indent, *args):
        for i in xrange(indent):
            print " ",
        print string.join(map(lambda each: str(each), args), " ")

    def printOn(self, aStream):
        aStream.write(self.__class__.__name__ +' instance')

    def printString(self):
        stream = StringIO.StringIO()
        self.printOn(stream)
        return stream.getvalue()

    def __repr__(self):
        return self.printString()

class Magnitude:
    def __init__(self, aValue):
        self.__value = aValue

    def __eq__(self, anObject):
        return self.__class__ == anObject.__class__ and self.__value == anObject.__value

    def getInternalValue(self):
        return self.__value

class Character(Magnitude):
    pass

class String(Magnitude):
    def printOn(self, aStream):
        return repr(self.__value)

class Symbol(Magnitude):
    pass

class Number(Magnitude):
    pass

class Collection(Object):
    pass

class SequenceableCollection(Collection):
    pass

class Array(SequenceableCollection):
    def __init__(self):
        self.elements = []

    def __repr__(self):
        return


