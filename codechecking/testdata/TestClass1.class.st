"This is a class comment."

Class {
    #name : 'TestClass1',
    #superclass : 'Object',
    #instVars : [
        'prompt',
        'labels',
        'values',
        'lines'
    ],
    #category : 'Test Category'
}

{ #category : 'protocol 1' }
TestClass1 >> testMethod1: anArray [
    | a1 a2  |
    uhu := 1.
    ^ self
        prompt: nil
        labels: anArray
        values: anArray
        lines: #()
]

TestClass1 >> testExoticVariableNames [
    | a a_ _a a_a |
    ^nil
]

TestClass1 >> testAssignment [
    "Test both ANSI assignment and Smalltalk-80 assignment."
    | a |
    a := 1.
    a _ 2.
]

TestClass1 class >> testHyphenWithSpaces [
    | a |
    a := 1 * -4.
    a := 2 - 5.
    a := -6.
]

TestClass1 class >> testMinusWithoutSpaces [
    "The minus in '2-5' is a separate token (binary_selector) 
    and not part of a number literal of -5."

    | a |
    a := 1*-4.
    a := 2-5.
    a := -6.
]

TestClass1 class >> testNumberLiterals [
    | a |
    a := 1.
    a := 111.
    a := 3.14.
    a := 10s.
    a := 10.8s3.
    a := 5.0p.
    a := 16rFFFF.
    a := 16r1000.
    a := 16r3444.
]

TestClass1 >> testBlock [
    ^[:value | value.name == nil ]
]

TestClass1 >> testCurlyBlock [
    ^{:value | value.name == nil }
]

TestClass1 >> testBlockWithoutSpaceBeforeTemporaries [
    "No space between the double vertical bar ||. 
    The first vertical is a separate token."
    
    ^[:value || result | result := value ]
]

TestClass1 >> testPragma [
    <someCommand1: 'test' value: #'abc'>
    | a b c |
    a := 0
]

TestClass1 >> testPoorlyNamedTemporaries [
    | e aValue anInteger someValues tempValue |
    ^nil
]

