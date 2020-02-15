#!/usr/bin/python

import sys, getopt, glob
import os, os.path, codecs
import StringIO, string
from collections import OrderedDict

class EmptyHandler:
    def setName(self, value):
        pass
    
    def setUnitType(self, value):
        pass
        
    def setInstVars(self, value):
        pass
        
    def setClassInstVars(self, value):
        pass
        
    def setClassVars(self, value):
        pass
        
    def setClassCategory(self, value):
        pass
        
    def setSuperclass(self, value):
        pass

    def setClassType(self, value):
        pass
        
    def setCurrentMethodCategory(self, value):
        pass
        
    def addClassMethod(self, name):
        pass
        
    def addInstanceMethod(self, name):
        pass

    def setClassComment(self, value):
        pass

    def addMethod(self, selector, arguments, methodSide, methodClass):
        pass

    def addTemporary(self, name):
        # This hack was added as a shortcut.
        pass
    
    def addUnaryMessageSend(self, name):
        # This hack was added as a shortcut.
        pass    
    
    def setConstraints(self, name):
        pass
        
    def addMethodBody(self, node):
        pass

class BasicHandler(EmptyHandler):
    def addMethod(self, selector, arguments, methodSide, methodClass):
        self.currentMethodSelector = selector
        self.currentMethodClass = methodClass + ("" if methodSide == "instance" else " " + methodSide)

    def getCurrentMethodSignature(self):
        return self.currentMethodClass + ">>" + self.currentMethodSelector

class DebugHandler(BasicHandler):
    def setName(self, value):
        print "name:", value
    
    def setUnitType(self, value):
        print "unit type:", value
        
    def setInstVars(self, value):
        print "ivars:", value
        
    def setClassInstVars(self, value):
        print "civars:", value
        
    def setClassVars(self, value):
        print "cvars:", value
        
    def setClassCategory(self, value):
        print "class category:", value
        
    def setSuperclass(self, value):
        print "superclass:", value

    def setClassType(self, value):
        print "class type:", value
        
    def setCurrentMethodCategory(self, value):
        pass
        #print "method category:", value
        
    def addClassMethod(self, name):
        print "class method:", name
        
    def addInstanceMethod(self, name):
        print "instance method:", name

    def setClassComment(self, value):
        print "class comment...", repr(value)      

    def addMethod(self, selector, arguments, methodSide, methodClass):
        print "Add method", methodClass, methodSide, ">>", selector

class Token:
    def __init__(self, type, value, lineNumber):
        self.type = type
        self.value = value
        self.lineNumber = lineNumber

    def __repr__(self):
        stream = StringIO.StringIO()
        stream.write(self.__class__.__name__ + "(" + self.type)
        if self.type != self.value and self.value != "":
            stream.write(", " + repr(self.value))
        stream.write(")")
        return stream.getvalue()

    def matches(self, aType, aValue=None):
        return ((aType is None or self.type == aType)
            and (aValue is None or self.value == aValue))
          
class Parser:
    def __init__(self):
        self.handler = None
    
    def processCommandLine(self):
        try:
            self.basicProcessCommandLine()
        except KeyboardInterrupt:
            sys.stderr.write("\nInterrupted...\n")
    
    def basicProcessCommandLine(self):
        options, arguments = getopt.getopt(sys.argv[1:],"")
        for option, value in options:
            pass
        if arguments == []:
            print "No arguments found"
            sys.exit(2) 
        self.numberOfProcessedFiles = 0
        for argument in arguments:
            for fn in glob.glob(argument):
                self.processFileOrDirectory(fn)
        if self.numberOfProcessedFiles == 0:
            print "No files processed"
                    
    def error(self, *args):
        print "error:", string.join(map(lambda each: repr(each), args), " ")
        sys.exit(1)
        
    def reportTonelError(self, lineNumber, *args):
        print string.join(map(lambda each: str(each), args), " "), "in", os.path.basename(self.currentFilename)+":"+str(lineNumber), "in", os.path.dirname(self.currentFilename)
        sys.exit(1)
    
    def parsingError(self, aString, token = None):
        if token is None:
            token = self.currentToken
        print aString,  "instead of", token  
        print os.path.basename(self.currentFilename)+":"+str(self.lineNumber), "in", os.path.dirname(self.currentFilename)+'/'
        sys.exit(1)
        
    def matches(self, type, value = None):
        return self.currentToken.matches(type, value)
        
    def processFileOrDirectory(self, fn):
        if os.path.isdir(fn):
            self.processDirectory(fn)
        else:
            self.processFile(fn)
    
    def processDirectory(self, fn):
        for each in os.listdir(fn):
            self.processFileOrDirectory(os.path.join(fn, each))
            
    def processFile(self, fn):
        self.currentFilename = fn
        root, ext = os.path.splitext(fn)
        if ext == ".st":
            self.processSmalltalkFile(fn)
            
    def processSmalltalkFile(self, fn):
        root, ext = os.path.splitext(fn)
        root, ext = os.path.splitext(root)
        if ext == ".class" or ext == ".extension":
            self.processSmalltalkClassFile(fn)
            
    def processSmalltalkClassFile(self, fn, ):
        #print "Process", fn
        self.stream = codecs.open(fn, encoding="UTF-8")
        self.lineNumber = 1
        self.nextCharacter = self.readCharacter()
        self.nextCharacterClass = self.classifyCharacter(self.nextCharacter)
        self.stepCharacter()
        self.nextToken = None
        self.stepTonelToken()
        self.parseTonelClass()
        if not self.matches("end"):
            self.reportTonelError(self.currentToken.lineNumber, "unexpected", repr(self.currentToken.value))
        self.stream.close()
        self.numberOfProcessedFiles += 1
        
    def parseTonelValue(self):
        self.skipTonelSeparators()
        if self.currentCharacter == "":
            return self.newToken("end", "", self.lineNumber)
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
        result =  OrderedDict() #{}
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
        return Token("colon", ":", self.lineNumber)

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
        return Token("binary", value.getvalue(), self.lineNumber)

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
        #print "parseTonelClass()"
        if self.matches("string"):
            self.handler.setClassComment(self.currentToken.value)
            self.stepTonelToken()
        if not self.matches("identifier"):
            self.reportTonelError(self.currentToken.lineNumber, "identifier (class/extension) expected")
        unitType = self.currentToken.value
        if unitType not in [ "Class", "Extension" ]:
            self.reportTonelError(self.currentToken.lineNumber, "identifier (class/extension) expected")
        self.handler.setUnitType(unitType)
        self.stepTonelToken()
        if not self.matches("dictionary"):
            self.reportTonelError(self.currentToken.lineNumber, "missing class attributes")
        self.processAttributes(self.currentToken.value)
        self.stepTonelToken()
        self.parseTonelCategoriesAndMethods()
        
    def processAttributes(self, attributes):
        assert len(attributes) > 0, "empty class attributes"
        for key, value in attributes.items():
            key = key.lower()
            if key == "category":
                self.handler.setClassCategory(value)
            elif key == "name":
                self.handler.setName(value)
            elif key == "superclass":
                self.handler.setSuperclass(value)
            elif key == "instvars":
                self.handler.setInstVars(value)
            elif key == "classinstvars":
                self.handler.setClassInstVars(value)
            elif key == "classvars":
                self.handler.setClassVars(value)
            elif key == "gs_options":
                self.handler.setClassOptions(value)
            elif key == "gs_constraints":
                self.handler.setConstraints(value)
            elif key == "type":
                self.handler.setClassType(value)
            else:
                self.reportTonelError(0, "unknown class attribute", key)
                
    def parseTonelCategoriesAndMethods(self):
        while True:
            if self.matches("dictionary"):
                self.processTonelMethodCategoryDictionary(self.currentToken.value)
                self.stepTonelToken()
                continue
            if self.parseTonelMethod():
                continue
            break

    def parseTonelMethod(self):
        if not self.parseMessagePattern():
            return False 
        if not self.matches("["):       
            self.reportTonelError(self.currentToken.lineNumber, "missing [")
        self.stepToken()
        sequence = self.parseMethodBody()
        if sequence is None:
            self.reportTonelError(self.currentToken.lineNumber, "missing method body")
        if not self.matches("]"):  
            self.parsingError("missing ]")
        self.stepTonelToken() 
        self.handler.addMethodBody(sequence)
        return True
        
    def parseMessagePattern(self):
        #print "parseMessagePattern"
        if not self.matches("identifier"):
            return False
        methodClass = self.currentToken.value
        self.stepToken()
        if self.matches("identifier"):
            methodSide = self.currentToken.value
            self.stepToken()
        else:
            methodSide = "instance"
        if not self.matches("binary_selector", ">>"):
            print self.currentToken
            self.reportTonelError(self.currentToken.lineNumber, ">> expected1")
        self.stepToken()
        if self.matches("identifier"):
            selector = self.currentToken.value
            arguments = []
            self.stepToken()
        elif self.matches("binary_selector"):
            selector = self.currentToken.value
            self.stepToken()
            if self.matches("identifier"):
                arguments = [self.currentToken.value]
            else:
                self.reportTonelError(self.currentToken.lineNumber, "argument identifer expected")
            self.stepToken()
        elif self.matches("keyword"):
            selector = StringIO.StringIO()
            arguments = []
            while self.matches("keyword"):
                selector.write(self.currentToken.value)
                self.stepToken()
                if not self.matches("identifier"):
                    self.reportTonelError(self.currentToken.lineNumber, "argument identifer expected")
                arguments.append(self.currentToken.value)
                self.stepToken()
            selector = selector.getvalue()
        else:
            self.reportTonelError(self.currentToken.lineNumber, "message pattern expected1")
        self.handler.addMethod(selector, arguments, methodSide, methodClass)
        return True

    def parseMethodBody(self):
        pragmas = self.parsePragmas()
        temporaries = self.parseTemporaries()
        sequence = self.parseStatements()
        sequence.temporaries = temporaries
        return sequence

    def parsePragmas(self):
        while self.parsePragma():
            pass

    # no return value yet, should be a PragmaNode
    def parsePragma(self):
        #print "parsePragma()", self.currentToken
        if not self.matches("binary_selector", "<"):
            return
        self.stepToken()
        if self.matches("identifier"):
            "UnaryPragma"
            self.stepToken()
        elif self.matches("keyword"):
            "KeywordPragma"
            while self.matches("keyword"):
                self.stepToken()
                if not self.parsePrimitiveLiteral():
                    self.parsingError("primitive literal expected")
        else:
            self.parsingError("unary or keyword pragma expected")
        if not self.matches("binary_selector", ">"):
            self.parsingError("> expected")
        self.stepToken()
        
    def parseTemporaries(self):
        temporaries = []
        if self.matches("binary_selector", "|"):
            self.stepToken()
            while self.matches("identifier"):
                temporaries.append(VariableNode(self.currentToken.value))
                # BEGIN OF HACK
                self.handler.addTemporary(self.currentToken.value)
                # END OF HACK
                self.stepToken()
            if not self.matches("binary_selector", "|"):
                self.error("identifier or | expected in temporaries")
            self.stepToken()
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
            if self.matches("."):
                self.stepToken()
                statement = self.parseStatement()
            else:
                statement = None
        return aSequenceNode

    def parseAssignment(self):
        if self.matches("identifier"):
            self.nextToken = self.getToken()
            if self.nextToken.matches("assignment"):
                node = AssignmentNode()
                node.variable = VariableNode(self.currentToken.value)
                self.stepToken()  # variable
                self.stepToken()  # assignment
                node.statement = self.parseAssignment()
                if node.statement is None:
                    self.parsingError("assignment must be followed by a statement")
                return node
            else:
                return self.parseCascadeMessage()
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
            self.stepToken()
            node = self.parseUnaryMessageWith(receiver)
            if node is None:
                node = self.parseBinaryMessageWith(receiver)
                if node is None:
                    node = self.parseKeywordMessageWith(receiver)
            if node is None:
                self.parsingError("something wrong in cascade")
            cascadeNode.addMessage(node)
        return cascadeNode

    def parseKeywordMessage(self):
        node = self.parseBinaryMessage()
        if not self.matches("keyword"):
            return node
        return self.parseKeywordMessageWith(node)

    def parseKeywordMessageWith(self, aNode):
        selector = ''
        arguments = []
        while self.matches("keyword"):
            selector = selector + self.currentToken.value
            self.stepToken()
            arguments.append(self.parseBinaryMessage())
        newNode = MessageNode()
        newNode.receiver = aNode
        newNode.selector = selector
        newNode.arguments = arguments
        return newNode

    def parseBinaryMessage(self):
        node = self.parseUnaryMessage()
        self.splitNegativeNumberLiteral()
        while self.matches("binary_selector"):
            newNode = MessageNode()
            newNode.receiver = node
            newNode.selector = self.currentToken.value
            self.stepToken()
            newNode.arguments = [self.parseUnaryMessage()]
            node = newNode
        return node

    def parseBinaryMessageWith(self, aNode):
        self.splitNegativeNumberLiteral()
        if not self.matches("binary_selector"):
            return None
        node = MessageNode()
        node.receiver = aNode
        node.selector = self.currentToken.value
        self.stepToken()
        node.arguments = [self.parseUnaryMessage()]
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
        node.arguments = []
        self.stepToken()
        # BEGIN OF HACK
        self.handler.addUnaryMessageSend(node.selector)
        # END OF HACK
        return node
    
    def splitNegativeNumberLiteral(self):
        if not(self.matches("number") and self.currentToken.value.startswith('-')):
            return
        self.currentToken = self.newToken("binary_selector", "-", self.currentToken.lineNumber)
        assert self.nextToken is None
        self.nextToken = self.newToken(
                "number", 
                self.currentToken.value.lstrip("-"),
                self.currentToken.lineNumber) 
    
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
        node = self.parseCurlyBlock()
        if node is not None:
            return node
        node = self.parseLiteralArray()
        if node is not None:
            return node
        node = self.parseParenthesizedExpression()
        if node is not None:
            return node
        node = self.parseCurlyArray()
        if node is not None:
            return node
        return None

    def parseCurlyArray(self):
        if not self.matches('{'):
            return None
        self.stepToken()
        node = ArrayNode()
        self.parseStatementListInto(node)
        if self.matches('}'):
            self.stepToken()
            return node
        else:
            self.parsingError('"}" expected')
            
    # GS needs to support byte arrays (without comma) and
    # array builder with comma and expressions.
    def parseByteArrayOrArrayBuilder(self, nested = False):
        if self.matches("bytearray"):
            self.stepToken()
            node = self.parsePrimitiveObject()
            isArrayBuilder = (self.matches("binary_selector", ",") or
                              (node is not None and not node.isLiteralValueNode()))

            if isArrayBuilder:
                newNode = ArrayNode()
                newNode.addStatement(node)
                while self.matches("binary_selector", ","):
                    self.stepToken()
                    node = self.parsePrimitiveObject()
                    if node is None:
                        self.parsingError('Missing object after comma in array.')
                    newNode.addStatement(node)
            else:
                newNode = LiteralArrayNode(isForByteArray=True)
                newNode.addElement(node)
                while True:
                    node = self.parseNumberLiteral()
                    if node is None:
                      break
                    newNode.addElement(node)
            if not self.matches("]"):
                print self.scanner.fragment.getSource()
                self.parsingError('Missing ] for #[ array.')
            self.stepToken()
            return newNode
        return None
        
    def parsePrimitiveIdentifier(self):
        if not self.matches("identifier"):
            return None
        node = VariableNode(self.currentToken.value)
        self.stepToken()
        return node

    def parseVariable(self):
        return self.parsePrimitiveIdentifier()

    def parsePrimitiveValueLiteral(self):
        if self.matches("string"):
            node = LiteralValueNode(String(self.currentToken.value))
            self.stepToken()
            return node
        if self.matches("symbol"):
            node = LiteralValueNode(Symbol(self.currentToken.value))
            self.stepToken()
            return node
        if self.matches("character"):
            node = LiteralValueNode(Character(self.currentToken.value))
            self.stepToken()
            return node
        if self.matches("qualified_name"):
            node = LiteralValueNode(String(self.currentToken.value))
            self.stepToken()
            return node
        return None

    def parseNumberLiteral(self):
        if not self.matches("number"):
            return None
        node = LiteralValueNode(Number(self.currentToken.value))
        self.stepToken()
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
        if not self.matches("["):
            return None
        self.stepToken()
        node = BlockNode()
        if self.matches(":"):
            while self.matches(":"):
                self.stepToken()
                variableNode = self.parseVariable()
                #print "block variable", variableNode
                if variableNode is None:
                    self.error("variable expected after colon")
                node.addArgument(variableNode)
            self.splitDoubleBar()            
            if not self.matches("binary_selector","|"):
                self.parsingError('"|" expected after block variable list')
            self.stepToken()
        node.body = self.parseStatements()
        #print self.currentToken
        if not self.matches("]"):
            self.parsingError('"]" expected at the end of a block')
        self.stepToken()
        return node
        
    def splitDoubleBar(self):
        if self.matches("binary_selector","||"):
            self.currentToken = self.newToken("binary_selector", "|", self.currentToken.lineNumber)
            assert self.nextToken is None
            self.nextToken = self.newToken("binary_selector", "|", self.currentToken.lineNumber) 

    def parseCurlyBlock(self):
        if not self.matches("{"):
            return None
        assert self.nextToken is None
        self.nextToken = self.getToken()
        if not self.nextToken.matches(":"):
            return None
        self.stepToken()
        node = BlockNode()
        while self.matches(":"):
            self.stepToken()
            variableNode = self.parseVariable()
            #print "block variable", variableNode
            if variableNode is None:
                self.error("variable expected after colon")
            node.addArgument(variableNode)
        if self.matches("binary_selector","||"):
            self.splitDoubleBar()     
        if not self.matches("binary_selector","|"):
            self.parsingError('"|" expected after block variable list')
        self.stepToken()
        node.body = self.parseStatements()
        #print self.currentToken
        if not self.matches("}"):
            self.parsingError('"}" expected at the end of a curly block')
        self.stepToken()
        return node

    def parseLiteralArray(self, nested = False):
        # Special array types, like #[] must be handled in subclasses.
        if self.matches("array") or (nested and self.matches("(")):
            newNode = LiteralArrayNode(isForByteArray=False)
            self.stepToken()
            node = self.parseLiteralArrayObject()
            while node is not None:
                newNode.addElement(node)
                node = self.parseLiteralArrayObject()
            if not self.matches(")"):
                print self.scanner.fragment.getSource()
                self.parsingError('")" expected')
            self.stepToken()
            return newNode
        node = self.parseByteArrayOrArrayBuilder(nested)
        if node is not None:
            return node
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
        if not self.matches("("):
            return None
        self.stepToken()
        node = self.parseAssignment()
        if not self.matches(")"):
            self.parsingError('")" expected')
        self.stepToken()
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
        self.stepToken()
        assignment = self.parseAssignment()
        if assignment is None:
            self.parsingError('missing statement or expression after ^')
        node.assignment = assignment
        return node


    def parseExpression(self):
        primary = self.parsePrimary()
        expression = ExpressionNode()
        expression.primary = primary
        return expression

    def parsePrimary(self):
        if self.matches("identifier"):
            node = VariableNode(self.currentToken.value)
            self.stepToken()
            return node
        if self.matches("string"):
            node = LiteralNode(self.currentToken.value)
            self.stepToken()
            return node
        return None

    def parseMessage(self):
        if self.matches("identifier"):
            node = MessageNode()
            node.selector = self.currentToken.value
            self.stepToken()
            return node
        self.error("unexpected message token", self.currentToken)

    def parseNestedBlock(self):
        assert self.currentToken.type in [ "[", "bytearray" ]
        self.stepToken()
        while not self.matches("]"):
            assert not self.matches("end")
            # process nested blocks
            if self.currentToken.type in ["[", "bytearray"]:
                self.parseNestedBlock()
            else:
                self.stepToken()
        assert self.matches("]")
        self.stepToken()

    def processTonelMethodCategoryDictionary(self, aDictionary):
        assert len(aDictionary) == 1, "method category dictionary expected to have one entry"
        self.handler.setCurrentMethodCategory(aDictionary["category"])
        
    def stepTonelToken(self):
        if self.nextToken is None:
            self.currentToken = self.parseTonelValue()
        else:
            self.currentToken = self.nextToken
            self.nextToken = None
        
    def readCharacter(self):
        ch = self.stream.read(1)
        # Ignore carriage returns.
        if ch == "\r":
            ch = self.stream.read(1)
            assert ch == "\n", "linefeed expected after carriage return"
        return ch
        
    def stepCharacter(self):
        self.currentCharacter = self.nextCharacter
        self.currentCharacterClass = self.nextCharacterClass
        self.nextCharacter = self.readCharacter()               
        self.nextCharacterClass = self.classifyCharacter(self.nextCharacter)
        
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
        if not 32 <= self.ord(ch) <= 127:
            return "exotic_character"
        self.error("unclassified character", ch, repr(self.ord(ch)))

    def ord(self, ch):
        # support for astral unicode surrogate pairs
        if len(ch) == 1:
            return ord(ch)
        if len(ch) == 2:
            high, low = ch
            return ((ord(high) - 0xD800) * 0x400) + (ord(low) - 0xDC00) + 0x10000
        self.error("cannot decode UTF-8", ch)
        
    def getBasicToken(self):
        self.scanWhite()
        token = self.scanComment()
        if token is not None:
            return token
        token = self.scanEnd()
        if token is not None:
            return token
        token = self.scanAssignment()
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
        self.parsingError("unexpected character " + repr(self.currentCharacter) + " " + hex(self.ord(self.currentCharacter)))
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
            
    def stepToken(self):
        if self.nextToken is None:
            self.currentToken = self.getToken()        
        else:
            self.currentToken = self.nextToken
            self.nextToken = None
        #print "stepToken()", self.currentToken
    
    def newToken(self, type, value, lineNumber):
        return Token(type, value, lineNumber)
        
    def isDigit(self, aCharacter):
        return "0" <= aCharacter <= "9"
        
    def isLetter(self, aCharacter):
        return "a" <= aCharacter <= "z" or "A" <= aCharacter <= "Z" or aCharacter == "_"
        
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
            
    def scanComment(self):
        if self.currentCharacter == "\"":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            self.stepCharacter()
            while self.currentCharacter != "\"":
                if self.currentCharacterClass == "end":
                    self.error("unterminated comment", lineNumber)
                value.write(self.currentCharacter)
                self.stepCharacter()
            self.stepCharacter()
            return self.newToken("comment", value.getvalue(), lineNumber)
        else:
            return None
            
    def scanIdentifier(self):
        if self.currentCharacterClass == "letter":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass in ["letter","digit"]:
                value.write(self.currentCharacter)
                self.stepCharacter()
            value = value.getvalue()
            if value == "_":
                return self.newToken("assignment", value, lineNumber)
            else:
                return self.newToken("identifier", value, lineNumber)
        else:
            return None
            
    def scanIdentifierOrKeyword(self):
        token = self.scanIdentifier()
        if self.currentCharacter == ":" and self.nextCharacter != "=":
            self.stepCharacter()
            return self.newToken("keyword", token.value + ":", self.lineNumber)
        else:
            return token

    def scanNumber(self):
        if not (self.currentCharacterClass == "digit" or
            (self.currentCharacter == "-" and self.nextCharacterClass == "digit")):
            return None
        value = StringIO.StringIO()
        value.write(self.currentCharacter)
        self.stepCharacter()
        while self.currentCharacterClass == "digit":
            value.write(self.currentCharacter)
            self.stepCharacter()
        if self.currentCharacter == "r":
            value.write(self.currentCharacter)
            self.stepCharacter()
            if self.currentCharacterClass not in ["digit", "letter"]:
                self.error("invalid radix number")
            while self.currentCharacterClass in ["digit", "letter"]:
                value.write(self.currentCharacter)
                self.stepCharacter()       
            return self.newToken("number", value.getvalue(), self.lineNumber)
        if self.currentCharacter == "." and self.nextCharacterClass == "digit":
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass == "digit":
                value.write(self.currentCharacter)
                self.stepCharacter()
        if self.currentCharacter in "sp":
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass == "digit":
                value.write(self.currentCharacter)
                self.stepCharacter()
        return self.newToken("number", value.getvalue(), self.lineNumber)
            
    def scanEnd(self):
        if self.currentCharacter == "":
            return self.newToken("end", "", self.lineNumber)
        else:
            return None

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
            return self.newToken("string",value.getvalue(), self.lineNumber)
        else:
            return None
            
    def scanCharacter(self):
        if self.currentCharacter == "$":
            self.stepCharacter()
            if self.currentCharacterClass == "end":
                self.error("missing character after dollar")
            token = self.newToken("character", self.currentCharacter, self.lineNumber)
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
                return self.newToken("array", "#(", self.lineNumber)
            if self.currentCharacter == "[":
                self.stepCharacter()
                return self.newToken("bytearray", "#[", self.lineNumber)
            if self.currentCharacter == "{":
                self.stepCharacter()
                self.scanWhite()
                identifier = self.scanIdentifier()
                assert identifier is not None
                self.scanWhite()
                if self.currentCharacter != "}":
                    self.error("incomplete qualified reference literal")
                self.stepCharacter()
                return self.newToken("qualified_name", identifier.value, self.lineNumber)
            if self.currentCharacterClass == "letter":
                value = StringIO.StringIO()
                value.write(self.currentCharacter)
                self.stepCharacter()
                while self.currentCharacterClass in ["letter", "digit", ":"]:
                    value.write(self.currentCharacter)
                    self.stepCharacter()
                return self.newToken("symbol", value.getvalue(), self.lineNumber)
            if self.currentCharacter == "'":
                token = self.scanString()
                if token is not None:
                    return self.newToken("symbol", token.value, self.lineNumber)
            token = self.scanBinarySelector()
            if token is None:
                self.error("incomplete literal after hash")
            return self.newToken("symbol", token.value, self.lineNumber)
        else:
            return None

    def scanComment(self):
        if self.currentCharacter == "\"":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            self.stepCharacter()
            while self.currentCharacter != "\"":
                if self.currentCharacterClass == "end":
                    self.error("unterminated comment", lineNumber)
                value.write(self.currentCharacter)
                self.stepCharacter()
            self.stepCharacter()
            return self.newToken("comment", value.getvalue(), lineNumber)
        else:
            return None

    def scanBinarySelector(self):
        if self.currentCharacter == "-":
            lineNumber = self.lineNumber
            self.stepCharacter()
            return self.newToken("binary_selector", "-", lineNumber)
        if self.currentCharacterClass == "special_character":
            lineNumber = self.lineNumber
            value = StringIO.StringIO()
            value.write(self.currentCharacter)
            self.stepCharacter()
            while self.currentCharacterClass == "special_character":
                value.write(self.currentCharacter)
                self.stepCharacter()
            return self.newToken("binary_selector", value.getvalue(), lineNumber)
        else:
            return None

    def scanSimple(self):
        if self.currentCharacter in "^.()[]{};":
            token = self.newToken(self.currentCharacter, self.currentCharacter, self.lineNumber)
            self.stepCharacter()
            return token
        return None

    def scanAssignment(self):
        if self.currentCharacter == "_" and self.nextCharacterClass != "letter":
            self.stepCharacter()
            return self.newToken("assignment", "_", self.lineNumber)
        if self.currentCharacter == ":":
            self.stepCharacter()
            if self.currentCharacter == "=":
                self.stepCharacter()
                return self.newToken("assignment", ":=", self.lineNumber)
            else:
                return self.newToken(":", ":", self.lineNumber)
        return None

class Node:
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

    def isLiteralArrayNode(self):
        return False

    def isBlockNode(self):
        return True

    def isReturnNode(self):
        return True

    def printCode(self):
        stream = StringIO.StringIO()
        self.writeCodeOn(stream)
        print stream.getvalue()

    def evaluate(self, aContext):
        print self.__class__
        self.error("Node>>evaluate:")

class ReturnNode(Node):
    def __init__(self):
        self.assignment = None

    def isReturnNode(self):
        return True
        
    def getFirstStatement(self):
        return self.assignment.getFirstStatement()

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
        
    def getFirstStatement(self):
        return self.statements[0].getFirstStatement()

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
        self.elements = []

    def isArrayNode(self):
        return True

    def addStatement(self, aNode):
        self.elements.append(aNode)
        
    def getFirstStatement(self):
        return None

class ExpressionNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.primary = None
        
    def printStructure(self, indent=0):
        print self.__class__.__name__
        
    def getFirstStatement(self):
        return None
        
    def evaluate(self, aContext):
        if self.primary is None:
            return None
        self.notYetImplemented("ExpressionNode>>evaluate")

class PrimaryNode(Node):
    def printStructure(self, indent=0):
        print self.__class__.__name__

class MessageNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.receiver = None
        self.selector = None
        self.arguments = None

    def printStructure(self, indent=0):
        print self.__class__.__name__
        print "  receiver:"
        self.receiver.printStructure(indent + 1)
        self.indentedPrint(indent + 1 , "  selector:", self.selector)

    def isMessageNode(self):
        return True
        
    def getFirstStatement(self):
        return self

    def evaluate(self, aContext):
        evaluatedReceiver = self.receiver.evaluate(aContext)
        selector = self.selector
        evaluatedArguments = map(lambda each: each.evaluate(aContext), self.arguments)
        return aContext.execute(evaluatedReceiver, selector, evaluatedArguments)

class CascadeNode(Node):
    def __init__(self):
        self.messages = []

    def isCascadeNode(self):
        return True

    def addMessage(self, aMessageNode):
        self.messages.append(aMessageNode)
        
    def getFirstStatement(self):
        return self.messages[0]

class AssignmentNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.variable = None
        self.statement = None
        
    def getFirstStatement(self):
        return self.statement.getFirstStatement()
        
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

    def evaluate(self, aContext):
        if self.name == "nil":
            return None
        if self.name == "false":
            return False
        if self.name == "true":
            return True
        return self.name
        
    def getFirstStatement(self):
        return None

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
        
    def getFirstStatement(self):
        return None

class LiteralArrayNode(Node):
    def __init__(self, isForByteArray):
        Node.__init__(self)
        self.elements = []
        self.isForByteArray = isForByteArray

    def isLiteralArrayNode(self):
        return True

    def addElement(self, aValue):
        self.elements.append(aValue)

    def evaluate(self, aContext):
        return map(lambda each: each.evaluate(aContext), self.elements)
        
    def getFirstStatement(self):
        return None

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

    def evaluate(self, aContext):
        return "some block"

    def getFirstStatement(self):
        return None
        
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

    def notYetImplemented(self, aString=""):
        self.error("not yet implemented", aString)

    def subclassResponsibility(self, aString=""):
        self.error("subclassResponsibility", aString);

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
        self.value = aValue

    def __eq__(self, anObject):
        return self.__class__ == anObject.__class__ and self.value == anObject.value

class Character(Magnitude):
    pass

class String(Magnitude):
    def printOn(self, aStream):
        return repr(self.value)

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

        
if __name__ == "__main__":  
    parser = Parser()
    parser.handler = BasicHandler()
    parser.processCommandLine()
    
           
        



