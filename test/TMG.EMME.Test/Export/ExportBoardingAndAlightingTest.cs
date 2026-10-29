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
using System.Runtime.CompilerServices;
using static System.Net.Mime.MediaTypeNames;

namespace TMG.Emme.Test.Export;

[TestClass]
public class ExportBoardingAndAlightingTest : TestBase
{
    const int ScenarioNumber = 1;

    private static void SetupTest([CallerMemberName] string testName = "")
    {
        if (!Directory.Exists("OutputTestFiles"))
        {
            Directory.CreateDirectory("OutputTestFiles");
        }
        else
        {
            if (File.Exists("OutputTestFiles/board_alight_at_stops.csv"))
            {
                File.Delete("OutputTestFiles/board_alight_at_stops.csv");
            }
        }
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
        Helper.ImportBinaryMatrix(ScenarioNumber, 10, Path.GetFullPath("TestFiles/Test0.25.mtx"));
        Helper.RunAssignTraffic(ScenarioNumber, "mf10", 11);
        Helper.ImportBinaryMatrix(ScenarioNumber, 10, Path.GetFullPath("TestFiles/Test0.25.mtx"));
        Helper.RunAssignBoardingPenalty([ScenarioNumber]);
        Helper.RunAssignTransit(ScenarioNumber, "mf10");
    }

    [TestMethod]
    public void ExportBoardingAndAlighting()
    {
        SetupTest();
        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Export.export_boarding_and_alighting",
             JSONParameterBuilder.BuildParameters(writer =>
             {
                 writer.WriteNumber("scenario_number", 1);
                 writer.WriteString("input_file", Path.GetFullPath("TestFiles/inputs.csv"));
                 writer.WriteString("export_file", Path.GetFullPath("OutputTestFiles/board_alight_at_stops.csv"));
                 writer.WriteBoolean("write_to_file", false);
             }), LogbookLevel.Standard));
    }

    [TestMethod]
    public void ExportBoardingAndAlightingModule()
    {
        SetupTest();
        var module = new Emme.Export.ExportBoardingAndAlighting()
        {
            Name = "ExportBoardingAndAlighting",
            ScenarioNumber = Helper.CreateParameter(1),
            FileLocation = Helper.CreateParameter(Path.GetFullPath("TestFiles/inputs.csv"), "Transit Stop File Name"),
            SaveTo = Helper.CreateParameter("OutputTestFiles/board_alight_at_stops.csv"),
            WriteToFile = Helper.CreateParameter(false)
        };
        module.Invoke(Helper.Modeller);
    }
}