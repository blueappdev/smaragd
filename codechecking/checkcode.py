#!/usr/bin/python

from __future__ import unicode_literals
import string
import lib.parsing

class CodeCheckingHandler(lib.parsing.BasicHandler):
    def methodWarning(self, *arguments):
        message = string.join(map(lambda each: str(each), arguments), " ")
        print self.getCurrentMethodSignature(), message + '.'
        
    def addTemporary(self, name):
        if self.isPoorlyNamedVariable(name):
            self.methodWarning("has poorly named variable", name)
    
    def isPoorlyNamedVariable(self, str):
        if str == "e":
            return True
        for prefix in ["a", "an", "some", "temp" ]:
            if str.startswith(prefix):
                suffix = str[len(prefix):]
                #print str, prefix, suffix, suffix[:1]
                if suffix[:1].isupper():
                    return True
        return False
        
        
if __name__ == "__main__":  
    parser = lib.parsing.Parser()
    parser.handler = CodeCheckingHandler()
    parser.processCommandLine()
    
           
        



