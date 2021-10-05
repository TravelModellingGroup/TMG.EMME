'''
    Copyright 2014-2019 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of XTMF.

    XTMF is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    XTMF is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XTMF.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import print_function
import sys
import os
import glob
import time
import math
import array
import inspect
import six
import timeit
import traceback as _traceback
from inro.emme.desktop import app as _app
import inro.modeller
import inro.modeller as _m
from threading import Thread
import threading
import time
from contextlib import contextmanager
import json

class ProgressTimer(Thread):
    def __init__(self, delegateFunction, XtmfBridge):
        self._stopped = False
        self.delegateFunction = delegateFunction
        self.bridge = XtmfBridge
        Thread.__init__(self)
        self.run = self._run
    
    def _run(self):
        while not self._stopped:
            progressTuple = self.delegateFunction()
            if progressTuple[2] is not None:
                self.bridge.ReportProgress((float(progressTuple[2]) - progressTuple[0]) / (progressTuple[1] - progressTuple[0]))
            time.sleep(0.01667)
    
    def stop(self):
        self._stopped = True

# A Stream that does nothing
class NullStream:
    # Do nothing
     def __init__(self): 
         pass 
     # fake the write method
     def write(self, data): 
         pass

# A Stream which redirects print statements to XTMF Console
class RedirectToXTMFConsole:
    def __init__(self, xtmfBridge):
        self.bridge = xtmfBridge
    
    def write(self, data):
        self.bridge.SendPrintSignal(str(data))

    def flush(self):
        pass

def RedirectLogbookWrite(name, attributes=None, value=None):
    pass

@contextmanager
def RedirectLogbookTrace(name, attributes=None, value=None):
    try:
        yield None
    finally:
        pass

class XTMFBridge:
    """Our link to the EMME modeller"""
    Modeller = None
    """The name of the field that XTMF enabled Modeller Tools will use"""
    _XTMFCallParameters = "XTMFCallParameters"
    
    # Message numbers
    """Tell XTMF that we are ready to start accepting messages"""
    SignalStart = 0
    """Tell XTMF that we exited / XTMF is telling us to exit"""
    SignalTermination = 1
    """XTMF is telling us to start up a tool <Depricated>"""
    SignalStartModule = 2
    """Tell XTMF that we have successfully ran the requested tool"""
    SignalRunComplete = 3
    """Tell XTMF that we have had an error when creating the parameters"""
    SignalParameterError = 4
    """Tell XTMF that we have had an error while running the tool"""
    SignalRuntimeError = 5
    """XTMF says we need to clean out the modeller log book"""
    SignalCleanLogbook = 6
    """We say that we need to generate a progress report for XTMF"""
    SignalProgressReport = 7
    """Tell XTMF that we have successfully ran the requested tool"""
    SignalRunCompleteWithParameter = 8
    """XTMF is requesting a check if a Tool namespace exists"""
    SignalCheckToolExists = 9
    """Tell XTMF that we have had an error finding the requested tool"""
    SignalSendToolDoesNotExistsError = 10
    """Tell XTMF that a print statement has been encountered and to write to the Run Console"""
    SignalSendPrintMessage = 11
    """Signal from XTMF to disable writing to logbook"""
    SignalDisableLogbook = 12
    """Signal from XTMF to enable writing to logbook"""
    SignalEnableLogbook = 13    
    """Signal from XTMF to start up a tool using binary parameters"""
    SignalStartModuleBinaryParameters = 14
    """Signal to XTMF saying that the current tool is not compatible with XTMF2"""
    SignalIncompatibleTool = 15
        
    """Initialize the bridge so that the tools that we run will not accidentally access the standard I/O"""
    def __init__(self):
        self.CachedLogbookWrite = _m.logbook_write
        self.CachedLogbookTrace = _m.logbook_trace
        
        # Redirect sys.stdout
        sys.stdin.close()
        self.XTMFPipe = open('\\\\.\\pipe\\' + pipeName, 'w+b', 0)
        #sys.stdout = NullStream()
        self.IOLock = threading.Lock()
        sys.stdin = None
        sys.stdout = RedirectToXTMFConsole(self)
        return
          
    def ReadString(self):
        length = self.ReadInt()
        try:
            stringArray = array.array('u')
            stringArray.fromfile(self.XTMFPipe, length)
            return str(stringArray.tounicode()) 
        except:
            return str(stringArray.tounicode())

    def ReadInt(self):
        intArray = array.array('l')
        intArray.fromfile(self.XTMFPipe, 1)
        return intArray.pop()
    
    def IsWhitespace(self, c):
        return (c == ' ') or (c == '\t') or (c == '\s')
    
    def CreateTool(self, toolName):
        return self.Modeller.tool(toolName)
    
    def SendString(self, stringToSend):
        msg = array.array('u', six.text_type(stringToSend))
        length = len(msg) * msg.itemsize
        tempLength = length
        bytes = 0
        #figure out how many bytes we are going to need to store the length
        #string
        while tempLength > 0:
            tempLength = tempLength >> 7
            bytes += 1
        lengthArray = array.array('B')
        if length <= 0:
            lengthArray.append(0)
        else:
            tempLength = length
            for i in range(bytes):
                current = int(tempLength >> 7)
                current = int(current << 7)
                diff = tempLength - current
                if tempLength < 128:
                    lengthArray.append(diff)
                else:
                    lengthArray.append(diff + 128)
                tempLength = tempLength >> 7
        lengthArray.tofile(self.XTMFPipe)
        msg.tofile(self.XTMFPipe)
        return
    
    def SendToolDoesNotExistError(self, namespace):
        self.IOLock.acquire()
        self.SendSignal(self.SignalSendToolDoesNotExistsError)
        self.SendString("A tool with the following namespace could not be found: %s" % namespace)
        self.IOLock.release()
        return

    def SendIncompatibleTool(self, namespace):
        self.IOLock.acquire()
        self.SendSignal(self.SignalIncompatibleTool)
        self.SendString("The tool with the following namespace did not have an entry point for XTMF2: %s" % namespace)
        self.IOLock.release()

    def SendParameterError(self, problem):
        self.IOLock.acquire()
        self.SendSignal(self.SignalParameterError)
        self.SendString(problem)
        self.IOLock.release()
        return
        
    def SendRuntimeError(self, problem):
        self.IOLock.acquire()
        self.SendSignal(self.SignalRuntimeError)
        self.SendString(problem)
        self.IOLock.release()
        return
    
    def SendSuccess(self):
        self.IOLock.acquire()
        intArray = array.array('l')
        intArray.append(self.SignalRunComplete)
        intArray.tofile(self.XTMFPipe)
        self.IOLock.release()
        return
    
    def SendReturnSuccess(self, returnValue):
        self.IOLock.acquire()
        self.SendSignal(self.SignalRunCompleteWithParameter)
        self.SendString(str(returnValue))
        self.IOLock.release()
        return

    def SignalToolExists(self):
        self.IOLock.acquire()
        self.SendSignal(self.SignalCheckToolExists)
        self.IOLock.release()
        return
    
    def SendSignal(self, signal):
        intArray = array.array('l')
        intArray.append(signal)
        intArray.tofile(self.XTMFPipe)
        return
    
    def SendPrintSignal(self, stringToPrint):
        self.IOLock.acquire()
        self.SendSignal(self.SignalSendPrintMessage)
        self.SendString(stringToPrint)
        self.IOLock.release()
        return

    def ReportProgress(self, progress):
        self.IOLock.acquire()
        self.SendSignal(self.SignalProgressReport)
        floatArray = array.array('f')
        floatArray.append(float(progress))
        floatArray.tofile(self.XTMFPipe)
        self.IOLock.release()   
        return

    def EnsureModellerToolExists(self, macroName):
        for i in range(1, 10):
            if macroName in self.Modeller.tool_namespaces():       
                return True
            time.sleep(1)
        _m.logbook_write("A tool with the following namespace could not be found: %s" % macroName)
        self.SendToolDoesNotExistError(macroName)
        return False
    
    def ExecuteModule(self):
        macroName = None
        parameterString = None
        timer = None
        # run the module here
        try:
            #figure out how long the macro's name is
            macroName = self.ReadString()
            parameterString = self.ReadString()
            logbook_level = self.ReadString()
            if not self.EnsureModellerToolExists(macroName):
                return
            self.SignalToolExists()

            tool = self.CreateTool(macroName)
            if 'run_xtmf' not in dir(tool):
                self.SendIncompatibleTool(macroName)
                return
            nameSpace = {'tool':tool, 'parameters':json.loads(parameterString)}
            callString = 'tool.run_xtmf(parameters)'
            
            #Now that everything is ready, attach an instance of ourselves into
            #the tool so they can send progress reports
            tool.XTMFBridge = self
            
            if "percent_completed" in dir(tool):
                timer = ProgressTimer(tool.percent_completed, self)
                timer.start()
            #Execute the tool, getting the return value
            previous_logbook_level = _m.logbook_level()
            if logbook_level == 'STANDARD':
                _m.logbook_level(_m.LogbookLevel.TRACE | _m.LogbookLevel.LOG)
            elif logbook_level == "NONE":
                _m.logbook_level(_m.LogbookLevel.NONE)
            else:
                # Enable everything for debugging
                _m.logbook_level(_m.LogbookLevel.TRACE | _m.LogbookLevel.LOG | _m.LogbookLevel.COOKIE | _m.LogbookLevel.ATTRIBUTE | _m.LogbookLevel.VALUE)
            try:
                ret = eval(callString, nameSpace, None)
            finally:
                _m.logbook_level(previous_logbook_level)
            
            if timer != None:
                timer.stop()
            
            nameSpace = None
            if ret == None: 
                self.SendSuccess()
            else:
                self.SendReturnSuccess(ret)
        except Exception as inst:
            if timer != None:
                timer.stop()
            _m.logbook_write("We are in the exception code for ExecuteModule")
            if(macroName != None):
                _m.logbook_write("Macro Name: " + macroName)
            else:
                _m.logbook_write("Macro Name: None")
            if(parameterString != None):
                _m.logbook_write("Parameter : " + parameterString)
            else:
                _m.logbook_write("Parameter : None")
            _m.logbook_write(str(inst))
            _m.logbook_write("Finished dumping exception")

            etype, evalue, etb = sys.exc_info()
            stackList = _traceback.extract_tb(etb)
            msg = "%s: %s\n\nStack trace below:" % (evalue.__class__.__name__, str(evalue))
            stackList.reverse()
            for file, line, func, text in stackList:
                msg += "\n  File '%s', line %s, in %s" % (file, line, func)
            self.SendRuntimeError(msg)
            print (msg)
        return
    
    def Run(self, emmeApplication, performanceMode):
        self.emmeApplication = emmeApplication
        self.Modeller = inro.modeller.Modeller(emmeApplication)
        _m.logbook_write("Activated modeller from ModellerBridge for XTMF")
        if performanceMode:
            _m.logbook_write("Performance Testing Activated")
        exit = False
        self.SendSignal(self.SignalStart)
        while(not exit):
            input = self.ReadInt()
            if input == self.SignalTermination:
                _m.logbook_write("Exiting on termination signal from XTMF")
                exit = True
            elif input == self.SignalStartModule:
                exit = True
                self.SendSignal(self.SignalTermination)
            elif input == self.SignalStartModuleBinaryParameters:
                if performanceMode:
                    t = timeit.Timer(self.ExecuteModule).timeit(1)
                    _m.logbook_write(str(t) + " seconds to execute.")
                else:
                    self.ExecuteModule()
            elif input == self.SignalCheckToolExists:
                self.CheckToolExists()
            else:
                #If we do not understand what XTMF is saying quietly die
                exit = True
                _m.logbook_write("Exiting on bad input \"" + input + "\"")
                self.SendSignal(self.SignalTermination)
        return

    def CheckToolExists(self):
        ns = self.ReadString()
        ret = ns in self.Modeller.tool_namespaces()
        if ret == False:
            _m.logbook_write("Unable to find a tool named " + ns)
        self.SendReturnSuccess(ret)
        return
    
    def DisableLogbook(self):
        _m.logbook_write = RedirectLogbookWrite
        _m.logbook_trace = RedirectLogbookTrace
    
    def EnableLogbook(self):
        _m.logbook_write = self.CachedLogbookWrite
        _m.logbook_trace = self.CachedLogbookTrace
    
#end XTMFBridge

#Get the project file
args = sys.argv # 0: This script's location, 1: Emme project file, 2: User initials, 3:
                # Performance flag
projectFile = args[1]
userInitials = args[2]
performanceFlag = bool(int(args[3]))
pipeName = args[4]
#sys.stderr.write(args)
print (userInitials)
print (projectFile)
try:
    TheEmmeEnvironmentXMTF = _app.start_dedicated(visible=False, user_initials=userInitials, project=projectFile)
    XTMFBridge().Run(TheEmmeEnvironmentXMTF, performanceFlag)
    TheEmmeEnvironmentXMTF.close()
except Exception as e:
    pass
