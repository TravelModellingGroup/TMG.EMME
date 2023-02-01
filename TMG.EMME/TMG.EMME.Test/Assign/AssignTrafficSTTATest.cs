/*
    Copyright 2023 University of Toronto

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

namespace TMG.Emme.Test.Assign
{
    [TestClass]
    public class AssignTrafficSTTATest : TestBase
    {
        [TestMethod]
        public void AssignTrafficSTTA()
        {
            var scenarioNumber = 2;
            Helper.ImportFrabitztownNetwork(scenarioNumber);

            Helper.ImportBinaryMatrix(scenarioNumber, 1, Path.GetFullPath("TestFiles/Test.mtx"));
            Helper.ImportBinaryMatrix(scenarioNumber, 2, Path.GetFullPath("TestFiles/Test.mtx"));
            Helper.ImportBinaryMatrix(scenarioNumber, 3, Path.GetFullPath("TestFiles/Test.mtx"));
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_traffic_stta",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WritePropertyName("interval_length_list");
                    writer.WriteStartArray();
                    writer.WriteNumberValue(300);
                    writer.WriteNumberValue(60);
                    writer.WriteNumberValue(60);
                    writer.WriteEndArray();
                    writer.WriteString("start_time", "00:00");
                    writer.WriteNumber("extra_time_interval", 60);
                    writer.WriteNumber("number_of_extra_time_intervals", 2);
                    writer.WriteBoolean("background_traffic", false);
                    writer.WriteString("link_component_attribute", "@tvph");
                    writer.WriteNumber("start_index", 1);
                    writer.WriteBoolean("variable_topology", false);
                    writer.WriteNumber("iterations", 10);
                    writer.WriteNumber("r_gap", 0);
                    writer.WriteNumber("br_gap", 0);
                    writer.WriteNumber("norm_gap", 0);
                    writer.WriteBoolean("performance_flag", true);
                    writer.WriteString("run_title", "run1");
                    writer.WritePropertyName("mixed_use_ttf_ranges");
                    writer.WriteStartArray();
                    writer.WriteStartObject();
                    writer.WriteNumber("start", 3);
                    writer.WriteNumber("stop", 128);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("traffic_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "traffic class 1");
                    writer.WriteString("mode", "c");
                    writer.WriteNumber("demand_matrix_number", 1000);
                    writer.WriteNumber("time_matrix_number", 10);
                    writer.WriteNumber("cost_matrix_number", 0);
                    writer.WriteNumber("toll_matrix_number", 0);
                    writer.WritePropertyName("toll_weight_list");
                    writer.WriteStartArray();
                    writer.WriteNumberValue(1);
                    writer.WriteNumberValue(2);
                    writer.WriteNumberValue(3);
                    writer.WriteEndArray();
                    writer.WriteString("link_toll_attribute", "@toll");
                    writer.WriteString("volume_attribute", "@auto_volume");
                    writer.WriteNumber("attribute_start_index", 1);
                    writer.WriteNumber("link_cost", 0.0);
                    writer.WriteStartArray("path_analyses");
                    writer.WriteStartObject();
                    writer.WriteString("attribute_id", "1");
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();

                }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void AssignTrafficSTTAModule()
        {
            Helper.ImportFrabitztownNetwork(1);
            Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));

            var pathAnalyses = new[]
            {
                new Emme.Assign.AssignTrafficSTTA.PathAnalysis()
                {
                    Name = "PathAnalysis",
                    AttributeId = Helper.CreateParameter("1"),
                }
            };

            var trafficClasses = new[]
            {
                new Emme.Assign.AssignTrafficSTTA.TrafficClass()
                {
                    Name = "TrafficClass1",
                    Mode = Helper.CreateParameter('c'),
                    DemandMatrixNumber = Helper.CreateParameter(10),
                }
            };
            var module = new Emme.Assign.AssignTrafficSTTA()
            {
                Name = "AssignTrafficSTTA",
                ScenarioNumber = Helper.CreateParameter(1),
                TrafficClasses = Helper.CreateParameters(trafficClasses),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
