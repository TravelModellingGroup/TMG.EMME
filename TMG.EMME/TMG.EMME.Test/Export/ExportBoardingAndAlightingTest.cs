/*
    Copyright 2022 University of Toronto

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
using System.Text;
using System.Text.Json;

namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportBoardingAndAlightingTest : TestBase
    {
        [TestMethod]
        public void ExportBoardingAndAlighting()
        {
            Helper.RunAssignTraffic(1, "mf9", 11);
            Helper.RunAssignTransit(1, "mf10");
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
            Helper.RunAssignTraffic(1, "mf9", 11);
            Helper.RunAssignTransit(1, "mf10");
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
}