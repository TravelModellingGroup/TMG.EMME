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
using System.IO;

namespace TMG.Emme.Test.Export
{

    [TestClass]
    public class ExportBinaryMatrixTest : TestBase
    {

        [TestMethod]
        public void ExportBinaryMatrix()

        {

            /*Ensure the scenario has a valid network and at least one matrix to be exported*/
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
                Helper.Modeller.Run(null, "tmg2.Import.import_binary_matrix",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteNumber("matrix_type", 4);
                     writer.WriteNumber("matrix_number", 10);
                     writer.WriteString("binary_matrix_file", Path.GetFullPath("TestFiles/Test.mtx"));
                     writer.WriteNumber("scenario_number", 1);
                     writer.WriteString("matrix_description", "Test Matrix");
                 }), LogbookLevel.Standard));


            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_binary_matrix",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteNumber("matrix_type", 4);
                     writer.WriteNumber("matrix_number", 1);
                     writer.WriteString("file_location", Path.GetFullPath("OutputTestFiles/exportedEBM.mtx"));
                     writer.WriteNumber("scenario_number", 1);
                 }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void ExportBinaryMatrixModule()
        {
            /*
            string outputFolder = Path.GetFullPath("OutputTestFiles");

            if (!Directory.Exists(outputFolder))
            {
                Directory.CreateDirectory(outputFolder);
            }
            */

            /*Ensure the scenario has a valid network and at least one matrix to be exported*/
            var importNetworkModule = new Emme.Import.ImportNetworkPackage()
            {
                Name = "Importer",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                NetworkPackageFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/test.nwp"), "NWP File Name"),
                ScenarioDescription = Helper.CreateParameter("From XTMF", "Description")
            };
            importNetworkModule.Invoke(Helper.Modeller);
            var importMatrixModule = new Emme.Import.ImportBinaryMatrix()
            {
                Name = "Importer",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                MatrixNumber = Helper.CreateParameter(1, "Matrix Number"),
                FileLocation = Helper.CreateParameter(Path.GetFullPath("TestFiles/Test.mtx"), "Matrix File Name"),
                Description = Helper.CreateParameter("Module Loaded", "Description")
            };
            importMatrixModule.Invoke(Helper.Modeller);


            var module = new Emme.Export.ExportBinaryMatrix()
            {
                Name = "Exporter",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                MatrixNumber = Helper.CreateParameter(1, "Matrix Number"),
                MatrixType = Helper.CreateParameter(4, "Matrix Type"),
                SaveTo = Helper.CreateParameter(Path.GetFullPath("OutputTestFiles/testEBM.mtx"), "Matrix File Name")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
