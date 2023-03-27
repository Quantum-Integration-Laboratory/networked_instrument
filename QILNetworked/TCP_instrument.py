"""
Most of the functions for handling of sockets come from this tutorial https://realpython.com/python-sockets/#multi-connection-client-and-server
I have commented my understand but don't actually know much more than what is there

"""

import sys
import socket
import selectors
import types
import struct
import numpy as np
import os
from contextlib import nullcontext
import traceback
#from abc import ABCMeta

# A pre agreed upon set of errors that are shared between client and server
ERRORID=b"~~~~"

ERRORS = {
    "ValueError": ERRORID+b"1",
    "FunctionError": ERRORID+b"2",
    "StatusError": ERRORID+b"3",
    "UnknownInput":ERRORID+b"4"
}

QUERYID=b"?"
FUNCTIONID=":"


#finds the key from the given value 
val2Key=lambda x,i: list(x.keys())[list(x.values()).index(i)]


class cTCPInstrumentServerMixin():
    def __init__(self,host:str=None,port:int=9090,silent:bool=False):
        """
        Implements a TCP/IP server for a generic instrument,  handles sending and reciving of data, and passes functions to 
        Co-parent class of the child class.

        Parameters
        ----------
        host: str
            The IP address/hostname on which to host, if passed None, will get the current hostname
        port: int
            The port to host on, needs to be unique to the host
        silent: bool
            Set if we want to print non critical information
        Returns
        -------
        """

        print("Initialising TCP/IP Server")

        #creates a selector, to deal with multiple inputs and outputs
        self.sel = selectors.DefaultSelector()

        #storage of the queries and functions lookup table
        self.queries = {}
        self.functions= {}

        #if we don't supply a host get the current computer
        if type(host)==type(None):
            self.host = socket.gethostname()
        else:
            self.host=host
        self.port=port

        self.silent=silent

        #create the socket and bind to a host and port, and start listening for calls
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((self.host, self.port))
        lsock.listen()
        
        
        #turn of blocking
        lsock.setblocking(False)
        #register the socket with the selector
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

    def run(self):
        """
        Mainloop of the server, regeisters and handles any read/write events that come in over the socket

        Parameters
        ----------
        
        Returns
        -------
        """
        print(f"Listening on {(self.host, self.port)}")

        try:
            while True:
                with HiddenPrints() if self.silent else nullcontext():
                    #get all connection attempts
                    events = self.sel.select(timeout=None)
                    for key,mask in events:
                        #If the connection is new do something
                        if key.data is None:
                            self.accept_wrapper(key.fileobj)
                        #If we have already accepted then do stuff with that connection
                        else:
                            self.service_connection(key, mask)

        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
            #return self.errorHandler("FunctionError")
            #print("ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host")
            #print("\t I will continue but you should check on the other guy")
            #self.run()
        finally:
            self.sel.close()

    def accept_wrapper(self,sock):
        """
        When we receive a new event register it as a socket, and start the connection

        Parameters
        ----------
        sock: socket
            pass the file object of the event key
        Returns
        -------
        """
        #accept the socket connection
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)

        #setup a data type, with address, an input and output buffer
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        #allow reading or writing
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        #register the new socket
        self.sel.register(conn, events, data=data)

    def service_connection(self,key, mask):
        """
        Actually do something with a registered connection
        
        Parameters
        ----------
        key: ¯⁠\⁠_⁠(⁠ツ⁠)⁠_⁠/⁠¯
            The actual contents of the event
        Mask: ¯⁠\⁠_⁠(⁠ツ⁠)⁠_⁠/⁠¯
            The port to host on, needs to be unique to the host

        Returns
        -------
        """
        #get socket and data from key
        sock = key.fileobj
        data = key.data
        try:
            #If we are reading
            if mask & selectors.EVENT_READ:
                #recieve data
                #try:
                recv_data = sock.recv(1024)  # Should be ready to read
                #If we recieved data append it to the buffer and close the connection
                if recv_data:
                    data.outb+=self.handleCalls(data.outb,recv_data)
                else:
                    print(f"Closing connection to {data.addr}")
                    self.sel.unregister(sock)
                    sock.close()
            #if we are writing
            if mask & selectors.EVENT_WRITE:
                #if we have data in the output buffer send it and remove it.
                if data.outb:
                    #print(f"Sending {data.outb!r} of length {len(data.outb)} to {data.addr}")
                    print(f"Sending packet of length {len(data.outb)} to {data.addr}")
                    sent = sock.send(data.outb)  # Should be ready to write
                    data.outb = data.outb[sent:]
        #Handle an error where the client is interupted while a socket is open
        except ConnectionResetError:
            self.sel.unregister(sock)
            sock.close()
            
            print("\nConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host")
            print("\t I will continue but you should check on the other guy\n")
            #del events

    
    def setQueries(self,queries:dict):
        """
        Setter for the queries, queries should be a short (Ideally 4 character) binary string key with an associated function to call,
        Query functions should take no input and return a single output, of any type
        
        This will likely eventually do more to enforce some standards
        Parameters
        ----------
        queries: dict
            A set of short key codes and the functions they correspond to.

        Returns
        -------
        """
        
        for k in queries:
            self.queries[(k).encode()+QUERYID]=queries[k]

        
        
    def setFunctions(self,functions:dict):
        """
        Setter for the functions, queries should be a short (Ideally 4 character) binary string key with an associated function to call,
        Functions can take an input and will return a numpy array
        
        Parameters
        ----------
        queries: dict
            A set of short key codes and the functions they correspond to.

        Returns
        -------
        """
        for k in functions:
           self.functions[k+FUNCTIONID]=functions[k]

        #self.functions=functions


    def handleCalls(self,output,input):
        """
        Works out if we made a query, function or unknown call, and make sure outputs are packaged as bytes
        
        Parameters
        ----------
        input: byte string
            the input recieved from the client
        output: byte string
            The output buffer

        Returns
        -------
        output: byte string
            The filled output buffer

        """
        #check if we are a query without any parameter passes
        if QUERYID in input:         
           output=self.handleQueries(input)
        #Just make it obvious we are making a function pass
        elif FUNCTIONID in input:
            output= self.handleFunction(input)
        else:
            output= self.errorHandler("UnknownInput")#"Unknown Input %s"%input
        return arb2Bytes(output)

    def handleQueries(self,input):
        """
        Handles queries, by looking up the key in the queries table
        
        Parameters
        ----------
        input: byte string
            the input recieved from the client, that has been verified to contain the query ID
        Returns
        -------
        output: byte string
            The filled output buffer

        """
        #if we have a valid key call that function
        if input in self.queries.keys():
            
            output  = self.queries[input]()
            
            #if we return a status flag, return an error code + the status
            if type(output)==str or type(output)==bool:
                output=self.errorHandler("StatusError")+str(output).encode()
        else:
            #otherwise flag an error
            output=self.errorHandler("FunctionError")
        return output
    
    def handleFunction(self,input):
        """
        Handles functions, unpacks all arguments, converts them to the correct type and call
        Parameters
        ----------
        input: byte string
            the input recieved from the client, verified to be a function call with spaced arguments
        
        Returns
        -------
        output: byte string
            The filled output buffer

        """
  
        #turn the input into a string and tokenize
        Istring = input.decode()
        tokens = Istring.split(" ")

        #remove the handle 
        hndl = tokens.pop(0)

        if hndl not in self.functions.keys():
            return self.errorHandler("FunctionError") 
        
        #get what function we want to run
        func = self.functions[hndl]
        #print("running func %s"%func)
        
        #After poping the handle arguments are the remaining tokens convert all args to their correct type
        args = typeConvert(tokens,func)

        #use list unpacking to fill in the correct values
        try:
            output  = func(*args)

        #if the function errors it will be printed to the server, this could be sent back as speed is no longer an issue but this is fine for now
        except Exception as error:
            exc_info=sys.exc_info()
            traceback.print_exc(exc_info)
            return self.errorHandler("FunctionError")
        #print(output)

        #Assume we are sending back an array as that is quite effecient to turn to bytes
        #May need to double check back conversion 
        return np.array(output).tobytes()



    def errorHandler(self,error):
        """
        Error handler, just ensure we have a mutually intelligible short code to send between client and server
        Parameters
        ----------
        error: string
           The error that we have raised        
        Returns
        -------
        output: byte string
            The error short code to return

        """
        output = ERRORS[error]
        return output



class cTCPInstrumentClientMixin():
    def __init__(self,host,port=9090,timeout=30) -> None:
        """
        A client wrapper for an inherited class, this generally needs a non-functional copy of the Co-Parent class to determine function layout.
        NOTE: This Must overload any functions of its Co-parent class to defer them to a query or function

        QUERYs:
            Can be simply handled by the LUT and should be defined as the form of the form
                {b"CODE?":function}
                def function(self):
                    return self.query(b"CODE?")
        FUNCTIONS:
            Are a bit more complicated but the overloaded functions, should have all default values set to None, so they can be inherited from
            the Co-Parent class.

            This function wrapper must handle filling in all default arguments, generating a call bytes string, sending a call and converting
            to the correct data type 
            
            An example call is given below
            ```
            def function(x,y=None,z=None):
                    #set expected return size
                returnBuffer=2048
                    #get dict of passed arguments
                args = locals()
                    #get a list of default arguments from inherited function
                defaults = super().function.__defaults__ 
                
                    #fill in all our default arguments from the Parent
                args= self.fillDefaults(args,defaults)
                
                    #encode our call        
                call=self.genFunctionCall(self.getScanRange,args)
        
                    #send the call, stating we will decode its data type 
                response = self.query(call,returnBuffer,decode=False)
                    #convert the bytes to a numpy array and return
                Data = np.frombuffer(response)
                return Data
    
            ```

        Parameters
        ----------
        host: str
            The IP address/hostname on which the server is hosted
        port: int
            The port the server is hosted on.

        Returns
        -------
        """

        self.host = host
        self.port = port
        self.timeout=timeout

        self.queries = {}
        self.functions= {}

    def setQueries(self,queries:dict):
        """
        Setter for the queries, client side inverts the dict so that the functions become the keys and the short codes the values
        Parameters
        ----------
        queries: dict
            A set of short key codes and the functions they correspond to.

        Returns
        -------
        """
        queries= invertDict(queries)
        for k in queries:
            self.queries[k]= (queries[k]).encode()+QUERYID

    def setFunctions(self,functions:dict):
        """
        Setter for the functions, client side inverts the dict so that the functions become the keys and the short codes the values
        Parameters
        ----------
        queries: dict
            A set of short key codes and the functions they correspond to.

        Returns
        -------
        """
        functions=invertDict(functions)
        for k in functions:
           self.functions[k]= (functions[k])+FUNCTIONID



    def query(self,string:bytes, buffer:int=1024,flt:bool=True):
        """
        Send a byte string to the server and receive a response.

        Parameters
        ----------
        string: bytes
            A byte string correpsonding to a query or function and its parameters
        buffer: int
            The expected maximum return size
        flt : bool
            If true convert the returned value to a float, otherwise return a bit string

        Returns
        -------
        data: bytes or float
            The data returned by the server, if decode is true this returns a float otherwise the bytes
        """
        #connect to the socket send the stirng and wait for a response.
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            s.connect((self.host,self.port))
            s.sendall(string)
            data=s.recv(buffer)
        #if we recieve an error flag, find it, work out what error it is
        #print the error type, the sent string and the returned string.
        if ERRORID in data:
            idx = data.find(ERRORID)
            flag = data[idx:idx+len(ERRORID)+1]
            error = val2Key(ERRORS,flag)
            raise KeyError("%s detected in string %s. Recieved: %s"%(error,string,data))
        if flt:
            return floatFromBytes(data)[0]
        else:
            return data
    def genFunctionCall(self,func,args):
        """
        Generates a the function call to send to the server, getting the correct code from the dict and appending argument
        
        Parameters
        ----------
        func: function
            The function object calling this function, ideally this could be done programatically
        args: list
            The list of arguments to pass
        Returns
        -------
        call: bytes
            The call to pass to query
        """
        #Look up the handle of the function to be called 
        hndl = self.functions[func]
        #generate the call string and encode on return
        call = " ".join(str(i) for i in [hndl]+args)
        return call.encode()
   
    def _fillDefaults(self,args:dict,defaults:list):
        """
        Fill in any none type arguments with the default argument of the inherited function
        
        Parameters
        ----------
        args: dict
            The results of a call to local(), by the calling function
        defaults: list
            The result of a call to super().func.__defaults__ by the calling function 
        
        Returns
        -------
        args: list
            A list of arguments wth all defaults as per the super
        """
        
        #get the total number of arguments, noting there will be a class reference appended
        nVars = len(args)-1
        #get the number of required args, i.e. without default values
        nRec = nVars-len(defaults)
        
        #iterate through the arguments
        for i,k in enumerate(args):
            #get the correct index for the optional args
            j=i-(nRec)
            #if its none use the default value
            if args[k]==None:
                args[k]=defaults[j]
        #convert to list and remove, self and class reference
        return list(args.values())[1:-1]

        
    

def typeConvert(args:list, func:callable):
    """
    Use typing hints to convert a list of argument strings to the correct type

    Parameters
    ----------
    args: list
        The results of a call to local(), by the calling function
    func: callable
        the function to get typing hints from 
    
    Returns
    -------
    args: list
        A list of arguments of the correct type
        
    """
    #gets all the typing annotations from a function
    types = list(func.__annotations__.values())
    #loop through and convert type
    for i,t in enumerate(types):
        args[i]=t(args[i])
    return args


# def repDefaults(oargs,func):
#     defaults=func.__defaults__
#     for i,a in enumerate(oargs):
#         if a ==defaults[i]:
#             oargs[i]=SKIPCHAR
#     return oargs

def arb2Bytes(x):
    """
    Convert a value of arbitrary data type to bytes

    NOTE: if you're using a new data type find byte efficient way to convert it

    Parameters
    ----------
    x: any
        The value to be converted
    
    Returns
    -------
    value: bytes
        The value as a byte expression
    
    """
    #null conversion
    if type(x)==bytes:
        return x
    #use encode for strings
    elif type(x)==str:
        return x.encode()
    #ints are easy
    elif type(x)==int:
        return bytes(x)
    #floats must be packed into a struct, "<" defines endianess
    elif type(x)==float:
        return struct.pack("<f",x)
    #for unknown types turn it into a string and encode, this is very inefficient
    #but should work for anything
    else:
        return str(x).encode()

def floatFromBytes(x):
    """
    Convert a set of bytes to a float.
    NOTE: double check sizings on this it may crash with more than 4 bytes
        
        Parameters
        ----------
        x: bytes
            A set of bytes to convert to a float
        Returns
        -------
        x: float
            the value as a float
        
    """
    return struct.unpack("<f",x)



def invertDict(x:dict):
    """
    Invert a dictionary such that its values become keys and vice-versa    
        Parameters
        ----------
        x: dict
            The dictionary to invert        
        Returns
        -------
        x: dicts
            The inverted dictionary
        
    """
    return {v: k for k, v in x.items()}

#block any calls to print to reduce overhead
# taken from https://stackoverflow.com/questions/8391411/how-to-block-calls-to-print User Alexander C
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout      