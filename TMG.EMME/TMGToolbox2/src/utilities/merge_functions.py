'''
    Copyright 2014 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of the TMG Toolbox.

    The TMG Toolbox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The TMG Toolbox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the TMG Toolbox.  If not, see <http://www.gnu.org/licenses/>.
'''

#---METADATA---------------------
'''
Merge Functions

    Authors: Peter Kucirek

    Latest revision by: 
    
    
    Merges functions from a .411 file, throwing an Exception if 
    a conflict of expression arises.
        
'''
#---VERSION HISTORY
'''
    0.0.1 Created
    
    0.1.0 Major overhaul of the popup GUI, which now displays all necessary changes at once.
    
    0.1.1 Bug fix to work properly with exported functions in a NWP file
    
    0.1.2 Minor update to check for null export file
    
    0.1.3 Conflicted functions are now sorted in alphabetical order
    
    1.0.0 Switched versioning system to start at 1.0.0. Additionally, added flag options
        to automate the tool.
    
'''

import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
#from PyQt4 import QtGui, QtCore
#from PyQt4.QtCore import Qt
from os import path as _path

_m.TupleType = object
_MODELLER = _m.Modeller() #Instantiate Modeller once.
_util = _MODELLER.module('tmg2.utilities.general_utilities')
_tmgTPB = _MODELLER.module('tmg2.utilities.TMG_tool_page_builder')

##########################################################################################################

class MergeFunctions(_m.Tool()):
    version = '1.0.0'
    tool_run_msg = ""
    number_of_tasks = 3 # For progress reporting, enter the integer number of tasks here
    
    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    
    function_file = _m.Attribute(str)
    revert_on_error = _m.Attribute(bool)
    
    conflict_option = _m.Attribute(str)
    
    RAISE_OPTION = "RAISE"
    PRESERVE_OPTION = "PRESERVE"
    OVERWRITE_OPTION = "OVERWRITE"
    EDIT_OPTION = "EDIT"
    SKIP_OPTION = "SKIP"

    OPTIONS_LIST = [(EDIT_OPTION, "EDIT - Launch an editor GUI to resolve conflicts manually."),
                  (RAISE_OPTION, "RAISE - Raise an error if any conflicsts are detected."),
                  (PRESERVE_OPTION, "PRESERVE - Preserve functional definitions from the current Emme project."),
                  (OVERWRITE_OPTION, "OVERWRITE - Overwrite functional definitions from the function file."),
                  (SKIP_OPTION, "SKIP - Do not import any functions to the current Emmebank.")]
    
    def __init__(self):
        #---Init internal variables
        self.TRACKER = _util.ProgressTracker(self.number_of_tasks) #init the ProgressTracker
        
        #---Set the defaults of parameters used by Modeller
        self.revert_on_error = True
        
        self.conflict_option = 'EDIT'
    
    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(self, title="Merge Functions v%s" % self.version,
                     description="Merges into this emmebank functions defined in a standard \
                         function transaction file. Delete and modify commands are ignored.\
                         <br><br>Detects conflicts in functional definitions and prompts \
                         user for input. New functions as simply merged in.",
                     branding_text="- TMG Toolbox 2")
        
        if self.tool_run_msg != "": # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)
        
        baseFolder = _path.dirname(_MODELLER.desktop.project_file_name())
        pb.add_select_file(tool_attribute_name='function_file',
                           window_type='file', start_path=baseFolder,
                           title="Functions File")
        
        pb.add_select(tool_attribute_name= 'conflict_option',
                      keyvalues= self.OPTIONS_LIST, title= "Conflict resolution option",
                      note= "Select an option for this tool to perform if \
                      conflicts in functional definitions are detected.")
        
        pb.add_checkbox(tool_attribute_name='revert_on_error',
                        label="Revert on error?")
        
        return pb.render()
    
    ##########################################################################################################
        
    def run(self):
        self.tool_run_msg = ""
        self.TRACKER.reset()
        
        if self.function_file == None:
            raise IOError("Import file not specified")
        
        try:
            self._Execute()
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc())
            raise
    
    ##########################################################################################################    
    
    
    def _Execute(self):
        with _m.logbook_trace(name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
                                     attributes=self._GetAtts()):
            
            file_functions = self._LoadFunctionFile()
            self.TRACKER.completeTask()
            
            database_functions = self._LoadFunctionsInDatabank()
            self.TRACKER.completeTask()
            
            if self.conflict_option == self.SKIP_OPTION:
                msg = "Skipped the import of functions."
            else:
                newFuncCount, modFuncCount = self._MergeFunctions(database_functions, file_functions)
                self.TRACKER.completeTask()            
                msg = "Done."
                if newFuncCount > 0:
                    msg += " %s functions added." %newFuncCount
                if modFuncCount > 0:
                    msg += " %s functions modified." %modFuncCount

            self.tool_run_msg = _m.PageBuilder.format_info(msg)
            _m.logbook_write(msg)

    ##########################################################################################################

    #----CONTEXT MANAGERS---------------------------------------------------------------------------------
    '''
    Context managers for temporary database modifications.
    '''
    
    @contextmanager
    def _NewFunctionMANAGER(self, newFunctions, modifiedFunctions):
        emmebank = _MODELLER.emmebank
        
        try:
            yield # Yield return a temporary object
        except Exception as e:
            if self.revert_on_error:
                for id in newFunctions:
                    emmebank.delete_function(id)
                for id, expression in modifiedFunctions.items():
                    emmebank.function(id).expression = expression
            raise
    
    
    #----SUB FUNCTIONS---------------------------------------------------------------------------------  
    
    def _GetAtts(self):
        atts = {
                "Functions File" : self.function_file,
                "Version": self.version,
                "self": self.__MODELLER_NAMESPACE__}
            
        return atts 
    
    def _LoadFunctionFile(self):
        functions = {}
        with open(self.function_file) as reader:
            expressionBuffer = ""
            trecord = False
            currentId = None
            
            for line in reader:
                line = line.rstrip()
                linecode = line[0]
                record = line[2:]
                
                if linecode == 'c':
                    pass
                elif linecode == 't':
                    if not record.startswith("functions"):
                        raise IOError("Wrong t record!")
                    trecord = True
                elif linecode == 'a':
                    if not trecord: raise IOError("A before T")
                    index = record.index('=')
                    currentId = record[:index].strip()
                    expressionBuffer = record[(index + 1):].replace(' ', '')
                    if currentId != None:
                        functions[currentId] = expressionBuffer
                elif linecode == ' ':
                    if currentId != None and trecord:
                        s = record.strip().replace(' ', '')
                        expressionBuffer += s
                        functions[currentId] = expressionBuffer
                elif linecode == 'd' or linecode == 'm':
                    currentId = None
                    expressionBuffer = ""
                else: raise KeyError(linecode)
                    
        return functions
    
    def _LoadFunctionsInDatabank(self):
        functions = {}
        for func in _MODELLER.emmebank.functions():
            expr = func.expression.replace(' ', '')
            functions[func.id] = expr
        return functions
    
    def _MergeFunctions(self, databaseFunctions, fileFunctions):
        emmebank = _MODELLER.emmebank
        
        
        databaseIds = set([key for key in databaseFunctions.keys()])
        fileIds = set([key for key in fileFunctions.keys()])
        
        newFunctions = []
        modifiedFunctions = {}
        with self._NewFunctionMANAGER(newFunctions, modifiedFunctions):
            for id in (fileIds - databaseIds): #Functions in the new source only
                expression = fileFunctions[id]
                emmebank.create_function(id, expression)
                _m.logbook_write("Added %s : %s" %(id, expression))
                newFunctions.append(id)
            
            conflicts = []
            for id in (fileIds & databaseIds): #Functions in both sources
                database_expression = databaseFunctions[id]
                file_expression = fileFunctions[id]
                if file_expression != database_expression:
                    conflicts.append((id, database_expression, file_expression))
            
            if len(conflicts) > 0:
                conflicts.sort()
                
                #If the PRESERVE option is selected, do nothing
                
                if self.conflict_option == self.OVERWRITE_OPTION:
                    #Overwrite exisiting functions with new ones
                    for fid, database_expression, file_expression in conflicts:
                        func = emmebank.function(fid)
                        func.expression = file_expression
                        modifiedFunctions[fid] = database_expression
                        with _m.logbook_trace("Changed function %s" %fid):
                            _m.logbook_write("Old expression: %s" %database_expression)
                            _m.logbook_write("New expresion: %s" %file_expression)
                elif self.conflict_option == self.EDIT_OPTION:
                    self._LaunchGUI(conflicts, modifiedFunctions)
                elif self.conflict_option == self.RAISE_OPTION:
                    tup = len(conflicts), ', '.join([t[0] for t in conflicts])
                    msg = "The following %s functions have conflicting definitions: %s" %tup
                    raise Exception(msg)
                        
        return len(newFunctions), len(modifiedFunctions)
    
    
    def _LaunchGUI(self, conflicts, modifiedFunctions):
        dialog = FunctionConflictDialog(conflicts)
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            acceptedChanges = dialog.getFunctionsToChange()
            for fid, expression in acceptedChanges.items():
                func = _MODELLER.emmebank.function(fid)
                oldExpression = func.expression
                func.expression = expression
                modifiedFunctions[fid] = oldExpression
                
                with _m.logbook_trace("Modified function %s" %fid.upper()):
                    _m.logbook_write("Old expression: %s" %oldExpression)
                    _m.logbook_write("New expression: %s" %expression)
        dialog.deleteLater()
    
    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self.TRACKER.getProgress()
                
    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
    
##########################################################################################

 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
