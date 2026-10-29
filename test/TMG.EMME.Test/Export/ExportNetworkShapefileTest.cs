/*
    Copyright 2022-2026 University of Toronto

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
using System.IO;

namespace TMG.Emme.Test.Export;

[TestClass]
public class ExportNetworkShapefileTest : TestBase
{
    const int ScenarioNumber = 1;

    const string OutputDir = "OutputTestFiles";

    const string OutputFile = OutputDir + "/exportedSHP";

    private static void SetupTest()
    {
        if (!Directory.Exists(OutputDir))
        {
            Directory.CreateDirectory(OutputDir);
        }
        else
        {
            // Clear the directory of any existing files
            if(Directory.Exists(OutputFile))
            {
                Directory.Delete(OutputFile, true);
            }
        }
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
    }

    private static void TestOutputExists()
    {
        ReadOnlySpan<string> expectedShapeFiles = ["emme_links.shp", "emme_nodes.shp", "emme_tsegs.shp"];
        foreach(var file in expectedShapeFiles)
        {
            Assert.IsTrue(File.Exists(Path.Combine(OutputFile, file)), $"The output file '{Path.GetFullPath(Path.Combine(OutputFile, file))}' does not exist!");
        }
    }

    [TestMethod]
    public void ExportNetworkShapefile()
    {
        SetupTest();
        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Export.export_network_shapefile",
            JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber);
                writer.WriteString("export_path", Path.GetFullPath(OutputFile));
                writer.WriteString("transit_shapes", "SEGMENTS");
            }), LogbookLevel.Standard));
        TestOutputExists();
    }

    [TestMethod]
    public void ExportNetworkShapefileModule()
    {
        SetupTest();
        var module = new TMG.Emme.Export.ExportNetworkShapefile()
        {
            ScenarioNumbers = Helper.CreateParameter(ScenarioNumber),
            SaveTo = Helper.CreateParameter(Path.GetFullPath(OutputFile)),
            TransitShapes = Helper.CreateParameter("SEGMENTS"),
        };
        module.Invoke(Helper.Modeller);
        TestOutputExists();
    }
}