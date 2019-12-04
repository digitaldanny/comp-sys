# SKELETON CODE FOR CLIENT STUB HW4
import xmlrpclib, config, pickle, math

N       = 4     # number of servers running RAID-5
port    = 8000  # starting port number to initialize proxies
PREV 	= 'P'
NEXT 	= 'N'

'''
SUMMARY: client_stub
This layer maps from virtual inode numbers / block numbers to physical inode
numbers and block numbers on the individual servers.
'''
class client_stub():

    '''
    SUMMARY: __init__
    Initialize proxies, etc..
    
    NOTE:
    This function initially claims ~TOTAL_NO_OF_BLOCKS/N parity blocks. If
    the number is not a multiple of N, claim enough blocks until it is.
    '''
    def __init__(self):
        
        # load configuration file properties
        self.virtual_block_size = config.TOTAL_NO_OF_BLOCKS

        # proxies to the servers
        self.proxy = [None for i in range(N)]
        for i in range(N):
            proxyName = "http://localhost:" + str(port + i) + "/"
            self.proxy[i] = xmlrpclib.ServerProxy(proxyName)
        
        # points to the next server to request a data block from
        # (starts at the far end because parity_blocks claims using
        # __prev function).
        self.data_blk_ptr = N-1

        # claim the first NUM_BLOCKS/N virtual blocks to use as parity blocks
        self.block_claim_dir = PREV
	self.block_claim_dir_old = PREV
        self.num_parity_blocks = int(math.ceil(config.TOTAL_NO_OF_BLOCKS))

        # if the number of parity blocks is not a multiple of N, continue incrementing
        # until it is.
        while (self.num_parity_blocks % N > 0):
            self.num_parity_blocks += 1

        self.parity_blocks = [None for i in range(self.num_parity_blocks)]
        
        # changed in the initialize function
        self.first_data_block_num = 0 

        # create an (N-1) x (N) matrix to map parity indexes with
        r = N-1	# remainders
        s = N	# number of servers
        self.offset_table = [[None for i in range(s)] for j in range(r)]

    # initialize the servers
    def Initialize(self):
        try:
            # initialize connection to the servers
            for i in range(N):
                self.proxy[i].Initialize()
				
        # initialize the offset table (i'm very sorry this is so ugly)
            count = 0
            for r in range(N-1): 
                for s in range(N):
                    self.offset_table[r][s] = int(math.floor(count/(N-1)))
                    count += 1
				
            # claim the parity blocks and switch the direction of block claiming
            for i in range(self.num_parity_blocks):
                self.parity_blocks[i] = self.get_valid_data_block()
        
            # switch block claim direction
            self.block_claim_dir = NEXT
	    

            # assuming the server has not crashed yet, the next block will be
            # one higher than the last claimed parity block. This should be a
            # physical data block.
            (dummy, self.first_data_block_num) = self.__translate_virtual_to_physical_block(self.parity_blocks[-1] + 1)
            print("EXPECTED FIRST DATA BLOCK: " + str(self.first_data_block_num))
			
            print("NUMBER OF PARITY BLOCKS CLAIMED: " + str(self.num_parity_blocks))
        
        except Exception as err :
            # print error message
            print "**ERROR CONNECTING TO SERVER**: " + str(err.message)
            print "ARGS: " + str(err.args)
            #quit()
    
    # requests servers to shut down
    def kill_all(self):
        for i in range(N):
            self.proxy[i].kill()

    '''
    SUMMARY: RPC wrapper functions
    These functions are wrappers to the client side of the remote file system. They
    serialize all requests, send to the server, and deserialize responses. If the
    server fails at some point, these functions will return -1.
    '''
    def status(self, server):
        try:
            rx = ''
            rx = self.proxy[server].status()
            return pickle.loads(rx)
        except Exception:
            print "ERROR (status): Server failure.."
            return -1  

    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    #                            BLOCK FUNCTIONS
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
        
    '''
    SUMMARY: get_data_block
    Return the contents of a data block on the appropriate server.
    
    NOTE:
    This function handles if the requested server of the virtual block number
    has a failure by reconstructing the data using the blocks from other servers.
    '''
    def get_data_block(self, virtual_block_number):
        try:
            (serverNum,physicalBlock) = self.__translate_virtual_to_physical_block(virtual_block_number)
	    print("Fetching Block " + str(physicalBlock) + " from server " + str(serverNum))
            serialMessage = pickle.dumps(physicalBlock)
            p = self.proxy[serverNum]
            rx = p.get_data_block(serialMessage)
            (data, state, decay) = pickle.loads(rx)  
            # check if the data is valid, or if it has to be reconstructed before returning..
            if ((state == True) and (decay == False)):
                # data is good..
                return data
            else:
                # data is bad.. reconstruct the block using all other blocks
		if(decay == True): print("Data block decay failure.. reconstructing data")
                else: print("Server  " + str(serverNum) + " failure detected.. reconstructing data")
            	
                serverNumList = [None for i in range(N-2)]
                pBlockNumList = [None for i in range(N-2)]
                
		#read parity block and remaining data blocks
		# read back the current parity block contents (2. SECOND READ)
                vParityNum = self.__pblock_number_to_vparity_number(physicalBlock, serverNum)	# virtual parity block number
                (serverNumParity, physical_parity_block) = self.__translate_virtual_to_physical_block(vParityNum) # find the physical block number and server to read/write
                proxyParity = self.proxy[serverNumParity]							# find server to read/write parity data from
                xorData = self.get_parity_block(serverNumParity, physical_parity_block)

		parityNum = N-1-serverNumParity	#0-3 for repetition

		#find the rows which data falls on and server associated with it
		listCount = 0
            	for r in range(N-1): 
			for s in range(N):
				if((self.offset_table[r][s] == parityNum)and(s != serverNum)):
					pBlockNumList[listCount] = int(r + 3*(math.floor((physical_parity_block-12)/N)) + self.first_data_block_num)
					serverNumList[listCount] = s
					listCount += 1

		#xor data from server and block numbers, since we use parity for the first xor we only need to read N-2 data blocks
		for j in range(N-2):
			print("Fetching Block " + str(pBlockNumList[j]) + " from server " + str(serverNumList[j]))
			#read from each block and server
			tempSerialMessage = pickle.dumps(pBlockNumList[j])
            		tempP = self.proxy[serverNumList[j]]
            		temprx = tempP.get_data_block(tempSerialMessage)
            		(tempData, state, tempdecay) = pickle.loads(temprx)
			xorData = self.__xor(tempData,xorData)
		passfail = True
		#for k in range(len(xorData)):
			#if(xorData[k] != data[k]): passfail = False
		#if(passfail): 	print("DATA RECONSTRUCTION SUCCESS!!!")
		#else:		print("DATA RECONSTRUCTION FAILED!!!")
		if(decay == True):
			print("Sending data back to server " + str(serverNum) + " in block " + str(physicalBlock))
			# update the data block with new data (3. SECOND WRITE)
                	serialBlockNum = pickle.dumps(physicalBlock)
                	serialBlockData = pickle.dumps(xorData)
                	rx = p.update_data_block(serialBlockNum, serialBlockData)

		return xorData
		#if
                # if yes, rebuild using the servers/physical block numbers the parity block number maps to
                # if no, find the other blocks and the parity block to compare for rebuilding
                '''
                if virtual_block_number in self.parity_blocks:
                        (serverNumList, pBlockNumList) = self.__vparity_number_to_pblock_list(virtual_block_number)
                else:
                        serverNumList = test #FINISH THIS LATER
                '''
                '''        
                # XOR to find the original block
                originalBlockData = '\x00'
                for i in range(len(serverNumList)):
                    server 		= serverNumList[i] # next server/address
                    blockNum 	= pBlockNumList[i] # next server/address
                    
                    p = self.proxy[server]                  # get data from the server
                    serialBlockNum = pickle.dumps(blockNum) # get data from the server
                    rx = p.get_data_block(serialBlockNum)   # get data from the server
                    (data,state) = pickle.loads(rx)			# get data from the server	

                    originalBlockData = self.__xor(originalBlockData, data)
                '''    
                return data
        except Exception:
            print "ERROR (get_data_block): Server failure.."
            return -1

    '''
    SUMMARY: get_parity_block
    Return the contents of a parity block on the appropriate server.
    
    NOTE:
    This function handles if the requested server of the physical parity number
    has a failure by reconstructing the parity using the blocks from other servers.
    '''
    def get_parity_block(self, serverNumParity, physical_parity_block):
	try:
		#read all data blocks
		print("Fetching Parity Block " + str(physical_parity_block) + " from server " + str(serverNumParity))
		serialMessage = pickle.dumps(physical_parity_block)
		p = self.proxy[serverNumParity]
		rx = p.get_data_block(serialMessage)
		(data, state, decay) = pickle.loads(rx)
		if((state == False) or (decay == True)):
			# data is bad.. reconstruct the block using all other blocks
			if(decay): print("Parity block data decay failure.. reconstructing parity data")
			else: print("Server " + str(serverNumParity) + " failure detected.. reconstructing parity data")

			serverNumList = [None for i in range(N-1)]
		        pBlockNumList = [None for i in range(N-1)]
			parityNum = N-1-serverNumParity	#0-3 for repetition

			#find the rows which data falls on and server associated with it
			listCount = 0
		    	for r in range(N-1): 
				for s in range(N):
					if(self.offset_table[r][s] == parityNum):
						pBlockNumList[listCount] = int(r + 3*(math.floor((physical_parity_block-12)/N)) + self.first_data_block_num)
						serverNumList[listCount] = s
						listCount += 1

			#xor data from server and block numbers
			parityData = ['\x00' for i in range(config.BLOCK_SIZE)]
			for j in range(N-1):
				print("Fetching Block " + str(pBlockNumList[j]) + " from server " + str(serverNumList[j]))
				#read from each block and server
				tempSerialMessage = pickle.dumps(pBlockNumList[j])
		    		tempP = self.proxy[serverNumList[j]]
		    		temprx = tempP.get_data_block(tempSerialMessage)
		    		(tempData, state, tempdecay) = pickle.loads(temprx)
				parityData = self.__xor(tempData,parityData)
			passfail = True
			#for k in range(len(parityData)):
				#if(parityData[k] != data[k]): passfail = False
			#if(passfail): 	print("PARITY RECONSTRUCTION SUCCESS!!!")
			#else:		print("PARITY RECONSTRUCTION FAILED!!!")
			
			if(decay):
				print("Sending parity data back to server " + str(serverNumParity) + " in block " + str(physical_parity_block))
				# update the data block with new data (3. SECOND WRITE)
                		serialBlockNum = pickle.dumps(physical_parity_block)
                		serialBlockData = pickle.dumps(parityData)
                		rx = p.update_data_block(serialBlockNum, serialBlockData)
			return parityData

		return data
	except Exception:
            print "ERROR (get_parity_block): Server failure.."
            return -1
    '''
    SUMMARY: get_valid_data_block
    Return the next available virtual block number by incrementing the target
    proxy to request a block from. After requesting a block from each server, 
    the pointer will wrap back to 0.
    '''
    def get_valid_data_block(self):
	try:
	    if(self.block_claim_dir != self.block_claim_dir_old): self.data_blk_ptr = 0
            # Retrieve the physical block
            p = self.proxy[self.data_blk_ptr]
            rx = p.get_valid_data_block()
            (blockNum,state) = pickle.loads(rx)
	    print("Retrieved free data block " + str(blockNum) + " from server " + str(self.data_blk_ptr))
            # map physical block number to virtual block number before returning
            # to the client.
            serverNum = self.data_blk_ptr
            pBlockNum = blockNum 
            virtual_block_number = self.__translate_physical_to_virtual_block(serverNum, pBlockNum)
            
            # point to the next server to write data to..
            # block_claim_dir is changed in the init function so the parity
            # blocks and data blocks are claimed in opposite directions.
            if self.block_claim_dir == NEXT:
                    # server pattern: 0, 1, 2, 3,.. 0, 1, 2, 3
                    self.data_blk_ptr = self.__next(self.data_blk_ptr)
            else:
                    # server pattern: 3, 2, 1, 0,.. 3, 2, 1, 0
                    self.data_blk_ptr = self.__prev(self.data_blk_ptr)
            self.block_claim_dir_old = self.block_claim_dir
            return virtual_block_number
			
        except Exception:
            print "ERROR (get_valid_data_block): Server failure.."
            return -1 
    
    '''
    SUMMARY: free_data_block
    Deallocate the specified data block.
    
    NOTE:
    This function also reads back the current DATA/PARITY blocks to adjust
    update the parity block.
    '''
    def free_data_block(self, virtual_block_number):
        try:
            # read back the current data block contents (1.FIRST READ)
            (serverNumData, pBlockData) = self.__translate_virtual_to_physical_block(virtual_block_number)
	    print("Freeing data block " + str(pBlockData) + " from server " + str(serverNumData))
            proxyData = self.proxy[serverNumData]				# find server 
	    currData = self.get_data_block(virtual_block_number)
            
            # read back the current parity block contents (2. SECOND READ)
            vParityNum = self.__pblock_number_to_vparity_number(pBlockData, serverNumData)	# virtual parity block number
            (serverNumParity, pParityNum) = self.__translate_virtual_to_physical_block(vParityNum) # find the physical block number and server to read/write
            proxyParity = self.proxy[serverNumParity]											# find server to read/write parity data from
            currParity = self.get_parity_block(serverNumParity, pParityNum)
                    
            # XOR to update the parity block with data being deleted
            newParity = self.__xor(currData, currParity)
            
            # update the parity block
            serialNewParity = pickle.dumps(newParity)
	    serialBlockNumParity = pickle.dumps(pParityNum)
            proxyParity.update_data_block(serialBlockNumParity, serialNewParity)
    
            # free the selected data block (finally :P)
	    serialPBlock = pickle.dumps(pBlockData)
            rx = proxyData.free_data_block(serialPBlock)
            deserialized = pickle.loads(rx)
            return deserialized[0]
        except Exception:
            print "ERROR (free_data_block): Server failure.."
            return -1
    
    '''
    SUMMARY: update_data_block
    Write the data block data to the appropriate server.
    
    NOTE:
    This function also reads back the DATA/PARITY blocks to calculate
    and update the parity data.
    
    The steps are labeled as 1,2,3,4 to match guide shown in the lecture
    slides (slide 66 - Parity in RAID 4,5)
    '''
    def update_data_block(self, virtual_block_number, block_data):
        try:
            # read back the current data block contents (1.FIRST READ)
            (serverNumData, pBlockData) = self.__translate_virtual_to_physical_block(virtual_block_number)
            proxyData = self.proxy[serverNumData]				# find server 
	    currData = self.get_data_block(virtual_block_number)
            
            # read back the current parity block contents (2. SECOND READ)
            vParityNum = self.__pblock_number_to_vparity_number(pBlockData, serverNumData)	# virtual parity block number
            (serverNumParity, pParityNum) = self.__translate_virtual_to_physical_block(vParityNum) # find the physical block number and server to read/write
            proxyParity = self.proxy[serverNumParity]											# find server to read/write parity data from
            currParity = self.get_parity_block(serverNumParity, pParityNum)

            # calculate the new parity block contents
            newData = list(block_data)
           
            # first XOR on the new data and the current data
            midData = self.__xor(newData, currData)

            # second XOR on middle data and current parity to find new parity block
            newParity = self.__xor(midData, currParity)

            # update the parity block contents (4. FIRST WRITE)
	    print("Updating parity block " + str(pParityNum) + " on server " + str(serverNumParity))
            serialBlockNum = pickle.dumps(pParityNum)
            serialBlockData = pickle.dumps(newParity)
            rx = proxyParity.update_data_block(serialBlockNum, serialBlockData)
            
            # update the data block with new data (3. SECOND WRITE)
	    print("Updating data block " + str(pBlockData) + " on server " + str(serverNumData))
            serialBlockNum = pickle.dumps(pBlockData)
            serialBlockData = pickle.dumps(block_data)
            rx = proxyData.update_data_block(serialBlockNum, serialBlockData)
            deserialized = pickle.loads(rx)
            return deserialized[0]
			
        except Exception:
            print "ERROR (update_data_block): Server failure.."
            return -1 
    
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    #                            INODE FUNCTIONS
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    
    def inode_number_to_inode(self, inode_number):
	try:
            serialMessage = pickle.dumps(inode_number)
	    for i in range(N):
		p = self.proxy[i]
                rx = p.inode_number_to_inode(serialMessage)
                deserialized = pickle.loads(rx)
		#todo: add ability to see block failure. if block failure then copy all inodes in block to the block that failed. 
		if(deserialized[1] == True): break
            return deserialized[0]
        except Exception:
            print "ERROR (inode_number_to_inode): Server failure.."
            return -1
    
    def update_inode_table(self, inode, inode_number):
        try:
            serialIn1 = pickle.dumps(inode)
            serialIn2 = pickle.dumps(inode_number)
	    for i in range(N):
                p = self.proxy[i]
                rx = p.update_inode_table(serialIn1, serialIn2)
            deserialized = pickle.loads(rx)
	    #todo: add ability to see block failure. if block failure then copy all inodes in block to the block that failed. 
            return deserialized[0]
        except Exception:
            print "ERROR (update_inode_table): Server failure.."
            return -1 
     
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    #                          PARITY BLOCK MAPPING
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
	
    '''
    SUMMARY: __next
    This function handles the wrap around for picking which server's 
    is pointed at.
    '''
    def __next(self, ptr):
        if ptr < N-1:
            ptr += 1 
        else:
            ptr = 0
        return ptr
		
    '''
    SUMMARY: __prev
    '''
    def __prev(self, ptr):
        if ptr > 0:
            ptr -= 1 
        else:
            ptr = N-1
        return ptr
		
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    #                         	OTHER AlGORITHMS
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
	
    '''
    SUMMARY: __xor
    This function performs the xor'ing of two blocks of data.
    '''
    def __xor(self, new, old):
        for i in range(len(new)):
            if old[i] == '\x00':
                old[i] = new[i]
            else:
                old[i] = chr(ord(new[i]) ^ ord(old[i]))
        return old
	
    '''
    SUMMARY: __physical_block_number_to_parity_index
    Maps physical block number and server number to the appropriate virtual parity block number.
    (This is the ugliest algorithm I've ever made and I'm sorry for that)
    '''
    def __pblock_number_to_vparity_number(self, physical_block_num, server_num):
        # parity block list index for specified data block
        r = (physical_block_num - self.first_data_block_num)%(N-1)
        s = server_num

        offset = self.offset_table[r][s]

        row = int(N * math.floor( (physical_block_num - self.first_data_block_num) / (N-1) ))

        iparity = row + offset
                    
        # virtual parity block number
        return self.parity_blocks[iparity]		
		
    '''
    SUMMARY: __vparity_number_to_pblock_list
    Returns a list of server numbers and physical block numbers that are related to the parity block
    number. (Each parity block has N-1 data blocks associated with it)
    '''
    def __vparity_number_to_pblock_list(self, virtual_parity_block_num):
        serverNumList = [i for i in range(1, N-1)] # skip parity block 0 in this example
        parityBlockNumList = [i*config.BLOCK_SIZE for i in range(1, N-1)]
        return (serverNumList, parityBlockNumList)
        
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    #                          BLOCK NUMBER MAPPING
    # +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
    
    '''
    SUMMARY: __translate_virtual_to_physical_block
    Translates a virtual block number to a physical block number and the port 
    offset for the target server.
    '''
    def __translate_virtual_to_physical_block(self, virtual_block_num):
        serverNum = (int)(math.floor(virtual_block_num/self.virtual_block_size))
        localBlockNum = virtual_block_num % self.virtual_block_size
        return (serverNum, localBlockNum)
    
    '''
    SUMMARY: __translate_physical_to_virtual_block
    Translates physical block number and server number it comes from to a virtual
    block number to be used in the client filesystem.
    '''
    def __translate_physical_to_virtual_block(self, server_num, physical_block_num):
        return (server_num * self.virtual_block_size) + physical_block_num

    '''
    SUMMARY: __proxy_of_virtual_block
    Returns proxy object from the server's proxy list based on the virtual block
    number passed in.
    '''
    def __proxy_of_virtual_block(self, virtual_block_number):
        serverNum = self.__translate_virtual_to_physical_block(virtual_block_number)
        return self.proxy[serverNum[0]]

