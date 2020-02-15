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
    | a |
    a := 1.
    a _ 2.
]

TestClass1 class >> testHyphen [
    | uhu als |
    uhu := 1 * -5.
    uhu := 1 - 5.
    uhu := 1 - 5.
    uhu := -5.
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
    | a |
    a := [:value | value.name == nil ]
]

TestClass1 >> testCurlyBlock [
    | a |
    a := {:value | value.name == nil }
]

TestClass1 >> testBlockWithoutSpaceBeforeTemporaries [
    "No space between the two vertical bars ||. 
    The first vertical is a separate token."
    
    ^[:value|| result | result := value ]
]

TestClass1 >> testPragma [
    <someCommand1: 'test' value: #'abc'>
    | a b c |
    a := 0
]

TestClass1 >> testPoorlyNamedTemporaries [
    | a aValue anInteger someValues temp |
    ^nil
]

