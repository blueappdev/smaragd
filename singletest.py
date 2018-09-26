#!/usr/bin/env python
#
# singletest.py
#

from scmd import *

parser = GSParser(Fragment("{ 2 * 8 . 7}"))
statement = parser.process()
print statement

