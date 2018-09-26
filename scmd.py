#!/usr/bin/env python

# smaragd.py

import getopt, sys
import os, os.path, glob
import json
import StringIO, io
import codecs
import cPickle as pickle

from slib.Kernel import *

class Fragment(Object):
    # Another subclass of Fragment could reference externally stored source code.

    def __init__(self, aString, lineNumber=0):
        self.source = aString
        self.lineNumber = lineNumber

    def getSource(self):
        return self.source

class Package(Object):
    def __init__(self, name = ""):
        self.name = name

    def printOn(self, aStream):
        aStream.write(self.__class__.__name__)
        aStream.write("(" + self.name + ")")

    def printStructure(self):
        for each in self.methods:
            each.printStructure()

class PackageLoader(Object):
    def __init__(self, targetImage, aFilename = None):
        self.targetImage = targetImage
        self.targetPackage = self.targetImage.findOrCreatePackageNamed("")
        self.filename = aFilename
        self.targetClass = None
        self.currentMethodCategoryName = "uncategorized"

    def load(self):
        self.processFile(self.filename)

    def newCompiler(self):
        return self.compilerClass()()

    def compilerClass(self):
        return Compiler

    def addMethod(self, className, methodSource, lineNumberOffset = 0):
        #print "Add a method to", className, 'in category', self.currentMethodCategory
        compiler = self.newCompiler()
        newMethod = compiler.makeCompiledMethodForSource(methodSource)
        newMethod.methodClass = self.targetImage.findOrCreateClassNamed(className)
        newMethod.category = self.currentMethodCategoryName
        self.targetImage.addCompiledMethod(newMethod)

    def addInstanceMethod(self, className, methodSource):
        #print "Add instance method to", className, 'in category', self.currentMethodCategoryName
        self.addMethod(className, methodSource)

    def addClassMethod(self, className, methodSource):
        #print "Add class method to", className, 'in category', self.currentMethodCategoryName
        self.addMethod(className + " " + "class", methodSource)

    def setTargetClassName(self, aString):
        self.targetClassName = aString

    def setCurrentMethodCategory(self, aString):
        self.currentMethodCategoryName = aString
        #print "CURRENT CATEGORY:", self.currentMethodCategoryName


class TopazCommand(Object):
    def __init__(self, aString, lineNumber):
        self.lineNumber = lineNumber
        self.commandLine = aString
        self.commandText = 'none'
        self.initializeCommandType()

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.commandType + ")"

    def initializeCommandType(self):
        #print "<<<",self.commandLine, ">>>"
        self.commandType = self.commandLine.split()[0]
        if self.commandType not in self.supportedCommandTypes():
            print "Unknown command", self.commandType, "in line", self.lineNumber
            sys.exit(1)

    def requiresCommandText(self):
        return self.commandType in ["doit", "classmethod:", "method:"]

    def supportedCommandTypes(self):
        return ["set", "doit", "category:", "classmethod:", "method:"]

    def process(self, aGSPackageLoader):
        #print "Process", self
        scanner = GSScanner(Fragment(self.commandLine))
        token = scanner.getToken()
        if token.type == "keyword":
            selector = token.value
            arguments = []
            token = scanner.getToken()
            if token.type in ['string', 'identifier']:
                arguments.append(token.value)
            else:
                print token.type, token.value
                self.error("unsupported argument type")
            token = scanner.getToken()
            if token.type != "end":
                self.error("only one argument supported", selector, token)
            if selector == "category:":
                aGSPackageLoader.setCurrentMethodCategory(arguments[0])
                return
            if selector == "method:":
                aGSPackageLoader.addInstanceMethod(arguments[0], Fragment(self.commandText, self.lineNumber))
                return
            if selector == "classmethod:":
                aGSPackageLoader.addClassMethod(arguments[0], Fragment(self.commandText, self.lineNumber))
                return
                return
        elif token.type == "identifier":
            identifier = token.value
            if identifier == "doit":
                aGSPackageLoader.doIt(Fragment(self.commandText, self.lineNumber))
                return
            if identifier == "set":
                token = scanner.getToken()
                assert token.type == "keyword"
                key = token.value
                token = scanner.getToken()
                assert token.type == "number"
                value = token.value
                aGSPackageLoader.set(key,value)
                return
        print token.type, token.value
        self.error("command not yet implemented ("+self.commandLine+")")

class GSPackageLoader(PackageLoader):
    def compilerClass(self):
        return GSCompiler

    def processFile(self, aFilename):
        self.stream = codecs.open(aFilename, encoding='UTF-8')
        self.lineNumber = 0
        self.currentCommand = self.readCommand()
        while self.currentCommand is not None:
            self.currentCommand.process(self);
            self.currentCommand = self.readCommand();
        self.stream.close()
        return self.targetPackage

    # readBasicLine() needs to preserve the line end characters (LF or CR).
    # maybe need to switch to binary mode
    def readBasicLine(self):
        self.lineNumber = self.lineNumber + 1
        self.currentLine = self.stream.readline()
        #print "Basic ["+self.currentLine+']'

    def readContentLine(self):
        self.readBasicLine()
        while self.currentLine != "":
            self.currentLine = self.currentLine.strip()
            if self.currentLine == "" or self.currentLine.startswith("!"):
                self.readBasicLine()
            else:
                return
        self.currentLine = None
        return

    def readCommand(self):
        self.readContentLine();
        if self.currentLine is None:
            return None
        newCommand = TopazCommand(self.currentLine, self.lineNumber)
        if newCommand.requiresCommandText():
            newText = StringIO.StringIO()
            self.readBasicLine()
            while self.currentLine != "" and self.currentLine.rstrip() != "%":
                newText.write(self.currentLine)
                self.readBasicLine()
            newCommand.commandText = newText.getvalue().strip()
        return newCommand

    def doIt(self, aFragment):
        compiler = self.newCompiler()
        compiler.process(aFragment)

    def set(self, key, value):
        assert key == "compile_env:"
        assert value == "0", 'unexpected compile_env'


class VWPackageLoader(PackageLoader):
    def compilerClass(self):
        return VWCompiler

    def processFile(self, aFilename):
        self.stream = codecs.open(aFilename, encoding='UTF-8')
        self.mode = "code"
        self.stepCharacter()
        self.beginChunk()
        while self.currentCharacter != "":
            if self.currentCharacter == "!":
                self.stepCharacter()
                if self.currentCharacter != "!":
                    self.endChunk()
                    self.processChunk()
                    self.beginChunk()
            self.chunkStream.write(self.currentCharacter)
            self.stepCharacter()
        self.endChunk()
        self.processTrailingChunk()
        self.stream.close()
        return self.targetPackage

    def stepCharacter(self):
        self.currentCharacter = self.stream.read(1)

    def beginChunk(self):
        self.chunkStream = StringIO.StringIO()

    def endChunk(self):
        self.chunk = self.chunkStream.getvalue()
        self.chunkStream.close()

    def processChunk(self):
        strippedChunk = self.chunk.strip()
        if self.mode == "code":
            if strippedChunk == "":
                self.mode = "category"
                return
            # print strippedChunk
            compiler = self.newCompiler()
            node = compiler.process(Fragment(self.chunk))
            #print node.evaluate(self)
            return
        if self.mode == "category":
            if strippedChunk == "":
                self.error("unexpected empty chunk in category")
                return
            #self.printChunk()
            components = VWScanner(Fragment(self.chunk)).allTokens()
            action = components[-2].value
            assert action in ['methodsFor:', 'methodsForUndefined:']
            if components[1].matches('identifier', 'class'):
                assert len(components) == 4
                self.setTargetClassName(components[0].value + ' ' + components[1].value)
            else:
                #print components
                assert len(components) == 3
                self.setTargetClassName(components[0].value)
            self.setCurrentMethodCategory(components[-1].value)
            self.mode = "method"
            return
        if self.mode == "method":
            #self.printChunk()
            if strippedChunk == "":
                self.mode = "code"
                return
            self.addInstanceMethod(self.targetClassName, Fragment(self.chunk.strip()))
            return
        self.error("unexpected mode ", self.mode)

    def processTrailingChunk(self):
        if self.chunk.strip() == "":
            return
        self.error("unexpected characters after final exclamation mark")

    # An empty chunk introduces a methods category chunk and a method definition chunk.
    def printChunk(self):
        #if chunk.strip()
        print "chunk <" + self.chunk.strip() + ">"
        #print "====================="

class Token(Object):
    def __init__(self, type, value, lineNumber = None):
        self.type = type
        self.value = value
        self.lineNumber = lineNumber

    def printOn(self, aStream):
        aStream.write(self.__class__.__name__ + "(" + self.type)
        if self.type != self.value and self.value != "":
            aStream.write("," + self.value)
        aStream.write(")")

    def matches(self, aType, aValue=None):
        return ((aType is None or self.type == aType)
            and (aValue is None or self.value == aValue))

    def asSource(self):
        if self.type == "character":
            return "$" + self.value
        elif self.type == "symbol":
            stream = StringIO.StringIO()
            stream.write("'")
            for ch in self.value:
                if ch == "'":
                    stream.write("''")
                else:
                    stream.write(ch)
            stream.write("'")
            return "#" + stream.getvalue()
        elif self.type == "string":
            stream = StringIO.StringIO()
            stream.write("'")
            for ch in self.value:
                if ch == "'":
                    stream.write("''")
                else:
                    stream.write(ch)
            stream.write("'")
            return stream.getvalue()
        elif self.type == "comment":
            stream = StringIO.StringIO()
            stream.write("\"")
            for ch in self.value:
                if ch == "\"":
                    stream.write("\"")
                else:
                    stream.write(ch)
            stream.write("\"")
            return stream.getvalue()
        else:
            return self.value

class Scanner(Object):
    def __init__(self, aFragment):
        self.fragment = aFragment
        self.stream = StringIO.StringIO(aFragment.getSource())
        self.lineNumber = 1
        self.nextCharacter = self.readCharacter()
        self.stepCharacter()

    def newToken(self, type, value, lineNumber = None):
        return Token(type, value, lineNumber)

    def ord(self, ch):
        # support for astral unicode surrogate pairs
        if len(ch) == 1:
            return ord(ch)
        if len(ch) == 2:
            return ((ord(ch[0]) - 0xD800) * 0x400) + (ord(ch[1]) - 0xDC00) + 0x10000
        self.error("cannot convert character", ch)

    def readCharacter(self):
        # handle Unicode surrogate pairs
        # D800 - DBFF and DC00 - DFFF
        #(H - 0xD800) * 0x400) + (L - 0xDC00) + 0x10000;
        ch = self.stream.read(1)
        if len(ch) != 1:
            return ch
        if 0xD800 <= ord(ch) <= 0xDBFF:
            ch2 = self.stream.read(1)
            assert 0xDC00 <= ord(ch2) <= 0xDFFF, "invalid unicode surrogate pair"
            return ch+ch2
        else:
            return ch

    def stepCharacter(self):
        self.currentCharacter = self.nextCharacter
        self.nextCharacter = self.readCharacter()
        self.currentCharacterClass = self.classifyCharacter(self.currentCharacter)
        #print self.currentCharacterClass, self.currentCharacter

    def isDigit(self, aCharacter):
        return "0" <= aCharacter <= "9"

    def isLetter(self, aCharacter):
        return "a" <= aCharacter <= "z" or "A" <= aCharacter <= "Z" or aCharacter == "_"

    def classifyCharacter(self, ch):
        if ch == "":
            return "end"
        if self.isDigit(ch):
            return "digit"
        if self.isLetter(ch):
            return "letter"
        if ch in " \n\r\f\t":
            if ch == "\n":
                self.lineNumber +=  1
            return "white"
        if ch in "{}:#'\"-.()^_[]$;":
            return ch
        if ch in "+/\\*~<>=@%|&?!,`":
            return "special_character"
        if 32 < self.ord(ch) > 127:
            return "exotic_character"
        self.error("unclassified character", ch, repr(self.ord(ch)))

    def getBasicToken(self):
        self.scanWhite()
        token = self.scanComment()
        if token is not None:
            return token
        token = self.scanEnd()
        if token is not None:
            return token
        token = self.scanNumber()
        if token is not None:
            return token
        token = self.scanIdentifierOrKeyword()
        if token is not None:
            return token
        token = self.scanString()
        if token is not None:
            return token
        token = self.scanSymbolOrArray()
        if token is not None:
            return token
        token = self.scanCharacter()
        if token is not None:
            return token
        token = self.scanBinarySelector()
        if token is not None:
            return token
        token = self.scanSimple()
        if token is not None:
            return token
        token = self.scanAssignment()
        if token is not None:
            return token
        print self.fragment.getSource()
        self.error(
            "line",
            self.lineNumber,
            "unexpected character",
            self.currentCharacter,
            hex(self.ord(self.currentCharacter)))

    def getToken(self):
        while True:
            token = self.getBasicToken()
            if token.matches("comment"):
                continue
            return token 

    def allBasicTokens(self, includeEndToken = False):
        tokens = []
        token = self.getBasicToken()
        while not token.matches("end"):
            tokens.append(token)
            token = self.getToken()
        if includeEndToken:
            tokens.append(token)
        return tokens

    def scanEnd(self):
        if self.currentCharacter == "":
            return self.newToken("end", "", self.lineNumber)

    def scanIdentifier(self):
        if self.currentCharacterClass == "letter":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass in ["letter","digit"]:
                value.write(self.currentCharacter)
                self.stepCharacter()
            return self.newToken("identifier", value.getvalue(), lineNumber)
        else:
            return None

    def scanIdentifierOrKeyword(self):
        token = self.scanIdentifier()
        if token is None:
            return token
        if self.currentCharacter == ":" and self.nextCharacter != "=":
            self.stepCharacter()
            return self.newToken("keyword", token.value + ":")
        else:
            return token

    def scanWhite(self):
        if self.currentCharacterClass == "white":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            while self.currentCharacterClass == "white":
                value.write(self.currentCharacter)
                self.stepCharacter()
            return self.newToken("white", value.getvalue(), lineNumber)
        else:
            return None

    def scanNumber(self):
        if not (self.currentCharacterClass == "digit" or
             (self.currentCharacter == "-" and self.classifyCharacter(self.nextCharacter) == "digit")):
            return None
        value = StringIO.StringIO()
        value.write(self.currentCharacter)
        self.stepCharacter()
        while self.currentCharacterClass == "digit":
             value.write(self.currentCharacter)
             self.stepCharacter()
        return self.newToken("number", value.getvalue())

    def scanString(self):
        if self.currentCharacter == "'":
            value = StringIO.StringIO()
            self.stepCharacter()
            while True:
                if self.currentCharacter == "'":
                    if self.nextCharacter == "'":
                        self.stepCharacter()
                    else:
                        break
                if self.currentCharacterClass == "end":
                    self.error("unterminated string")
                value.write(self.currentCharacter)
                self.stepCharacter()
            self.stepCharacter()
            return self.newToken("string",value.getvalue())
        else:
            return None

    def scanCharacter(self):
        if self.currentCharacter == "$":
            self.stepCharacter()
            if self.currentCharacterClass == "end":
                self.error("missing character after dollar")
            token = self.newToken("character", self.currentCharacter)
            self.stepCharacter()
            return token
        else:
            return None

    def scanSymbolOrArray(self):
        if self.currentCharacter == "#":
            self.stepCharacter()
            self.scanWhite()
            if self.currentCharacter == "(":
                self.stepCharacter()
                return self.newToken("array", "#(")
            if self.currentCharacter == "[":
                self.stepCharacter()
                return self.newToken("bytearray", "#[")
            if self.currentCharacter == "{":
                self.stepCharacter()
                self.scanWhite()
                identifier = self.scanIdentifier()
                assert identifier is not None
                self.scanWhite()
                if self.currentCharacter != "}":
                    self.error("incomplete qualified reference literal")
                self.stepCharacter()
                return self.newToken("qualified_name", identifier.value)
            if self.currentCharacterClass == "letter":
                value = StringIO.StringIO()
                value.write(self.currentCharacter)
                self.stepCharacter()
                while self.currentCharacterClass in ["letter", "digit", ":"]:
                    value.write(self.currentCharacter)
                    self.stepCharacter()
                return self.newToken("symbol", value.getvalue())
            if self.currentCharacter == "'":
                token = self.scanString()
                if token is not None:
                    return self.newToken("symbol", token.value)
            token = self.scanBinarySelector()
            if token is None:
                self.error("incomplete literal after hash")
            return self.newToken("symbol", token.value)
        else:
            return None

    def scanComment(self):
        if self.currentCharacter == "\"":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            self.stepCharacter()
            while self.currentCharacter != "\"":
                if self.currentCharacterClass == "end":
                    self.error("unterminated comment")
                value.write(self.currentCharacter)
                self.stepCharacter()
            self.stepCharacter()
            return self.newToken("comment", value.getvalue(), lineNumber)
        else:
            return None

    def scanBinarySelector(self):
        if self.currentCharacter == "-":
            self.stepCharacter()
            return self.newToken("binary_selector","-")
        if self.currentCharacterClass == "special_character":
            value = StringIO.StringIO()
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass == "special_character":
                value.write(self.currentCharacter)
                self.stepCharacter()
            return self.newToken("binary_selector",value.getvalue())
        else:
            return None

    def scanSimple(self):
        if self.currentCharacter in "^.()[]{};":
            token = self.newToken(self.currentCharacter, self.currentCharacter, self.lineNumber)
            self.stepCharacter()
            return token
        else:
            return None

    def scanAssignment(self):
        if self.currentCharacter == ":":
            self.stepCharacter()
            if self.currentCharacter == "=":
                self.stepCharacter()
                return self.newToken("assignment",":=")
            else:
                return self.newToken(":", ":")
        else:
            return None

class GSScanner(Scanner):
    pass

class VWScanner(Scanner):
    # VW version needs to support dot notation (e.g. Core.Integer)

    def scanIdentifier(self):
        if self.currentCharacterClass == "letter":
            value = StringIO.StringIO()
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass in ["letter","digit","."]:
                value.write(self.currentCharacter)
                self.stepCharacter()
            return self.newToken("identifier", value.getvalue())
        else:
            return None

class ST80Scanner(Scanner):
    def isLetter(self, aCharacter):
        # UNDERLINE is not a letter and not part of an identifer in ST80
        return "a" <= aCharacter <= "z" or "A" <= aCharacter <= "Z"

    def scanAssignment(self):
        # UNDERLINE is used as short assignment
        if self.currentCharacter == "_":
            self.stepCharacter()
            return self.newToken("assignment", "_")
        else:
            return Scanner.scanAssignment(self)

class Node(Object):
    def __init__(self):
        pass

    def __repr__(self):
        return self.__class__.__name__ + "(" + ")"

    def isSequenceNode(self):
        return False

    def isMethodNode(self):
        return False

    def isMessageNode(self):
        return False

    def isVariableNode(self):
        return False

    def isLiteralValueNode(self):
        return False

    def isBlockNode(self):
        return True

    def isReturnNode(self):
        return True

    def printCode(self):
        stream = StringIO.StringIO()
        self.writeCodeOn(stream)
        print stream.getvalue()

class ReturnNode(Node):
    def __init__(self):
        self.assignment = None

    def isReturnNode(self):
        return True

class MethodNode(Node):
    def __init__(self):
        self.selector = None
        self.body = None

    def isMethodNode(self):
        return True

class SequenceNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.statements = []

    def isSequenceNode(self):
        return True

    def addStatement(self, aNode):
        self.statements.append(aNode)

    def printStructure(self, indent=0):
        print self.__class__.__name__
        self.indentedPrint(indent + 1, "temporaries")
        for each in self.temporaries:
            each.printStructure(indent + 2)
        self.indentedPrint(indent + 1,"statements")
        for each in self.statements:
            each.printStructure(indent + 2)

    def writeCodeOn(self, aStream):
        for each in self.statements:
            each.writeCodeOn(aStream)

    def evaluate(self, aContext):
        print self
        assert self.temporaries == [], 'evaluation of temporaries not yet supported'
        for each in self.statements:
            result = each.evaluate(aContext)
        return result
#
# ArrayNode for curly arrays. It has statements but no temporaries as a genuine SequenceNode.
#
class ArrayNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.statements = []

    def isArrayNode(self):
        return True

    def addStatement(self, aNode):
        self.statements.append(aNode)

class ExpressionNode(Node):
    def printStructure(self, indent=0):
        print self.__class__.__name__

class PrimaryNode(Node):
    def printStructure(self, indent=0):
        print self.__class__.__name__

class MessageNode(Node):
    def printStructure(self, indent=0):
        print self.__class__.__name__
        print "  receiver:"
        self.receiver.printStructure(indent + 1)
        self.indentedPrint(indent + 1 , "  selector:", self.selector)

    def isMessageNode(self):
        return True

    def evaluate(self, aContext):
        self.notYetImplemented()

class CascadeNode(Node):
    def __init__(self):
        self.messages = []

    def isCascadeNode(self):
        return True

    def addMessage(self, aMessageNode):
        self.messages.append(aMessageNode)

class AssignmentNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.variable = None
        self.statement = None

    def printStructure(self,indent):
        print self.__class__.__name__,
        self.variable.printStructure(indent)
        print ":="

class VariableNode(Node):
    def __init__(self, aString):
        Node.__init__(self)
        self.name = aString

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.name + ")"

    def isVariableNode(self):
        return True

    def printStructure(self, indent):
        self.indentedPrint(indent, self.name)

    def writeCodeOn(self, aStream):
        aStream.write(self.name)

class LiteralValueNode(Node):
    def __init__(self, aValue):
        Node.__init__(self)
        self.value = aValue

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.value) + ")"

    def isLiteralValueNode(self):
        return True

    def printStructure(self, indent):
        self.indentedPrint(indent,  self.__class__.__name__ + "("+ repr(self.value) + ")")

    def evaluate(self, aContext):
        return self.value

class LiteralArrayNode(Node):
    def __init__(self, isForByteArray):
        Node.__init__(self)
        self.elements = []
        self.isForByteArray = isForByteArray

    def isLiteralArrayNode(self):
        return True

    def addElement(self, aValue):
        self.elements.append(aValue)

class BlockNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.arguments = []
        self.body = None   # should be a sequence node

    def isBlockNode(self):
        return True

    def __repr__(self):
        return self.__class__.__name__ + "(...)" 

    def addArgument(self, aVariableNode):
        self.arguments.append(aVariableNode)

    def writeCodeOn(self, aStream):
        aStream.write("[")
        if self.arguments != []:
            for each in self.arguments:
                aStream.write(":"+ each.name+" ")
            aStream.write("|")
        self.body.writeCodeOn(aStream)
        aStream.write("]")

class Parser(Object):
    def __init__(self, aFragment):
        self.lineNumber = aFragment.lineNumber
        #print "Parse linenumber", self.lineNumber
        self.scanner = self.newScanner(aFragment)
        self.nextToken = self.scanner.getToken()
        self.step()

    def scannerClass(self):
        return Scanner

    def newScanner(self, aFragment):
        return self.scannerClass()(aFragment)

    def step(self):
        self.currentToken = self.nextToken
        self.nextToken = self.scanner.getToken()
        #print "Parsed token", self.currentToken

    def matches(self, type, value = None):
        return self.currentToken.matches(type, value)

    def process(self):
        node = self.parseStatements()
        #node.printStructure()
        if not self.currentToken.matches("end"):
            self.reportParsingError("unexpected input in line", self.currentToken)
        return node

    def processMethodDefinition(self):
        if self.matches("identifier"):
            selector = self.currentToken.value
        elif self.matches("binary_selector"):
            selector = self.currentToken.value
        elif self.matches("keyword"):
            selector = ""
            while self.matches("keyword"):
                selector = selector + self.currentToken.value
                self.step()
                if self.matches("identifier"):
                    self.step()
                else:
                    self.reportParsingError("Argument identifier expected in method definition", self.currentToken)
        else:
            return None
        # requires full parsing #self.parseStatements()
        node = MethodNode()
        node.selector = selector
        return node

    def parseMethodBody(self):
        temporaries = self.parseTemporaries()
        statements = self.parseStatements()
        statements.temporaries = temporaries
        return statements

    def parseTemporaries(self):
        temporaries = []
        if not self.currentToken.matches("binary_selector", "|"):
            return temporaries
        self.step()
        while self.currentToken.matches("identifier"):
            temporaries.append(VariableNode(self.currentToken.value))
            self.step()
        if not self.currentToken.matches("binary_selector", "|"):
            self.error("identifier or | expected in temporaries")
        self.step()
        return temporaries

    def parseStatements(self):
        node = SequenceNode()
        return self.parseStatementsInto(node)

    def parseStatementsInto(self, aSequenceNode):
        aSequenceNode.temporaries = self.parseTemporaries()
        return self.parseStatementListInto(aSequenceNode)

    def parseStatementListInto(self, aSequenceNode):
        statement = self.parseStatement()
        while statement is not None:
            aSequenceNode.addStatement(statement)
            if self.currentToken.matches("."):
                self.step()
                statement = self.parseStatement()
            else:
                statement = None
        return aSequenceNode

    def parseAssignment(self):
        if (self.currentToken.matches("identifier") and
                self.nextToken.matches("assignment")):
            node = AssignmentNode()
            node.variable = VariableNode(self.currentToken.value)
            self.step()  # variable
            self.step()  # assignment
            node.statement = self.parseAssignment()
            if node.statement is None:
                self.reportParsingError("assignment must be followed by a statement", self.currentToken)
            return node
        else:
            return self.parseCascadeMessage()

    def parseCascadeMessage(self):
        node = self.parseKeywordMessage()
        if not self.matches(";"):
            return node
        receiver = node.receiver
        cascadeNode = CascadeNode()
        cascadeNode.addMessage(node)
        while self.matches(";"):
            self.step()
            node = self.parseUnaryMessageWith(receiver)
            if node is None:
                node = self.parseKeywordMessageWith(receiver)
            if node is None:
                self.reportParsingError("something wrong in cascade", self.currentToken)
            cascadeNode.addMessage(node)
        return cascadeNode

    def parseKeywordMessage(self):
        node = self.parseBinaryMessage()
        if not self.currentToken.matches("keyword"):
            return node
        return self.parseKeywordMessageWith(node)

    def parseKeywordMessageWith(self, aNode):
        selector = ''
        arguments = []
        while self.currentToken.matches("keyword"):
            selector = selector + self.currentToken.value
            self.step()
            arguments.append(self.parseBinaryMessage())
        newNode = MessageNode()
        newNode.receiver = aNode
        newNode.selector = selector
        newNode.arguments = arguments
        return newNode

    def parseBinaryMessage(self):
        node = self.parseUnaryMessage()
        while self.currentToken.matches("binary_selector"):
            newNode = MessageNode()
            newNode.receiver = node
            newNode.selector = self.currentToken.value
            self.step()
            newNode.arguments = [self.parseUnaryMessage()]
            node = newNode
        return node

    def parseUnaryMessage(self):
        node = self.parsePrimitiveObject()
        while self.matches("identifier"):
            node = self.parseUnaryMessageWith(node)
        return node

    def parseUnaryMessageWith(self, aNode):
        if not self.matches("identifier"):
            return None
        node = MessageNode()
        node.receiver = aNode
        node.selector = self.currentToken.value
        self.step()
        return node

    def parsePrimitiveObject(self):
        node = self.parseVariable()
        if node is not None:
            return node
        node = self.parsePrimitiveLiteral()
        if node is not None:
            return node
        node = self.parseBlock()
        if node is not None:
            return node
        node = self.parseLiteralArray()
        if node is not None:
            return node
        node = self.parseParenthesizedExpression()
        if node is not None:
            return node
        return None

    def parsePrimitiveIdentifier(self):
        if not self.currentToken.matches("identifier"):
            return None
        node = VariableNode(self.currentToken.value)
        self.step()
        return node

    def parseVariable(self):
        return self.parsePrimitiveIdentifier()

    def parsePrimitiveValueLiteral(self):
        if self.currentToken.matches("string"):
            node = LiteralValueNode(String(self.currentToken.value))
            self.step()
            return node
        if self.currentToken.matches("symbol"):
            node = LiteralValueNode(Symbol(self.currentToken.value))
            self.step()
            return node
        if self.currentToken.matches("character"):
            node = LiteralValueNode(Character(self.currentToken.value))
            self.step()
            return node
        if self.currentToken.matches("qualified_name"):
            node = LiteralValueNode(String(self.currentToken.value))
            self.step()
            return node
        return None

    def parseNumberLiteral(self):
        if not self.currentToken.matches("number"):
            return None
        node = LiteralValueNode(Number(self.currentToken.value))
        self.step()
        return node

    def parsePrimitiveLiteral(self):
        node = self.parsePrimitiveValueLiteral()
        if node is not None:
            return node
        node = self.parseNumberLiteral()
        if node is not None:
            return node
        return None

    def parseBlock(self):
        if not self.currentToken.matches("["):
            return None
        self.step()
        node = BlockNode()
        if self.currentToken.matches(":"):
            while self.currentToken.matches(":"):
                self.step()
                variableNode = self.parseVariable()
                #print "block variable", variableNode
                if variableNode is None:
                    self.error("variable expected after colon")
                node.addArgument(variableNode)
            if not self.currentToken.matches("binary_selector","|"):
                self.reportParsingError('"|" expected after block variable list', self.currentToken)
            self.step()
        node.body = self.parseStatements()
        #print self.currentToken
        if not self.currentToken.matches("]"):
            self.reportParsingError('"]" expected at the end of a block', self.currentToken)
        self.step()
        return node

    #parseLiteralByteArrayObject
    #(currentToken isLiteralToken and:
    #[currentToken value isInteger and:[currentToken value between: 0 and: 255]])
    #ifFalse: [self parserError: (  # Expecting8bitInteger << #browser >> 'Expecting 8-bit integer')].
    #    ^ self parsePrimitiveLiteral
    def parseLiteralArray(self, nested = False):
        if self.currentToken.matches("array") or (nested and self.currentToken.matches("(")):
            newNode = LiteralArrayNode(isForByteArray=False)
            self.step()
            node = self.parseLiteralArrayObject()
            while node is not None:
                newNode.addElement(node)
                node = self.parseLiteralArrayObject()
            if not self.matches(")"):
                print self.scanner.fragment.getSource()
                self.reportParsingError('")" expected', self.currentToken)
            self.step()
            return newNode
        elif self.currentToken.matches("bytearray"):
            newNode = LiteralArrayNode(isForByteArray=True)
            self.step()
            while True:
                node = self.parseNumberLiteral()
                if node is None:
                    break
                #if not (0 <= node.value.getInternalValue() <= 255):
                #    print self.scanner.fragment.getSource()
                #    self.reportParsingError('byte arrays only support 8 bit numbers '+repr(node.value.getInternalValue()))
                newNode.addElement(node)
            if not self.matches("]"):
                print self.scanner.fragment.getSource()
                self.reportParsingError('"]" expected', self.currentToken)
            self.step()
            return newNode
        else:
             return None

    def parseLiteralArrayObject(self):
        node = self.parseNumberLiteral()
        if node is not None:
            return node
        node = self.parsePrimitiveValueLiteral()
        if node is not None:
            return node
        node = self.parseVariable()
        if node is not None:
            # Inside array literals, identifiers are converted to symbols.
            # (The variable node is converted to literal array node.)
            return LiteralValueNode(Symbol(node.name))
        node = self.parseLiteralArray(nested = True)
        if node is not None:
            return node
        return None

    def parseParenthesizedExpression(self):
        if not self.currentToken.matches("("):
            return None
        self.step()
        node = self.parseAssignment()
        if not self.currentToken.matches(")"):
            self.reportParsingError('")" expected instead of', self.currentToken)
        self.step()
        return node

    def parseStatement(self):
        node = self.parseReturn()
        if node is not None:
            return node
        node = self.parseAssignment()
        if node is not None:
            return node
        node = self.parseExpression()
        if node is not None:
            return node
        self.error("cannot parse statement")

    def parseReturn(self):
        if not self.matches("^"):
            return None
        node = ReturnNode()
        self.step()
        assignment = self.parseAssignment()
        if assignment is None:
            self.reportParsingError('missing statement or expression after ^', self.currentToken)
        node.assignment = assignment
        return node


    def parseExpression(self):
        primary = self.parsePrimary()
        expression = ExpressionNode()
        expression.primary = primary
        return expression

    def parsePrimary(self):
        if self.currentToken.matches("identifier"):
            node = VariableNode(self.currentToken.value)
            self.step()
            return node
        if self.currentToken.matches("string"):
            node = LiteralNode(self.currentToken.value)
            self.step()
            return node
        return None

    def parseMessage(self):
        if self.currentToken.matches("identifier"):
            node = MessageNode()
            node.selector = self.currentToken.value
            self.step()
            return node
        self.error("unexpected message token", self.currentToken)

    def reportParsingError(self, aString, token = None):
        print self.scanner.fragment.source
        lineNumber = self.lineNumber
        if token is not None:
            lineNumber += token.lineNumber
        print "Line", str(lineNumber)+":", aString,
        if token is not None:
            print 'instead of', token
        sys.exit(2)

class GSParser(Parser):
    def scannerClass(self):
        return GSScanner

    def parsePrimitiveObject(self):
        node = Parser.parsePrimitiveObject(self)
        if node is not None:
            return Node
        node = self.parseCurlyArray()
        if node is not None:
            return node
        return node

    def parseCurlyArray(self):
        if not self.matches('{'):
            return None
        self.step()
        node = ArrayNode()
        self.parseStatementListInto(node)
        if self.matches('}'):
            self.step()
            return node
        else:
            self.reportParsingError('"}" expected', self.currentyToken)

class VWParser(Parser):
    def scannerClass(self):
        return VWScanner

class BasicClass(Object):
    def __init__(self, aString):
        self.name = aString
        self.superclass = None
        self.instVars = []
        self.methodsDictionary = {}

    def setInstVars(self, someStrings):
        #print "Set instVars", someStrings
        assert self.instVars == []
        self.instVars = someStrings

    def getAllMethods(self):
        return sorted(self.methodsDictionary.values())

    def getAllMethodCategories(self):
        categories = []
        for each in self.getAllMethods():
            if not each.category in categories:
                categories.append(each.category)
        categories.sort()
        return categories

class Class(BasicClass):
    def __init__(self, aString):
        BasicClass.__init__(self, aString)
        self.metaClass = MetaClass(aString + " class")
        self.category = ""
        self.classVars = []
        self.classType = ""
        self.classOptions = []

    def setName(self, aString):
        assert self.name == aString

    def setSuperclass(self, aClass):
        assert self.superclass is None
        self.superclass = aClass

    def setCategory(self, aString):
        #print "Set class category", aString
        assert self.category == ""
        self.category = aString

    def setClassInstVars(self, someStrings):
        assert self.metaClass.instVars == []
        self.metaClass.setInstVars(someStrings)

    def setClassVars(self, someStrings):
        #print "Set classVars", someStrings
        assert self.classVars == []
        self.classVars = someStrings

    def setClassType(self, aString):
        #print "Set classType", aString
        assert self.classType == ""
        self.classType = aString

    def setClassOptions(self, someStrings):
        #print "Set classOptions", someStrings
        assert self.classOptions == []
        self.classOptions = someStrings

    def getClassDefinition(self):
        stream = StringIO.StringIO()
        if self.superclass is None:
            stream.write("nil")
        else:
            stream.write(self.superclass.name)
        stream.write(" subclass: ")
        stream.write(self.name)
        stream.write("\n")
        stream.write("\tinstVarNames: ")
        stream.write(self.instVars)
        stream.write("\n")
        stream.write("\tclassInstVarNames: ")
        stream.write(self.metaClass.instVars)
        stream.write("\n")
        stream.write("\tclassVarNames: ")
        stream.write(self.classVars)
        stream.write("\n")
        return stream.getvalue()

class MetaClass(BasicClass):
    def __init__(self, aString):
        assert aString.split()[1] == "class", "invalid name for meta class"
        BasicClass.__init__(self, aString)

class CompiledMethod(Object):
    def __init__(self):
        self.source = None
        self.methodClass = None
        self.selector = None

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.selector) + ")"

    def getSignature(self):
        return self.methodClass.name + ">>" + self.selector

    def printStructure(self):
        print self.getSignature()
        print self.source


class Compiler(Object):
    def makeCompiledMethodForSource(self, aFragment):
        parser = self.newParser(aFragment)
        node = parser.processMethodDefinition()
        if node is None:
            print "========"
            print aFragment.getSource()
            self.error("method definition expected")
        newMethod = CompiledMethod()
        newMethod.source = aFragment.getSource()
        newMethod.selector = node.selector
        #print newMethod
        return newMethod

    def process(self, aFragment):
        #print "start process"
        #print "-----------------------------------------"
        #print aString
        #print "-----------------------------------------"
        parser = self.newParser(aFragment)
        return parser.process()
        #print "end process"
        #self.halt("Compiler>>process completed", aString)

    def newParser(self, aFragment):
        return self.parserClass()(aFragment)

    def parserClass(self):
        self.subclassResponsibility()

class GSCompiler(Compiler):
    def parserClass(selfself):
        return GSParser

class VWCompiler(Compiler):
    def parserClass(selfself):
        return VWParser

class TonelLoader(PackageLoader, GSScanner):
    def compilerClass(self):
        return GSCompiler

    def processFile(self, aFilename):
        if not os.path.isdir(aFilename):
           if os.path.basename(aFilename) == "properties.st":
               return
           self.error(aFilename, "tonel packages must be directories")
        packageFile = os.path.join(aFilename, "package.st")
        if not os.path.exists(packageFile):
            self.error(aFilename, "missing package.st")
        classFiles = glob.glob(os.path.join(aFilename, "*.class.st"))
        extensionFiles = glob.glob(os.path.join(aFilename, "*.extension.st"))
        allFiles = classFiles + extensionFiles
        if len(allFiles) == 0:
            self.warn(aFilename, "no class files found")
        for each in allFiles:
            self.processClassFile(each)

    def processClassFile(self, aFilename):
        self.info("Process class file", aFilename)
        self.stream = codecs.open(aFilename, encoding='UTF-8')
        self.lineNumber = 1
        self.nextCharacter = self.readCharacter()
        self.stepCharacter()
        self.parseTonelUnit()
        self.stream.close()
        return self.targetPackage

    # This scanner must distinguish between Smalltalk tokens (mainly in method bodies)
    # and Tonel tokens.
    def getToken(self):
        token = self.scanWhite()
        if token is not None:
            return token
        token = self.scanComment()
        if token is not None:
            return token
        return Scanner.getToken(self)

    def stepTonelToken(self):
        self.currentToken = self.parseTonelValue()

    def parseTonelUnit(self):
        self.stepTonelToken()
        if self.currentToken.matches("string"):
            comment = self.currentToken.value
            self.stepTonelToken()
        self.parseTonelClass()
        if self.currentCharacter != "":
            self.reportTonelError(self.currentToken.lineNumber, "unexpected", repr(self.currentToken.value))

    def reportTonelError(self, lineNumber, *args):
        print "Line", str(lineNumber)+":", string.join(map(lambda each: str(each), args), " ")
        sys.exit(1)

    def parseTonelValue(self):
        self.skipTonelSeparators()
        if self.currentCharacter == "":
            return None
        token = self.scanTonelString()
        if token is not None:
            return token
        token = self.scanTonelIdentifierOrKeyword()
        if token is not None:
            return token
        token = self.parseTonelDictionary()
        if token is not None:
            return token
        token = self.parseTonelList()
        if token is not None:
            return token
        self.reportTonelError(self.lineNumber, "unknown character", self.currentCharacter)

    def skipTonelSeparators(self):
        while self.currentCharacter != "" and self.currentCharacter in "\n\r\f \t":
            self.stepCharacter()

    # Unlike Smalltalk comments, tonel string can have two consecutive double quotes.
    def scanTonelString(self):
        if self.currentCharacter not in  "\"'":
            return None
        delimiter = self.currentCharacter
        lineNumber = self.lineNumber
        value = StringIO.StringIO()
        self.stepCharacter()
        while True:
            if self.currentCharacter == delimiter:
                if self.nextCharacter == delimiter:
                    self.stepCharacter()
                else:
                    break
            if self.currentCharacter == "":
                self.reportTonelError(lineNumber, "unterminated string literal")
            value.write(self.currentCharacter)
            self.stepCharacter()
        self.stepCharacter()
        return Token("string", value.getvalue(), lineNumber)

    def scanTonelSymbol(self):
        if self.currentCharacter != "#":
            return None
        lineNumber = self.lineNumber
        self.stepCharacter()
        assert self.currentCharacter.isalpha()
        value = StringIO.StringIO()
        while self.currentCharacter.isalnum() or self.currentCharacter == "_":
            value.write(self.currentCharacter)
            self.stepCharacter()
        self.stepCharacter()
        return Token("symbol", value.getvalue(), lineNumber)

    def parseTonelDictionary(self):
        if self.currentCharacter != '{':
            return None
        lineNumber = self.lineNumber
        self.stepCharacter()
        result = {}
        while True:
            self.scanWhite()
            if self.currentCharacter == "":
                self.error("unterminated dictionary")
            # key can be symbol or string
            self.currentToken = self.scanTonelSymbol()
            if self.currentToken is None:
                self.reportTonelError(self.lineNumber, "dictionary key expected")
            key = self.currentToken.value
            self.scanWhite()
            colon = self.scanTonelColon()
            if colon is None:
                self.reportTonelError(self.lineNumber, 'colon expected')
            value = self.parseTonelObject()
            if value is None:
                print self.currentToken
                self.reportTonelError(self.lineNumber, "dictionary object expected")
            if result.has_key(key):
                self.reportTonelError(None,"duplicate key in dictionary")
            result[key] = value.value
            self.scanWhite()
            if self.currentCharacter == ",":
                self.stepCharacter()
            else:
                break
        if self.currentCharacter != "}":
            self.error(self.currentLine, "'}' expected")
        self.stepCharacter()
        return Token("dictionary", result, lineNumber)

    def scanTonelList(self):
        if self.currentCharacter != '[':
            return None
        lineNumber = self.lineNumber
        self.stepCharacter()
        result = []
        while True:
            self.skipTonelSeparators()
            if self.currentCharacter == "":
                self.error("unterminated dictionary")
            element = self.parseTonelObject()
            if element is not None:
                result.append(element.value)
            self.skipTonelSeparators()
            if self.currentCharacter == ",":
                self.stepCharacter()
            else:
                break
        if self.currentCharacter != "]":
            self.reportTonelError(self.lineNumber, "']' expected")
        self.stepCharacter()
        return Token("list", result, lineNumber)

    def parseTonelObject(self):
        self.skipTonelSeparators()
        value = self.scanTonelString()
        if value is not None:
            return value
        value = self.scanTonelList()
        if value is not None:
            return value
        return None

    def scanTonelColon(self):
        if self.currentCharacter != ":":
            return None
        self.stepCharacter()
        return Token("colon",":")

    def scanTonelIdentifierOrKeyword(self):
        if not self.currentCharacter.isalpha() or self.currentCharacter == "_":
            return None
        lineNumber = self.lineNumber
        value = StringIO.StringIO()
        while self.currentCharacter.isalnum() or self.currentCharacter == "_":
            value.write(self.currentCharacter)
            self.stepCharacter()
        if self.currentCharacter == ":":
            value.write(self.currentCharacter)
            self.stepCharacter()
            return Token("keyword", value.getvalue(), lineNumber)
        else:
            return Token("identifier", value.getvalue(), lineNumber)

    def scanTonelBinary(self):
        if self.currentCharacter not in ">":
            return None
        value = StringIO.StringIO()
        while self.currentCharacter in ">":
            value.write(self.currentCharacter)
            self.stepCharacter()
        return Token("binary", value.getvalue())

    def scanTonelSpecial(self):
        specialCharacters = ":>"
        if self.currentCharacter not in specialCharacters:
            return None
        lineNumber = self.lineNumber
        value = StringIO.StringIO()
        while self.currentCharacter in specialCharacters:
            value.write(self.currentCharacter)
            self.stepCharacter()
        return Token("special", value.getvalue(), lineNumber)

    def parseTonelClass(self):
        if not self.currentToken.matches("identifier"):
            print self.currentToken
            assert self.currentToken.matches("identifier")
        unitType = self.currentToken.value
        assert unitType in [ "Class", "Extension" ]
        self.stepTonelToken()
        if not self.currentToken.matches("dictionary"):
            self.reportTonelError(self.currentToken.lineNumber, "missing class attributes")
        attributes = self.currentToken.value
        assert len(attributes) > 0, "empty class attributes"
        self.targetClass = self.targetImage.findOrCreateClassNamed(attributes["name"])
        for key, value in attributes.items():
            key = key.lower()
            if key == "category":
                self.targetClass.setCategory(value)
            elif key == "name":
                self.targetClass.setName(value)
            elif key == "superclass":
                mySuperclass = self.targetImage.findOrCreateClassNamed(value)
                self.targetClass.setSuperclass(mySuperclass)
            elif key == "instvars":
                self.targetClass.setInstVars(value)
            elif key == "classinstvars":
                self.targetClass.setClassInstVars(value)
            elif key == "classvars":
                self.targetClass.setClassVars(value)
            elif key == "gs_options":
                self.targetClass.setClassOptions(value)
            elif key == "type":
                self.targetClass.setClassType(value)
            else:
                self.reportTonelError(0, "unknown class attribute", key)

        self.parseTonelCategoriesAndMethods()

    def parseTonelCategoriesAndMethods(self):
        while True:
            self.currentToken = self.scanWhite()
            self.currentToken = self.scanEnd()
            if self.currentToken is not None:
                break
            attributes = self.parseTonelDictionary()
            if attributes is not None:
                self.processTonelMethodCategoryDictionary(attributes.value)
                continue
            if self.readAndProcessTonelMethod():
                continue
            self.error("unexpected data in unit")

    def readAndProcessTonelMethod(self):
        name = self.scanIdentifier()
        if name is None:
            return False
        name = name.value
        lineNumber = self.lineNumber
        self.skipTonelSeparators()
        side = self.scanIdentifier()
        if side is not None:
            side = side.value
        #print name, side
        self.skipTonelSeparators()
        special = self.scanTonelSpecial()
        if special is None or not special.matches("special", ">>"):
            self.reportTonelError(None, ">> expected")
        self.currentToken = self.getToken()
        methodSource = StringIO.StringIO()
        while self.currentToken.type in ['identifier', 'keyword', 'white', 'binary_selector']:
            methodSource.write(self.currentToken.value)
            self.currentToken = self.getToken()
        self.parseTonelMethodBody(methodSource)
        methodSource = methodSource.getvalue().strip()
        #print methodSource
        if side in [ "class", "classSide" ]:
            self.addClassMethod(name, Fragment(methodSource, lineNumber))
        elif side is None:
            self.addInstanceMethod(name, Fragment(methodSource, lineNumber))
        else:
            self.error("unexpected side", repr(side))
        return True

    def parseTonelMethodBody(self, aStream):
        if not self.currentToken.matches("["):
            self.reportTonelError(self.currentToken.lineNumber, "missing '['")
        self.currentToken = self.getToken()
        while not self.currentToken.matches("]"):
            if self.currentToken.matches("end"):
                self.reportTonelError(self.lineNumber, "unexpected end")
            aStream.write(self.currentToken.asSource())
            # process nested blocks
            if self.currentToken.type in [ "[", "bytearray" ]:
                self.parseTonelNestedBlock(aStream)
            else:
                self.currentToken = self.getToken()
        if not self.currentToken.matches("]"):
            self.reportTonelError(self.currentToken.lineNumber, "missing ']'")
        self.currentToken = self.getToken()

    def parseTonelNestedBlock(self, aStream):
        assert self.currentToken.type in [ "[", "bytearray" ]
        #aStream.write(self.currentToken.value)
        self.currentToken = self.getToken()
        while not self.currentToken.matches("]"):
            assert not self.currentToken.matches("end")
            aStream.write(self.currentToken.asSource())
            # process nested blocks
            if self.currentToken.type in ["[", "bytearray"]:
                self.parseTonelNestedBlock(aStream)
            else:
                self.currentToken = self.getToken()
        assert self.currentToken.matches("]")
        aStream.write(self.currentToken.value)
        self.currentToken = self.getToken()

    def processTonelMethodCategoryDictionary(self, aDictionary):
        assert len(aDictionary) == 1, "method category dictionary expected to have one entry"
        self.setCurrentMethodCategory(aDictionary["category"])

class SmaragdLoader(PackageLoader):
    def processFile(self, aFilename):
        print "Load smaragd file", aFilename
        stream = codecs.open(aFilename, encoding = 'UTF-8')
        while True:
            line = stream.readline()
            if line == "":
                break
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            self.targetImage.loadFile(line)
        stream.close()

class RowanLoader(PackageLoader):
    def processFile(self, aFilename):
        print "Process Rowan repository", aFilename
        packageDirectories = glob.glob(os.path.join(aFilename, "rowan", "sources", "*"))
        if len(packageDirectories) == 0:
            self.error(aFilename, "No packages found.")
        for each in packageDirectories:
            TonelLoader(self.targetImage, each).load()

class Image(Object):
    def __init__(self):
        self.root = {}
        self.packages = {}
        self.classes = {}
        self.filename = None

    def findOrCreateClassNamed(self, aString):
        parts = aString.split()
        className = parts[0]
        newClass = self.classes.get(className, None)
        if newClass is None:
            newClass = Class(className)
            self.classes[aString] = newClass
            newClass.image = self
            newClass.metaClass.image = self
        if len(parts) == 1:
            return newClass
        if len(parts) == 2 and parts[1] == "class":
            return newClass.metaClass
        self.error("Unsupported class name", aString)

    def findOrCreatePackageNamed(self, aString):
        package = self.packages.get(aString, None)
        if package is None:
            package = Package(aString)
            self.packages[package.name] = package
        return package

    def addCompiledMethod(self, aCompiledMethod):
        methodClass = aCompiledMethod.methodClass
        methodSelector = aCompiledMethod.selector
        if methodClass.methodsDictionary.has_key(methodSelector):
            self.warn("Override", aCompiledMethod.getSignature())
        methodClass.methodsDictionary[methodSelector] = aCompiledMethod

    def loadFile(self, aFilename):
        loader = ImageBuilder(self)
        loader.loadFile(aFilename)

    def getAllClasses(self):
        return self.classes.values()

    def getAllPackages(self):
        return self.packages.values()

    def printStatistics(self):
        print self.__class__.__name__
        print "  Classes:", len(self.classes)
        print "  Methods:", self.getNumberOfMethods()
        #for each in self.methods:
        #    print each.getSignature()
        #    print "  ", each.category
        #for signature, list  in self.methodsDictionary.items():
        #    print signature
        #    for each in list:
        #        print each.source
        
    def getNumberOfMethods(self):
        result = 0
        for each in self.classes.itervalues():
            result += len(each.methodsDictionary)
            result += len(each.metaClass.methodsDictionary)
        return result
        

    def cache(self, recompile):
        assert self.filename is not None
        newFilename = self.filename + ".cached"
        stream = open(newFilename, "wb")
        pickle.dump(self, stream, protocol = pickle.HIGHEST_PROTOCOL)
        stream.close()
        print newFilename
        if Configuration.sessionConfiguration.verboseFlag:
            self.printStatistics()



class ImageBuilder(Object):
    def __init__(self, targetImage):
        self.targetImage = targetImage

    def packageTypeForFilename(self, aFilename, type):
        if type is not None:
            return type
        if os.path.isdir(aFilename):
            if os.path.exists(os.path.join(aFilename, "rowan")):
                return "rowan"
            return "tonel"
        basename, type =  os.path.splitext(aFilename)
        if type.startswith("."):
            type = type[1:]
        if type in ["gs", "st", "smaragd"]:
            return type
        self.error("Unknown file type", aFilename)

    def packageLoaderClassFor(self, type):
        if type == "gs":
            return GSPackageLoader
        if type == "st":
            return VWPackageLoader
        if type == "tonel":
            return TonelLoader
        if type == "smaragd":
            return SmaragdLoader
        if type == "rowan":
            return RowanLoader
        self.error("Unsupported file type", type)

    def newPackageLoader(self, aFilename, type):
        packageType = self.packageTypeForFilename(aFilename, type)
        loaderClass = self.packageLoaderClassFor(packageType)
        return loaderClass(self.targetImage, aFilename)

    def loadFile(self, aFilename, type = None):
        self.newPackageLoader(aFilename, type).load()

if __name__ == "__main__":
    options, arguments = getopt.getopt(sys.argv[1:], "vcr")
    action = None
    for option, value in options:
        if option == "-v":
            Configuration.sessionConfiguration.verboseFlag = True
        elif option == "-c":
            action = "cache"
        elif option == "-r":
            action = "recache"
        else:
            print "Option", option, "not supported."
    if len(arguments) == 0:
        filename = "scmd.smaragd"
    else:
        filename = arguments[0]
    image = Image()
    image.loadFile(filename)
    image.filename = filename
    if action == "cache":
        image.cache(False)
    elif action == "recache":
        image.cache(True)
    else:
        image.printStatistics()

