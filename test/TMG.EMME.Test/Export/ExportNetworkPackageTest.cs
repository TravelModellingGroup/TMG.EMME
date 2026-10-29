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
using System.IO;


namespace TMG.Emme.Test.Export;

[TestClass]
public class ExportNetworkPackageTest : TestBase
{
    const int ScenarioNumber = 1;

    const string OutputDir = "OutputTestFiles";

    const string OutputFile = OutputDir + "/exportedNWPFriday.nwp";

    private static void SetupTest()
    {
        if (!Directory.Exists(OutputDir))
        {
            Directory.CreateDirectory(OutputDir);
        }
        else
        {
            if (File.Exists(OutputFile))
            {
                File.Delete(OutputFile);
            }
        }
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
    }

    private static void TestOutputExists()
    {
        Assert.IsTrue(File.Exists(OutputFile));
    }

    [TestMethod]
    public void ExportNetworkPackage()
    {
        SetupTest();
        
        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Export.export_network_package",
            JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteString("export_file", Path.GetFullPath(OutputFile));
                    writer.WriteNumber("scenario_number", ScenarioNumber);
                    writer.WriteString("extra_attributes", "all");
                    writer.WriteBoolean("export_all_flag", true);
                    writer.WriteString("export_meta_data", "");
                }), LogbookLevel.Standard));
        TestOutputExists();
    }

    [TestMethod]
    public void ExportNetworkPackageModule()
    {
        SetupTest();

        var module = new TMG.Emme.Export.ExportNetworkPackage()
        {
            ScenarioNumber = Helper.CreateParameter(ScenarioNumber),
            SaveTo = Helper.CreateParameter(OutputFile),
            Attributes = Helper.CreateParameter("all"),
            ExportAllFlag = Helper.CreateParameter(true),
            ExportMetaData = Helper.CreateParameter(""),
        };
        module.Invoke(Helper.Modeller);
        TestOutputExists();
    }
}

