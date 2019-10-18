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
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using XTMF2;


namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportNetworkPackageTest : TestBase
    {
        [TestMethod]
        public void ExportNetworkPackage()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_network_package", new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteString("export_file", Path.GetFullPath("exported.nwp"));
                        writer.WriteNumber("scenario_number", 1);
                        writer.WriteString("extra_attributes", "all");                       
                    })),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                }));
        }

        [TestMethod]
        public void ExportNetworkPackageModule()
        {
            var module = new TMG.Emme.Export.ExportNetworkPackage()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                SaveTo = Helper.CreateParameter("Exported.nwp"),
                Attributes = Helper.CreateParameter("all")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
