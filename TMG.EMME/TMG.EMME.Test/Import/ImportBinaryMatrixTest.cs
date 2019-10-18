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

namespace TMG.Emme.Test.Import
{
    [TestClass]
    public class ImportBinaryMatrixTest : TestBase
    {
        [TestMethod]
        public void ImportBinaryMatrix()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Import.import_binary_matrix",
                new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteParameter("matrix_type", 4);
                        writer.WriteParameter("matrix_number", 1);
                        writer.WriteParameter("binary_matrix_file", Path.GetFullPath("test.mtx"));
                        writer.WriteParameter("scenario_number", 1);
                        writer.WriteParameter("matrix_description", "Test Matrix");
                    })),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                }));
        }

        [TestMethod]
        public void ImportBinaryMatrixModule()
        {
            var importModule = new Emme.Import.ImportBinaryMatrix()
            {
                Name = "Importer",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                MatrixNumber = Helper.CreateParameter(1, "Matrix Number"),
                FileLocation = Helper.CreateParameter("Test.mtx", "Matrix File Name"),
                Description = Helper.CreateParameter("Module Loaded", "Description")
            };
            importModule.Invoke(Helper.Modeller);
        }
    }
}
