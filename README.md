# QIL Networked Instrument
A set of Mixins for creating a class that allows a USB instrument to communicate over TCP/IP.

# Installation
It is important that the driver is installed in a permanent location, and remains in its git repository for pulling updates
 
Install is from the package directory
 
```
pip install --editable .
```
The `--editable` flag means the installed script just points back to the folder so updates are properly reflected, hence the need for a permanent location, and clear names.

# Developing a networked instrument
In order to develop a networked instrument we will assume that there is already a python class object (`cInstrument`) that can handle the calls over USB, or similar. We then wish to create both a client and server class that incorporates the client and server Mixins and the original instrument class.

The necessary imports will be the server and client mixins and the instrument class
```
from QILNetworked.TCP_instrument import cTCPInstrumentServerMixin,cTCPInstrumentClientMixin
from .instrument import cInstrument
```

## Overview, Terminology and Logic
We will define two classes of functions we may want to call generally separated by their ease of implementation
### Queries
Queries are simple functions that take no input (or all default input) and produce a single output returned as a float, they should cover most of our functionality 

### Functions
Functions are slightly more complicated in that they take inputs, to simplify some of the logic, sending a function call sends all parameters whether they are different from the default or not, however this should be handled within the client code as described later.

Any function used in this way must use typing hints and have a well defined type for each argument. By having type hints it is relatively easy for the server to look at what the correct type values for each argument is. 
    __NOTE:__ Though it is likely unnecessary it is also untested what passing complex argument types does. 

### FUNCDEFS class
As we want both the client and the server speaking the same language we want a lookup table (LUT) that is common to both that tells us what strings sent over the network connection correspond to what queries and functions. Each is held in its own dictionary

The keys of queries and functions are short descriptive strings (around 4 characters), the values are the function of the `cInstrument` class that that code will call. The code will do some further manipulations on the keys that will make each more identifiable as a function or query but for implementation strings are fine.

By defining this as a class we let the Method Resolution Order (MRO) defer all these calls to the class they are actually defined in, without the class, `self` would be undefined. We also give the `queries` and `functions` slightly different names (i.e. `lqueries` for load queries) so they are not automatically loaded, as their `getQueries` method performs some important operations.

An example `FUNCDEFS` class is given below.
```
class FUNCDEFS:
    def __init__(self):
        print("Importing Functions")
        self.lqueries = {
                    "FREQ": self.readFrequency,
                    "TEMP": self.readTemperature,
                    "WAVL": self.readWavelength,
                }

        self.lfunctions = {
                    "SCRN": self.getScanRange,
                    "INTC":self.getInternalC
        }
```


## Developing a server class
Developing the server is actually the simpler part, we will only define a `__init__` function as below
```
class cInstrumentServer(cInstrument,cTCPInstrumentServerMixin,FUNCDEFS):
    def __init__(self,host=None,port=9090,silent=False):

        cInstrument.__init__(self)
        FUNCDEFS.__init__(self)
        cTCPInstrumentServerMixin.__init__(self,host,port,silent)
        
        self.setQueries(self.lqueries)
        self.setFunctions(self.lfunctions)
```
Stepping through, we want this class to inherit from the instrument class `cInstrument` the server Mixin `cTCPInstrumentServerMixin` as well as our `FUNCDEFS` class.

Next we define our `__init__` that takes any arguments that may need to be passed on to its inherited inits. As the standard MRO tends to run the derived class not last, we want to make sure we explicitly call the derived `__init__`s in the correct order. The server can be called at any point, but the `cInstrument` must come before the `FUNCDEFS`, so that `FUNCDEFS` is pointing to the correct functions.

Finally once all the `__init__`s have been called we can do our query and function setters.

### `cTCPInstrumentServerMixin.__init__` Parameters
- `host` The host ip address, by setting to `None` the server will automatically determine the hostname.
- `port` The port the connection is accessible on, must be unique to the hostname, but must also be allowed by IT, so may require searching.
- `silent` Whether the server should print what it's doing to the terminal.

### Server Internals
The running of the server is heavily dependent on the methods in `cInstrument` not being overloaded by anything else. When a request is passed to the server we first check if it contains the `QUERYID` or `FUNCTIONID` character. 
- For a query we simply check the query is a valid key, and then call the corresponding value, which from the MRO will default to the function of `cInstrument` 
- For a function we have taken a standardised format that we will pass the function handle and arguments in a space separated format
    - We first tokenize the input string based on the above, taking the function key as the first element
    - We check the function is valid
    - We then use the functions typing annotations to determine the correct data type, fill these in and call the function.
    - If the output of the function was successful we convert to a numpy array and encode it.
        - If unsuccessful the server prints the traceback and sends an error to the client.


## Developing a Client class 
For the most part the initialisation of the client class is the same as the server, with the added caveat that `cTCPInstrumentClientMixin` requires we input a host, However this derived class can still have a default. 

It is also important to note that the client copy of `cInstrument` should never initialise, as we don't have access to the instrument this should fail fast, but may require some rewrites of the `cInstrument` class to prevent its connection on initialisation.

An example __init__ is given below but not expanded upon.
```
class cInstrumentClient(cInstrument,cTCPInstrumentClientMixin,FUNCDEFS):
    def __init__(self,host="host-name",port=9090):
        cInstrument.__init__(self,init=False)
        FUNCDEFS.__init__(self)
        cTCPInstrumentClientMixin.__init__(self,host=host,port=port)
        self.setQueries(self.lqueries)
        self.setFunctions(self.lfunctions)
```

The client class should overload any function we may want to call (i.e. any non-protected method) of `cInstrument`, if the functions are not overloaded a call will likely try to access an instrument that doesn't exist. 

As a note the `setQueries` and `setFunctions` methods in the client reverse the key and value order, i.e the short code that describes the function.

### Writing Query functions
Query functions are very simple and likely the same for each, an example is given below.
```
 def readFrequency(self):
        hndl = self.queries[readFrequency]
        return self.query(hndl,flt=True)
```
We simply overload the function of the same name to look up what code we wish to send, send it and get the return, setting the `flt` flag to true converts the returned values to a `float`.

Ideally these can eventually be generated programmatically from the LUT, though for now it seems to be difficult to get the calling function as an object, and I'm trying to avoid `eval`

### Writing Function functions:
These are less likely to be as simple as Queries in future, however they still contain more boilerplate code than I would like, but most of these things need to be done in function scope. An example is given below
```
def getScanRange(self, freq: float, runs: int = None, ret: str = None, rnd: int = None):
        #get dict of passed arguments and list of default arguments from inherited function
        args = locals()
        defaults = super().getScanRange.__defaults__ 
                
        #fill in a list of args, get our handle and convert into our call string
        args= self._fillDefaults(args,defaults)
        
        #encode our call       
        call=self.genFunctionCall(self.getScanRange,args)
        #NOTE: code from here onwards will be more function dependant

        #send the call, get a response and convert the datatype
        response = self.query(call,2048,flt=False)
        
        scanData = np.frombuffer(response)
        return scanData
```
Walking through
- `locals()` gets the names and values of each passed argument
- `super().function.__defaults__` gets all the default values as defined by the function we are overloading, i.e. we don't have to define them twice
- `self._fillDefaults` gets an argument list where any omitted values are replaced with their default.
- `self.genFunctionCall` encodes the function we wish to call and its arguments into the correct format
- We send the function call, where the value `2048` defines the return buffer, and should be tailored to the function being called.
- As per the query definition this time we don't convert to a float but keep the bytes which can then be converted to a more appropriate data type.

The calls `_fillDefaults` through `self.query` could be combined into one function as they don't require function scope and will largely be the same for each function but it is a bit more transparent to leave them seperate.


# Running the server:
To run a server of the defined instrument class we simply instantiate a server instance, and call its run function a simple python file is given as an example
```
#runServer.py
from QILInsturment import TCP_Instrument
Instrument_server = TCP_Instrument.cInstrumentServer(silent=False)
Insturment_server.run()
```
To simplify running we can also create a `.bat` file that uses the `-c` file to call the above lines, here the `;` character represents a new line and the `pause` line ensures we don't close the terminal on a crash.
```
#runServer.bat
python -c "from QILInsturment import TCP_Instrument;Instrument_server = TCP_Instrument.cInstrumentServer(silent=False);Insturment_server.run()
"
pause
```
This method is slightly harder to read but saves changing two files when you wish to change things.

