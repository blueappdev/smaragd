import sys

class ProgressBar(object):
    def __init__(self, maxValue):
        self.maxValue = maxValue
        self.update(0)

    def update(self, currentValue):
        sys.stderr.write('%s of %s\r' % (currentValue, self.maxValue))

    def finish(self):
        sys.stderr.write('\n')
