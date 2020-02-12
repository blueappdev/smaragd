#
# handlers.py
#
class Handler:
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
        print name
        
class DebugHandler:
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
        

