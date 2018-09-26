#!/usr/bin/env python

# Configuration.py

import sys
import string
import StringIO
import codecs
import os
import json

class TransientConfiguration:
    def __init__(self):
        self.verboseFlag = False
        
class PersistentConfiguration:
    def __init__(self):
        self.setDefaults()
        self.setConfigurationFile()
        self.load()
        
    def setDefaults(self):
        self.fontName = "Tahoma"
        self.fontSize = "7"
        
    def getFont(self):
        return (self.fontName, int(self.fontSize))
        
    def setConfigurationFile(self):
        if os.name == "nt":
            directory = os.environ["APPDATA"]
            if os.path.exists(directory):
                directory = os.path.join(directory, "Smaragd")
                if not os.path.exists(directory):
                    os.makedirs(directory)
            basename = os.path.basename(sys.argv[0])
            root, extension = os.path.splitext(basename)
            configurationFilename = root + ".inf"
            self.filename = os.path.join(directory, configurationFilename)
        else:
            directory = os.environ.get("HOME","").strip()
            if directory == "":
                self.error("Environment variable HOME must be defined.")
            basename = os.path.basename(sys.argv[0])
            root, extension = os.path.splitext(basename)
            configurationFilename = "." + root
            self.filename = os.path.join(directory, configurationFilename)

    def load(self):
        if not os.path.exists(self.filename):
            return
        stream = codecs.open(self.filename, "r", encoding="UTF-8")
        while True:
            line = stream.readline()
            line = line.strip()
            if line == "":
                break
            if line == "" or line[0] == "#":
                continue
            key, value = line.split("=")
            key = key.strip()
            value = value.strip()
            self.__dict__[key] = value
        stream.close()
           
sessionConfiguration = TransientConfiguration()
globalConfiguration = PersistentConfiguration()


