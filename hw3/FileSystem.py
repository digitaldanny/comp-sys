import MemoryInterface, AbsolutePathNameLayer

def Initialize_My_FileSystem():
    MemoryInterface.Initialize_My_FileSystem()
    AbsolutePathNameLayer.AbsolutePathNameLayer().new_entry('/', 1)

#HANDLE TO ABSOLUTE PATH NAME LAYER
interface = AbsolutePathNameLayer.AbsolutePathNameLayer()

class FileSystemOperations():

    #MAKES NEW DIRECTORY
    def mkdir(self, path):
        interface.new_entry(path, 1)

    #CREATE FILE
    def create(self, path):
        interface.new_entry(path, 0)
        

    #WRITE TO FILE
    def write(self, path, data, offset=0):
        interface.write(path, offset, data)
      

    #READ
    def read(self, path, offset=0, size=-1):
        read_buffer = interface.read(path, offset, size)
        if read_buffer != -1: print(path + " : " + read_buffer)

    
    #DELETE
    def rm(self, path):
        interface.unlink(path)


    #MOVING FILE
    def mv(self, old_path, new_path):
        interface.mv(old_path, new_path)


    #CHECK STATUS
    def status(self):
        print(MemoryInterface.status())

def printDivider():
    print("+====="*20 + "+")

def announce(msg):
    printDivider()
    print(msg)
    printDivider()

if __name__ == '__main__':
    #DO NOT MODIFY THIS
    Initialize_My_FileSystem()
    fs = FileSystemOperations()
    #announce("INIT MEMORY")
    #fs.status()
    
    # FILE WRITE/READ TEST ----------------------------------------------------
    msg = "Hello world!"
    
    announce("FILE FAILED CREATION..")
    fs.create('/A/B/file.txt')
    
    announce("DIRECTORY CREATED..")
    fs.mkdir('/A')
    fs.mkdir('/A/B')
    
    announce("FILE CREATION SUCCESSFUL..")
    fs.create('/A/B/file.txt')
    
    announce("WRITE COMPLETE..")
    fs.write('/A/B/file.txt', msg, offset=0)
    fs.status()
    
    # compare the message read back from memory with the value written out
    readData = fs.read('/A/B/file.txt', 0, len(msg))
    
    # SYMBOLIC LINK TESTS -----------------------------------------------------
    announce("REMOVING FILE BY UNLINKING")
    fs.rm('/A/B/file.txt')
    fs.status()
    
    '''Examples:
    my_object.mkdir("/A")
    my_object.status()
    my_object.mkdir("/B")
    my_object.status()
    my_object.create("/A/1.txt"), as A is already there we can crete file in A
    my_object.status()
    my_object.write("A/1.txt", "POCSD", offset), as 1.txt is already created now, we can write to it.
    my_object.status()
    my_object.mv("/A/1.txt", "/B")
    my_object.status()
    my_object.rm("A/1.txt")
    my_object.status()
    '''
