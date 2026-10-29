/*
    Copyright 2017-2026 University of Toronto

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

namespace TMG.Emme.Test.Export;

[TestClass]
public class ExportBinaryMatrixTest : TestBase
{
    const int ScenarioNumber = 1;

    [TestMethod]
    public void ExportBinaryMatrix()
    {
        SetupTest();

        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Export.export_binary_matrix",
             JSONParameterBuilder.BuildParameters(writer =>
             {
                 writer.WriteNumber("matrix_type", (int)Emme.Export.ExportBinaryMatrix.MatrixTypes.MF);
                 writer.WriteNumber("matrix_number", 10);
                 writer.WriteString("file_location", Path.GetFullPath("OutputTestFiles/testEBM.mtx"));
                 writer.WriteNumber("scenario_number", 1);
             }), LogbookLevel.Standard));
        Assert.IsTrue(File.Exists("OutputTestFiles/testEBM.mtx"), "Even though the module executed successfully, we did not get the output file!");
    }

    [TestMethod]
    public void ExportBinaryMatrixModule()
    {
        SetupTest();

        var module = new Emme.Export.ExportBinaryMatrix()
        {
            Name = "Exporter",
            ScenarioNumber = Helper.CreateParameter(ScenarioNumber, "Const Number"),
            MatrixNumber = Helper.CreateParameter(10, "Matrix Number"),
            MatrixType = Helper.CreateParameter(Emme.Export.ExportBinaryMatrix.MatrixTypes.MF, "Matrix Type"),
            SaveTo = Helper.CreateParameter(Path.GetFullPath("OutputTestFiles/testEBM.mtx"), "Matrix File Name")
        };
        module.Invoke(Helper.Modeller);
        Assert.IsTrue(File.Exists("OutputTestFiles/testEBM.mtx"), "Even though the module executed successfully, we did not get the output file!");
    }

    private static void SetupTest()
    {
        // Make sure that the output directory exists and does not have our output file.
        if (!Directory.Exists("OutputTestFiles"))
        {
            Directory.CreateDirectory("OutputTestFiles");
        }
        else
        {
            if (File.Exists("OutputTestFiles/testEBM.mtx"))
            {
                File.Delete("OutputTestFiles/testEBM.mtx");
            }
        }
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
        Helper.ImportBinaryMatrix(ScenarioNumber, 10, Path.GetFullPath("TestFiles/Test.mtx"));
    }
}
