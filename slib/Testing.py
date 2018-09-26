#
# Testing.py
#

import unittest

class TestCase(unittest.TestCase):
    def assertEqual(self, actual, expected):
        if actual == expected:
            return 
        print "actual   =", actual
        print "expected =", expected
        unittest.TestCase.assertEqual(actual, expected)
    
