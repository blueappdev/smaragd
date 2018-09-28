#!/usr/bin/env python

# scleanup.py

from scmd import *

class Cleaner(Object):
    def __init__(self, aFilename):
        self.filename = aFilename

    def loadImage(self):
        root, extension = os.path.splitext(self.filename)
        if extension != ".cached":
            self.error("Filetype should be '.cached'", self.filename)
        stream = open(self.filename, "rb")
        self.image = pickle.load(stream)
        stream.close()
        self.image.filename = root

    def saveImage(self):
        self.image.cache()

    def processImage(self):
        self.printStatistics("Before cleanup")
        # The self-modifying loop cannot use the iterator itervalues().
        for each in self.image.classes.values():
            self.processClass(each)
        self.printStatistics("After cleanup")
        self.printNamespaces()

    def processClass(self, aClass):
        if self.shouldDeleteClass(aClass):
            aClass.remove()

    def shouldDeleteClass(self, aClass):
        namespacesToCleanup = [
                "UI", "UISkinsOSX", "Refactory.Browser", "Store",
                "Tools.Trippy", "Tools.FileTools", "Graphics",
                "Root.GemStone.Globals", "Root.GemStone.Tests"]
        return aClass.getNamespace() in namespacesToCleanup

    def printStatistics(self, aString):
        print aString
        print "    Classes", len(self.image.classes)

    def printNamespaces(self):
        print "Namespaces"
        namespaces = map(lambda each: each.getNamespace(), self.image.classes.itervalues())
        for each in set(namespaces):
            print "    ", each

if __name__ == "__main__":
    options, arguments = getopt.getopt(sys.argv[1:], "s")
    saveFlag = False
    for option, value in options:
        if option == "-s":
            saveFlag = True
        else:
            print "Option", option, "not supported"

    if len(arguments) == 0:
        print "Missing parameters"

    for each in arguments:
        cleaner = Cleaner(each)
        cleaner.loadImage()
        cleaner.processImage()
        if saveFlag:
            cleaner.saveImage()
        else:
            print "File not saved (use -s to save it)"
