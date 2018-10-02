#!/usr/bin/env python

# svalidate.py

import getopt, sys
import os, os.path, glob
import json
import StringIO, io
import codecs

from slib.Kernel import *
import scmd

class Validator:
    def process(self, aFilename):
        if os.path.isdir(aFilename):
            self.processDirectory(aFilename)
        elif os.path.exists(aFilename):
            self.processFile(aFilename)
        else:
            self.error(aFilename, "file not found")
            sys.exit(1)

    def processDirectory(self, aFilename):
        for each in os.listdir(aFilename):
            self.process(os.path.join(aFilename, each))

    def processFile(self, aFilename):
        if not self.isTonelFile(aFilename):
            return
        print "Process", aFilename
        loader = scmd.TonelPackageLoader()
        self.currentPackage = scmd.GSPackage()
        loader.targetPackage = self.currentPackage
        loader.processClassFile(aFilename)
        self.validatePackage()

    def isTonelFile(self, aFilename):
        directory, base = os.path.split(aFilename)
        parts = base.split(".")
        return (len(parts) >= 3
            and parts[-1] == "st"
            and parts[-2] in ["class", "extension"])

    def validatePackage(self):
        print self.currentPackage
        for key, value in self.currentPackage.methodsDictionary.items():
            self.validateMethod(value)

    def validateMethod(self, aMethod):
        pass

if __name__ == "__main__":
    options, arguments = getopt.getopt(sys.argv[1:], "")
    for option, value in options:
        if option == "-h":
            #help()
            sys.exit(1)
        else:
            print "Option", option, "not supported"
    if len(arguments) == 0:
        print "Missing parameters"
    for each in arguments:
        Validator().process(each)
