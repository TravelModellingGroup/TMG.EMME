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
            /*Ensure the project has a valid network to be exported*/
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Import.import_network_package",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteString("network_package_file", Path.GetFullPath("TestFiles/test.nwp"));
                     writer.WriteString("scenario_description", "Test Network");
                     writer.WriteNumber("scenario_number", 1);
                     writer.WriteString("conflict_option", "PRESERVE");
                 }), LogbookLevel.Standard));

            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_network_package",
                JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteString("export_file", Path.GetFullPath("OutputTestFiles/exportedNWP.nwp"));
                        writer.WriteNumber("scenario_number", 1);
                        writer.WriteString("extra_attributes", "all");
                    }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void ExportNetworkPackageModule()
        {
            /*Ensure the project has a valid network to be exported*/
            var importModule = new Emme.Import.ImportNetworkPackage()
            {
                Name = "Importer",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                NetworkPackageFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/test.nwp"), "NWP File Name"),
                ScenarioDescription = Helper.CreateParameter("From XTMF", "Description")
            };
            importModule.Invoke(Helper.Modeller);

            var module = new TMG.Emme.Export.ExportNetworkPackage()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                SaveTo = Helper.CreateParameter("OutputTestFiles/Exported.nwp"),
                Attributes = Helper.CreateParameter("all")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
