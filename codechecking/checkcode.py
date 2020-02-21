#!/usr/bin/python

from __future__ import unicode_literals
import lib.parsing

# Check for poorly named variables.
# Check for senders of self and nil.
# Check for recursion.

class CodeCheckingHandler(lib.parsing.BasicHandler):
    def methodWarning(self, *arguments):
        message = " ".join(map(lambda each: str(each), arguments))
        print message, "in", self.getCurrentMethodSignature() + '.'
        
    def addTemporary(self, name):
        if self.isPoorlyNamedVariable(name):
            self.methodWarning("Poorly named variable", repr(str(name)))
    
    def isPoorlyNamedVariable(self, name):
        poorPrefixes = ["a", "an", "some", "temp" ]
        for prefix in poorPrefixes:
            if name.startswith(prefix):
                suffix = name[len(prefix):]
                if suffix[:1].isupper():
                    return True
        return False
        
    def addUnaryMessageSend(self, selector):
        blocked = ["self", "nil", "super", "true", "false"]
        if selector in blocked:
            self.methodWarning("Sender of", repr(str(selector)))
            
    def addMethodBody(self, node):
        node = node.getFirstStatement()
        if node is None:
            return
        if not(node.receiver.isVariableNode() and node.receiver.name == "self"):
            return
        if node.selector != self.currentMethodSelector:
            return
        self.methodWarning("Recursion")

    def addBlockParameter(self, name):
        if name == "e":
            self.methodWarning("Poorly named block parameter", repr(str(name)))
        
if __name__ == "__main__":  
    parser = lib.parsing.Parser()
    parser.handler = CodeCheckingHandler()
    parser.processCommandLine()
    
           
        



