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
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using System.IO;
using System.Text;

namespace TMG.Emme.Test.Import
{
    [TestClass]
    public class ImportNetworkPackageTest
    {
        [TestMethod]
        public void ImportNetworkPackage()
        {
            string GetParameters()
            {
                string ret = null;
                using (MemoryStream backing = new MemoryStream())
                {
                    using (StreamWriter sWriter = new StreamWriter(backing, Encoding.Unicode, 0x4000, true))
                    using (JsonWriter writer = new JsonTextWriter(sWriter))
                    {
                        writer.WriteStartObject();
                        Helper.WriteProperty(writer, "network_package_file", Path.GetFullPath("test.nwp"));
                        Helper.WriteProperty(writer, "scenario_number", 1);
                        Helper.WriteProperty(writer, "add_functions", false);
                        Helper.WriteProperty(writer, "conflict_option", "PRESERVE");
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
            Assert.IsTrue(Helper.Modeller.Run(null, "tmg2.Import.import_network_package",
                new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", GetParameters()),
                    new ModellerControllerParameter("xtmf_logbook_level", Helper.LogbookAll)
                }));
        }
    }
}
