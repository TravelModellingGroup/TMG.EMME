"""
    Copyright 2016 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
"""
# ---METADATA---------------------
"""
Copy Scenario

    Authors: JamesVaughan

    Latest revision by: JamesVaughan
    
    
    This tool will allow XTMF to be able to copy scenarios within 
    an EMME Databank.
        
"""
# ---VERSION HISTORY
"""
    0.0.1 Created on 2016-03-23 by JamesVaughan
    
    
"""
import inro.modeller as _m
import traceback as _traceback

_MODELLER = _m.Modeller()  # Instantiate Modeller once.


class CopyScenario(_m.Tool()):
    version = "0.0.1"

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Copy Scenario",
            runnable=False,
            description="Cannot be called from Modeller.",
            branding_text="XTMF",
        )

        return pb.render()

    def run(self):
        pass

    def run_xtmf(self, parameters):
        from_scenario = parameters["from_scenario"]
        to_scenario = parameters["to_scenario"]
        copy_strategy = parameters["copy_strategy"]
        try:
            self._execute(from_scenario, to_scenario, copy_strategy)
        except Exception as e:
            raise Exception(_traceback.format_exc())

    def _execute(self, from_scenario, to_scenario, copy_strategy):
        if from_scenario == to_scenario:
            print(
                "A copy was requested to from scenario "
                + str(from_scenario)
                + " to "
                + str(to_scenario)
                + ".  This was not executed."
            )
            return
        project = _MODELLER.emmebank
        original = project.scenario(str(from_scenario))
        if original == None:
            raise Exception(
                "The base scenario '"
                + str(from_scenario)
                + "' does not exist in order to copy to scenario '"
                + str(to_scenario)
                + "'!"
            )
        dest = project.scenario(str(to_scenario))
        if dest != None:
            project.delete_scenario(dest.id)
        if copy_strategy == True:
            project.copy_scenario(original.id, str(to_scenario), True, True, True)
        else:
            project.copy_scenario(original.id, str(to_scenario), True, False, True)
