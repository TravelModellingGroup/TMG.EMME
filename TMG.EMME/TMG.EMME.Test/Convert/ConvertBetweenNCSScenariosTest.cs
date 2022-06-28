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
using System.Collections.Generic;
using System.Text;
using System.IO;
using XTMF2;

namespace TMG.Emme.Test.Convert
{
    [TestClass]
    public class ConvertBetweenNCSScenariosTest : TestBase
    {
        [TestMethod]
        public void ConvertBetweenNCSScenarios()
        {
            const int scenarioNumber = 1;
            Helper.ImportNetwork(scenarioNumber, "TestFiles/test.nwp");
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Convert.convert_between_ncs_scenarios",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("old_ncs_scenario", scenarioNumber);
                    writer.WriteNumber("new_ncs_scenario", 2);
                    writer.WriteString("station_centroid_file", "TestFiles/station_centriods.csv");
                    writer.WriteString("zone_centroid_file", "TestFiles/zone_centriods.csv");
                    writer.WriteString("mode_code_definitions", "TestFiles/mode_code_definitions.csv");
                    writer.WriteString("link_attributes", "TestFiles/link_attributes.csv");
                    writer.WriteString("transit_vehicle_definitions", "TestFiles/transit_vehicles.csv");
                    writer.WriteString("lane_capacities", "TestFiles/lane_capacities.csv");
                    writer.WriteString("transit_line_codes", "TestFiles/transit_line_codes.csv");
                    writer.WriteBoolean("skip_missing_transit_lines", false);
                }), LogbookLevel.Standard));
            Helper.ExportNetwork(scenarioNumber, "TestFiles/ncs_test.nwp");
        }


        [TestMethod]
        public void ConvertBetweenNCSScenariosModule()
        {
            const int scenarioNumber = 1;
            Helper.ImportNetwork(scenarioNumber, "TestFiles/base_network.nwp");
            var module = new Emme.Convert.ConvertBetweenNCSScenarios()
            {
                OldScenarioNumber = Helper.CreateParameter(scenarioNumber),
                NewScenarioNumber = Helper.CreateParameter(2),
                StationCentroidFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/station_centriods.csv")),
                ZoneCentroidFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/zone_centriods.csv")),
                LinkAttributes = Helper.CreateParameter(Path.GetFullPath("TestFiles/link_attributes.csv")),
                TransitVehicleFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/transit_vehicles.csv")),
                LaneCapacityFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/lane_capacities.csv")),
                TransitLineFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/transit_line_codes.csv")),
                SkipMissingTransitLines = Helper.CreateParameter(false)
            };
            module.Invoke(Helper.Modeller);
        }
    }
}

