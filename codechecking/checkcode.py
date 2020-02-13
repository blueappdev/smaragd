import lib.parsing

class CodeCheckingHandler(lib.parsing.Handler):
    def addTemporary(self, name):
        print name
        
if __name__ == "__main__":  
    parser = lib.parsing.Parser()
    parser.handler = CodeCheckingHandler()
    parser.processCommandLine()
    
           
        



