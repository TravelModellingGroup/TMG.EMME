/*
    Copyright 2017 University of Toronto

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
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Import
{
    [Module(Name = "Import Network Package", Description = "Import an EMME scenario from a network package into the databank.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ImportNetworkPackage : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Import.import_network_package", GetParameters(), LogbookLevel.Standard);
        }

        [Parameter(DefaultValue = "myNetwork.nwp", Index = 0, Name = "Network Package File",
            Description = "The location of the file to load into the EMME bank.")]
        public IFunction<string> NetworkPackageFile;

        [Parameter(DefaultValue = "1", Index = 1, Name = "Scenario Number", Description = "The scenario to import into.")]
        public IFunction<int> ScenarioNumber;

        private string GetParameters()
        {
            return JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteString("network_package_file", Path.GetFullPath(NetworkPackageFile.Invoke()));
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteBoolean("add_functions", true);
                writer.WriteString("conflict_option", "OVERWRITE");
            });
        }
    }
}
