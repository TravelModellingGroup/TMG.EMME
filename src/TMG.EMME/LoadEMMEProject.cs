/*
    Copyright 2026 University of Toronto

    This file is part of TMG.EMME for XTMF2.

    TMG.EMME for XTMF2 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    TMG.EMME for XTMF2 is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TMG.EMME for XTMF2.  If not, see <http://www.gnu.org/licenses/>.
*/
using XTMF2;

namespace TMG.Emme;

[Module(Name = "Load EMME Project", Description = "Loads an EMME project and provides a ModellerController to interact with it.",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
public sealed class LoadEMMEProject : BaseFunction<ModellerController>
{

    [SubModule(Name = "Project File", Description = "The EMME project file to load.", Required = true, Index = 0)]
    public IFunction<string> ProjectFile = null!;

    [Parameter(Name = "EMME Path", Description = "The path to the EMME installation, leave blank to use the environment variable EMMEPATH.", Required = false, Index = 1, DefaultValue = "")]
    public IFunction<string> EMMEPath = null!;

    [Parameter(Name = "EMME Bank", Description = "The name of the EMME bank to load, leave blank to use the default bank.", Required = false, Index = 2, DefaultValue = "")]
    public IFunction<string> EMMEBank = null!;

    [Parameter(Name = "Check All Tools Exist", Description = "Whether to check that all required tools exist before loading the project.", Required = true, Index = 3, DefaultValue = "false")]
    public IFunction<bool> CheckAllToolsExist = null!;

    public override ModellerController Invoke()
    {
        var projectFile = ProjectFile.Invoke();
        var emmePath = EMMEPath?.Invoke();

        // TODO: We will likely need to add the ability to set the EMME bank in the future, but for now we will just ignore it if it is not provided.
        var emmeBank = EMMEBank?.Invoke();
        if (!string.IsNullOrWhiteSpace(emmeBank))
        {
            throw new XTMFRuntimeException(this, "Setting the EMME databank is not supported yet!");
        }
        var controller = new ModellerController(this, projectFile, emmePath: emmePath);
        if (CheckAllToolsExist.Invoke())
        {
            controller.CheckAllToolsExist(this);
        }
        return controller;
    }
}
