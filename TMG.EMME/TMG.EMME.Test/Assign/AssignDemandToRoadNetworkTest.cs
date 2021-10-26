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
    public class AssignDemandToRoadNetworkTest : TestBase
    {
        [TestMethod]
        public void AssignBoardingPenalty()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_demand_to_road_network",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteString("link_toll_attribute_id", "@toll");
                    writer.WriteString("times_matrix_id", "mf0");
                    writer.WriteString("cost_matrix_id", "");
                    writer.WriteString("tolls_matrix_id", "");
                    writer.WriteString("run_title", "multi -class run");
                    writer.WriteString("mode_list", "c");
                    writer.WriteString("demand_string", "mf10,mf11,f12");
                    writer.WriteString("demand_list", "mf10,mf11,f12");
                    writer.WriteNumber("peak_hour_factor", 0.43f);
                    writer.WriteString("link_cost", "");
                    writer.WriteString("toll_weight", "");
                    writer.WriteNumber("iterations", 100);
                    writer.WriteNumber("r_gap", 0.0f);
                    writer.WriteNumber("br_gap", 0.1f);
                    writer.WriteNumber("norm_gap", 0.05f);
                    writer.WriteBoolean("performance_flag", false);
                    writer.WriteBoolean("sola_flag", true);
                    writer.WriteString("name_string", "");
                    writer.WriteString("result_attributes", "");
                    writer.WriteString("analysis_attributes", "");
                    writer.WriteString("analysis_attributes_matrix_id", "");
                    writer.WriteString("aggregation_operator", "+");
                    writer.WriteString("lower_bound", "none");
                    writer.WriteString("upper_bound", "");
                    writer.WriteString("path_selection", "");
                    writer.WriteString("multiply_path_prop_by_demand", "true");
                    writer.WriteString("multiply_path_prop_by_value", "");
                    writer.WriteString("background_transit", "true");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void AssignDemandToRoadNetworkModule()
        {

            var module = new Emme.Assign.AssignDemandToRoadNetwork()
            {
                Name = "AssignDemandToRoadNetwork",
                ScenarioNumber = Helper.CreateParameter(1),
                LinkTollAttributeId = Helper.CreateParameter("@toll"),
                TimesMatrixId = Helper.CreateParameter("mf0"),
                CostMatrixId = Helper.CreateParameter(""),
                TollsMatrixId = Helper.CreateParameter(""),
                RunTitle = Helper.CreateParameter("multi-class run"),
                ModeList = Helper.CreateParameter("c"),
                DemandString = Helper.CreateParameter("mf10,mf11,f12"),
                DemandList = Helper.CreateParameter("mf10,mf11,f12"),
                PeakHourFactor = Helper.CreateParameter(0.43f),
                LinkCost = Helper.CreateParameter(""),
                TollWeight = Helper.CreateParameter(""),
                Iterations = Helper.CreateParameter(100),
                rGap = Helper.CreateParameter(0.0f),
                brGap = Helper.CreateParameter(0.1f),
                normGap = Helper.CreateParameter(0.05f),
                PerformanceFlag = Helper.CreateParameter(false),
                SOLAFlag = Helper.CreateParameter(true),
                NameString = Helper.CreateParameter(""),
                ResultAttributes = Helper.CreateParameter(""),
                AnalysisAttributes = Helper.CreateParameter(""),
                AnalysisAttributesMatrixId = Helper.CreateParameter(""),
                AggregationOperator = Helper.CreateParameter("+"),
                LowerBound = Helper.CreateParameter("none"),
                UpperBound = Helper.CreateParameter(""),
                PathSelection = Helper.CreateParameter(""),
                MultiplyPathPropByDemand = Helper.CreateParameter("true"),
                MultiplyPathPropByValue = Helper.CreateParameter(""),
                BackgroundTransit = Helper.CreateParameter("true")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}