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
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Import
{
    [Module(Name = "Import Network Package", Description = "Import an EMME scenario from a network package into the dataank.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ImportNetworkPackage : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(null, "tmg2.Import.import_network_package",
                new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", GetParameters()),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                });
        }

        [Parameter(DefaultValue = "myNetwork.nwp", Index = 0, Name = "Network Package File",
            Description = "The location of the file to load into the EMME bank.")]
        public IFunction<string> NetworkPackageFile;

        [Parameter(DefaultValue = "1", Index = 1, Name = "Scenario Number", Description = "The scenario to import into.")]
        public IFunction<int> ScenarioNumber;

        private string GetParameters()
        {
            string ret = null;
            using (MemoryStream backing = new MemoryStream())
            {
                using (StreamWriter sWriter = new StreamWriter(backing, Encoding.Unicode, 0x4000, true))
                using (JsonWriter writer = new JsonTextWriter(sWriter))
                {
                    writer.WriteStartObject();
                    writer.WritePropertyName("network_package_file");
                    writer.WriteValue(Path.GetFullPath(NetworkPackageFile.Invoke()));
                    writer.WritePropertyName("scenario_number");
                    writer.WriteValue(ScenarioNumber.Invoke());
                    writer.WritePropertyName("add_functions");
                    writer.WriteValue(true);
                    writer.WritePropertyName("conflict_option");
                    writer.WriteValue("OVERWRITE");
                    writer.WriteEndObject();
                    writer.Flush();
                    sWriter.Flush();
                }
                backing.Position = 0;
                using (StreamReader reader = new StreamReader(backing))
                {
                    ret = reader.ReadToEnd();
                }
            }
            return ret;
        }
    }
}
