

def getTest(version):
    name = version
    
    def simple():
        return name
        
    return simple
    
test_func = getTest("hello")
test_func2 = getTest("other")

print test_func()        
print test_func2()        
print test_func()        
