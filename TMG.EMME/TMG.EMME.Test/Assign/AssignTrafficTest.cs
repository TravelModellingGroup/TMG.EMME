/*
    Copyright 2021 University of Toronto

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
    public class AssignTrafficTest : TestBase
    {
        [TestMethod]
        public void AssignTraffic()
        {
            Helper.ImportFrabitztownNetwork(1);
            Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_traffic",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteString("background_transit", "true");
                    writer.WriteNumber("br_gap", 0);
                    writer.WriteNumber("iterations", 100);
                    writer.WriteNumber("norm_gap", 0);
                    writer.WriteBoolean("performance_flag", true);
                    writer.WriteNumber("r_gap", 0);
                    writer.WriteString("run_title", "road assignment");
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteBoolean("sola_flag", true);

                    writer.WriteStartArray("traffic_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "traffic class 1");
                    writer.WriteString("mode", "c");
                    writer.WriteString("demand_matrix", "mf1");
                    writer.WriteString("time_matrix", "mf0");
                    writer.WriteString("cost_matrix", "mf4");
                    writer.WriteString("toll_matrix", "mf0");
                    writer.WriteNumber("peak_hour_factor", 1);
                    writer.WriteString("volume_attribute", "@auto_volume1");
                    writer.WriteString("link_toll_attribute_id", " @toll");
                    writer.WriteNumber("toll_weight", 0.0);
                    writer.WriteNumber("link_cost", 0.0);
                    writer.WriteStartArray("path_analyses");
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void AssignTrafficModule()
        {
            Helper.ImportFrabitztownNetwork(1);
            Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));

            var trafficClasses = new[]
            {
                new Emme.Assign.AssignTraffic.TrafficClass()
                {
                    Name = "traffic class 1",
                    Mode = Helper.CreateParameter('c'),
                    DemandMatrixNumber = Helper.CreateParameter("mf1"),
                    TimeMatrix = Helper.CreateParameter("mf0"),
                    CostMatrix = Helper.CreateParameter("mf4"),
                    TollMatrix = Helper.CreateParameter("mf0"),
                    PeakHourFactor = Helper.CreateParameter(1f),
                    VolumeAttribute = Helper.CreateParameter("@auto_volume1"),
                    LinkTollAttributeID = Helper.CreateParameter("@toll"),
                    TollWeight = Helper.CreateParameter(0.0f),
                    LinkCost = Helper.CreateParameter(0.0f),
                    PathAnalyses = Array.Empty<IFunction<Emme.Assign.AssignTraffic.PathAnalysis>>()
                }
            };

            var module = new Emme.Assign.AssignTraffic()
            {
                Name = "AssignTraffic",
                BackgroundTransit = Helper.CreateParameter("true"),
                brGap = Helper.CreateParameter(0f),
                Iterations = Helper.CreateParameter(100),
                normGap = Helper.CreateParameter(0f),
                PerformanceFlag = Helper.CreateParameter(true),
                rGap = Helper.CreateParameter(0f),
                RunTitle = Helper.CreateParameter("road assignment"),
                ScenarioNumber = Helper.CreateParameter(1),
                SOLAFlag = Helper.CreateParameter(true),
                TrafficClasses = Helper.CreateParameters(trafficClasses),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}