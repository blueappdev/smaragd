#!/usr/bin/env python

#
# stest.py
#

import unittest
from slib import Testing
from scmd import *

class ScannerTest(Testing.TestCase):
    def scannerClass(self):
        return Scanner

    def scan(self, aString, *expectedValues):
        self.tokens = self.scannerClass()(Fragment(aString)).allBasicTokens()
        for i in range(min(len(self.tokens), len(expectedValues))):
            tupel = expectedValues[i]
            if type(tupel) == str:
                tupel = (tupel,None)
            expectedType = tupel[0]
            expectedValue = tupel[1]
            actual = self.tokens[i]
            if not actual.matches(expectedType, expectedValue):
                print self.tokens
                print expectedValues
                self.assertTrue(actual.matches(expectedType, expectedValue))
        assert len(self.tokens) == len(expectedValues)

    def assertTokenMatch(self, index, expectedType, expectedValue = None):
        assert (self.tokens[index].matches(expectedType, expectedValue))

    def testArrayLiteral(self):
        self.scan("#(123)", 
            ("array", "#("),
            ("number", "123"),
            ")")

    def testArrayLiteralWithSeparators(self):
        self.scan("#\n \n\t(456)",
            ("array", "#("),
            ("number", "456"),
            (")"))

    def testNestedArrayLiteral(self):
        self.scan("#(1 #(2 b) (3 c) a)", 
            ("array", "#("),
            ("number", '1'),
            ("array", "#("),
            ("number", '2'),
            ("identifier", "b"),
            (")"),
            ("("),
            ("number", "3"),
            ("identifier", "c"),
            (")"),
            ("identifier", 'a'),
            ")")

    """def testArrayLiteral(self):
        self.scan("#[0 100 255]", 
            ("bytearray", "#["),
            ("number", "0"),
            ("number", "100"),
            ("number", "255"),
            "]")
    """
    def testMinus(self):
        self.scan("- 1", 
            ["binary_selector", "-"],
            ["number", "1"])
        self.scan("-1", ["number", "-1"])
        self.scan("1 - 1", "number", "binary_selector", "number")
        # special case
        self.scan("1-1", ["number", "1"], ["number", "-1"])    
        # degenerate case
        self.scan("1--1", ["number", "1"], ["binary_selector", "-"], ["number", "-1"])   

#    def testMinusVW(self):
#        self.scan("1-1", "1", "-1")
#        #self.scan("1--1",3,"1","--","1")

    def testExoticCharacters(self):
        exotic = "\x24"
        self.scan("'" + exotic + "'", ("string", exotic))
        self.scan("\"" + exotic + "\"", ("comment", exotic))
        

class ST80ScannerTest(ScannerTest):
    def scannerClass(self):
        return ST80Scanner

    def testSingleUnderscore(self):
        self.scan("_", ("assignment", "_"))

class VWScannerTest(ScannerTest):
    def scannerClass(self):
        return VWScanner

    def testSingleUnderscore(self):
        self.scan("_", ("identifier", "_"))

    def testQualifiedReference(self):
        self.scan("#{Core.Object}", ("qualified_name", "Core.Object"))

class GSScannerTest(ScannerTest):
    def scannerClass(self):
        return GSScanner

    def testIdentifier(self):
        self.scan("Transcript", ("identifier", "Transcript"))

    def testIdentifierWithUnderscore(self):
        self.scan("My_Address", ("identifier", "My_Address"))

    def testSingleUnderscore(self):
        self.scan("_", ("identifier", "_"))

    def testString(self):
        self.scan("'Hello World'", ("string", "Hello World"))

    def testSymbol(self):
        self.scan("#uhu", ["symbol", "uhu"])

    def testQuotedSymbol(self):
        self.scan("#'uhu'", ["symbol", "uhu"])
        self.scan("#'tailor''s'", ["symbol", "tailor's"])
        self.scan("#'333'", ["symbol", "333"])
        self.scan("#'AAA-BBB-CCC'", ["symbol", "AAA-BBB-CCC"])

    def testSymbolWithSingleColon(self):
        self.scan("#uhu:", ["symbol", "uhu:"])

    def testSymbolWithMultipleColons(self):
        self.scan("#one:two:three:", ["symbol", "one:two:three:"])

    def testAssignment(self):
        self.scan(":=", ["assignment", ":="])

    def testIdentifierImmediatelyFollowedByAssignment(self):
        self.scan("id:=", 
            ["identifier", "id"],
            ["assignment", ":="])

    def testSymbolImmediatelyFollowedByAssignment(self):
        self.scan("#uhu:=", 
            ["symbol", "uhu:"],
            ["binary_selector", "="])

    def testNumber(self):
        self.scan("123", ["number", "123"])
        self.scan("-123", ["number", "-123"])
        # The handling of --123 is different in Smalltalk-80, VW, annd ANSI.
        self.scan("--123", 
            ["binary_selector", "-"],
            ["number", "-123"])

class ParserTest(Testing.TestCase):
    def parserClass(self):
        return Parser

    def newParser(self, aString):
        return self.parserClass()(Fragment(aString))

    def parse(self, aString):
        parser = self.newParser(aString)
        result = parser.process()
        assert parser.currentToken.matches("end"), "end of input expected"
        return result

    def parseSingleStatement(self, aString):
        node = self.parse(aString)
        assert node.isSequenceNode(), "sequence node expected"
        assert len(node.statements) == 1, "one statement expected"
        return node.statements[0]

    def parseSimpleObject(self, aString):
        node = self.parseSingleStatement(aString)
        self.assertFalse(node.isMessageNode())
        return node

    def testIdentifier(self):
        node = self.parseSimpleObject("Transcript")
        assert node.isVariableNode(), "variable node expected"
        assert node.name == "Transcript"

    def testParenthesizedExpression(self):
        node = self.parseSimpleObject("(Transcript)")
        assert node.isVariableNode(), "variable node expected"
        assert node.name == "Transcript"

    def testString(self):
        node = self.parseSimpleObject("'uhu'")
        assert node.isLiteralValueNode(), "literal value node expected"
        assert node.value == String("uhu")
        node = self.parseSimpleObject("'uhu''s'")
        assert node.isLiteralValueNode(), "literal value node expected"
        assert node.value == String("uhu's")

    def testSymbol(self):
        node = self.parseSimpleObject("#uhu")
        assert node.isLiteralValueNode(), "literal value node expected"
        assert node.value == Symbol("uhu")

    def testInteger(self):
        node = self.parseSimpleObject("123")
        assert node.isLiteralValueNode(), "literal value node expected"
        assert node.value == Number("123")

    def testArray(self):
        node = self.parseSimpleObject("#(999 #symbol 'string' identifier #(1 2))")
        self.assertTrue(node.isLiteralArrayNode())
        self.assertFalse(node.isForByteArray)
        self.assertEqual(node.elements[0].value, Number("999"))
        self.assertEqual(node.elements[1].value, Symbol("symbol"))
        self.assertEqual(node.elements[2].value, String("string"))
        self.assertEqual(node.elements[3].value, Symbol("identifier"))

    def testBlock(self):
        sequenceNode = self.parse("[:aa :bb | ala]")
        assert sequenceNode.isSequenceNode(), "sequence node expected"
        assert len(sequenceNode.statements) == 1, "one statement expected"
        blockNode = sequenceNode.statements[0]
        assert blockNode.isBlockNode(), "block node expected"
        assert blockNode.arguments[0].name == "aa"
        assert blockNode.arguments[1].name == "bb"
        statement = blockNode.body.statements[0]
        self.assertTrue(statement.isVariableNode())
        self.assertEqual(statement.name, "ala")

    def testSingleUnaryMessage(self):
        node = self.parseSingleStatement("'hello' size")
        # print node

    def testTwoUnaryMessage(self):
        node = self.parseSingleStatement("'hello' size printString")
        # print node

    def testVariableTarget(self):
        node = self.parseSingleStatement("Transcript cr")

    def testKeywordMessage(self):
        node = self.parseSingleStatement("Transcript show: 'hello'")
        self.assertTrue(node.isMessageNode())
        self.assertTrue(node.receiver.name == "Transcript")
        self.assertTrue(node.selector == "show:")
        self.assertTrue(node.arguments[0].value == String('hello'))

    def testBinaryMessage(self):
        node = self.parseSingleStatement("'Hello',' World'")
        self.assertTrue(node.isMessageNode())
        self.assertTrue(node.receiver.value == String("Hello"))
        self.assertTrue(node.selector == ",")
        self.assertTrue(node.arguments[0].value == String(' World'))

    def testCascade(self):
        node = self.parseSingleStatement("Transcript tab; cr")

    def testReturnStatement(self):
        node = self.parseSingleStatement("^55")
        self.assertTrue(node.isReturnNode())

    def testMultipleReturnStatement(self):
        node = self.parse("^55. 3")
        assert node.isSequenceNode(), "sequence node expected"
        pass

    def testMultipleStatements(self):
        sequenceNode = self.parse("a := 4. b := 5.")
        assert sequenceNode.isSequenceNode(), "sequence node expected"

class VWParserTest(ParserTest):
    def parserClass(self):
        return VWParser

    def testIdentifier(self):
        node = self.parseSingleStatement("Object")
        self.assertTrue(node.isVariableNode())
        self.assertTrue(node.name == "Object")

    def testByteArray(self):
        node = self.parseSimpleObject("#[0 100 255]")
        self.assertTrue(node.isLiteralArrayNode())
        self.assertTrue(node.isForByteArray)
        self.assertEqual(node.elements[0].value, Number("0"))
        self.assertEqual(node.elements[1].value, Number("100"))
        self.assertEqual(node.elements[2].value, Number("255"))

    #def testQualified(self):
    #    node = self.parseSingleStatement("#{Core.Object}")
    #    self.assertTrue(node.isMessageNode())
    #    self.assertTrue(node.receiver.value == String("Hello"))
    #    self.assertTrue(node.selector == ",")
    #    self.assertTrue(node.arguments[0].value == String(' World'))

class GSParserTest(ParserTest):
    def parserClass(self):
        return GSParser

    def testCurlyArray(self):
        node = self.parseSimpleObject("{0 . 100 . 255}")
        self.assertTrue(node.isArrayNode())
        self.assertEqual(node.elements[0].value, Number("0"))
        self.assertEqual(node.elements[1].value, Number("100"))
        self.assertEqual(node.elements[2].value, Number("255"))

    # GS parser must support byte array #[ 1 2 3] and
    # comma separated ArrayBuilder #[ expression , expression ]
    def testByteArray(self):
        node = self.parseSimpleObject("#[0 100 255]")
        self.assertTrue(node.isLiteralArrayNode())
        self.assertTrue(node.isForByteArray)
        self.assertEqual(node.elements[0].value, Number("0"))
        self.assertEqual(node.elements[1].value, Number("100"))
        self.assertEqual(node.elements[2].value, Number("255"))

    def testArrayBuilder(self):
        node = self.parseSimpleObject("#[0, 100, 255]")
        self.assertTrue(node.isArrayNode())
        self.assertEqual(node.elements[0].value, Number("0"))
        self.assertEqual(node.elements[1].value, Number("100"))
        self.assertEqual(node.elements[2].value, Number("255"))




if __name__ == '__main__':
    unittest.main()
