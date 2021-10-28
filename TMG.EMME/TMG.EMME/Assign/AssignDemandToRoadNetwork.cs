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

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Assign
{
    [Module(Name = "Assign Demand To Road Network", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class AssignDemandToRoadNetwork : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Link Toll Attribute Id", Description = "",
            Index = 1)]
        public IFunction<string> LinkTollAttributeId;

        [Parameter(Name = "Times Matrix Id", Description = "",
            Index = 2)]
        public IFunction<string> TimesMatrixId;

        [Parameter(Name = "Cost Matrix Id", Description = "",
            Index = 3)]
        public IFunction<string> CostMatrixId;

        [Parameter(Name = "Tolls Matrix Id", Description = "",
            Index = 4)]
        public IFunction<string> TollsMatrixId;

        [Parameter(Name = "Run Title", Description = "",
            Index = 5)]
        public IFunction<string> RunTitle;

        [Parameter(Name = "Mode List ", Description = "",
            Index = 6)]
        public IFunction<string> ModeList;

        [Parameter(Name = "Demand String", Description = "",
            Index = 7)]
        public IFunction<string> DemandString;

        [Parameter(Name = "Peak Hour Factor", Description = "",
            Index = 9)]
        public IFunction<float> PeakHourFactor;

        [Parameter(Name = "Link Cost", Description = "",
            Index = 10)]
        public IFunction<string> LinkCost;

        [Parameter(Name = "Toll Weight", Description = "",
            Index = 11)]
        public IFunction<string> TollWeight;

        [Parameter(Name = "Iterations", Description = "",
            Index = 12)]
        public IFunction<int> Iterations;

        [Parameter(Name = "r Gap", Description = "",
            Index = 13)]
        public IFunction<float> rGap;

        [Parameter(Name = "br Gap", Description = "",
            Index = 14)]
        public IFunction<float> brGap;

        [Parameter(Name = "norm Gap", Description = "",
            Index = 15)]
        public IFunction<float> normGap;

        [Parameter(Name = "Performance Flag", Description = "",
            Index = 16)]
        public IFunction<bool> PerformanceFlag;

        [Parameter(Name = "SOLA Flag", Description = "",
            Index = 17)]
        public IFunction<bool> SOLAFlag;

        [Parameter(Name = "Name String", Description = "",
            Index = 18)]
        public IFunction<string> NameString;

        [Parameter(Name = "Result Attributes", Description = "",
            Index = 19)]
        public IFunction<string> ResultAttributes;

        [Parameter(Name = "Analysis Attributes", Description = "",
            Index = 20)]
        public IFunction<string> AnalysisAttributes;

        [Parameter(Name = "Analysis Attributes Matrix Id", Description = "",
            Index = 21)]
        public IFunction<string> AnalysisAttributesMatrixId;

        [Parameter(Name = "Aggregation Operator", Description = "",
            Index = 22)]
        public IFunction<string> AggregationOperator;

        [Parameter(Name = "Lower Bound", Description = "",
            Index = 23)]
        public IFunction<string> LowerBound;

        [Parameter(Name = "Upper Bound", Description = "",
            Index = 24)]
        public IFunction<string> UpperBound;

        [Parameter(Name = "Path Selection", Description = "",
            Index = 25)]
        public IFunction<string> PathSelection;

        [Parameter(Name = "Multiply Path Prop By Demand", Description = "",
            Index = 26)]
        public IFunction<string> MultiplyPathPropByDemand;

        [Parameter(Name = "Multiply Path Prop By Value", Description = "",
            Index = 27)]
        public IFunction<string> MultiplyPathPropByValue;

        [Parameter(Name = "Background Transit", Description = "",
            Index = 28)]
        public IFunction<string> BackgroundTransit;

        [SubModule(Name = "", Description = "" , Index = 0)]
        public IFunction<Class>[] Classes;

        public class Class : XTMF2.IModule
        {
            [Parameter(Name = "Mode", DefaultValue = "c", Description = "The mode for this class.", Index = 0)]
            public IFunction<char> Mode;

            [Parameter(Name = "Demand Matrix", DefaultValue = "0", Description = "The id of the demand matrix to use.", Index = 0)]
            public IFunction<int> DemandMatrixNumber;

            [Parameter(Name = "Time Matrix", DefaultValue = "0", Description = "The matrix number to save in vehicle travel times", Index = 0)]
            public IFunction<int> TimeMatrix;

            [Parameter(Name = "Cost Matrix", DefaultValue = "0", Description = "The matrix number to save the total cost into.", Index = 0)]
            public IFunction<int> CostMatrix;

            [Parameter(Name = "Toll Matrix", DefaultValue = "0", Description = "The matrix to save the toll costs into.", Index = 0)]
            public IFunction<int> TollMatrix;

            [Parameter(Name = "VolumeAttribute", DefaultValue = "@auto_volume1", Description = "The name of the attribute to save the volumes into (or None for no saving).", Index = 0)]
            public IFunction<string> VolumeAttribute;

            [Parameter(Name = "TollAttributeID", DefaultValue = "@toll", Description = "The attribute containing the road tolls for this class of vehicle.", Index = 0)]
            public IFunction<string> LinkTollAttributeID;

            [Parameter(Name = "Toll Weight", DefaultValue = "0", Description = "", Index = 0)]
            public IFunction<float> TollWeight;

            [Parameter(Name = "LinkCost", DefaultValue = "0", Description = "The penalty in minutes per dollar to apply when traversing a link.", Index = 0)]
            public IFunction<float> LinkCost;

            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("mode", Mode.Invoke().ToString());
                writer.WriteNumber("demand_matrix", DemandMatrixNumber.Invoke());
                writer.WriteNumber("time_matrix", TimeMatrix.Invoke());
                writer.WriteNumber("cost_matrix", CostMatrix.Invoke());
                writer.WriteNumber("toll_matrix", TollMatrix.Invoke());
                writer.WriteString("volume_attribute", VolumeAttribute.Invoke());
                writer.WriteString("toll_attribute_id", LinkTollAttributeID.Invoke());
                writer.WriteNumber("toll_weight", TollWeight.Invoke());
                writer.WriteNumber("link_cost", LinkCost.Invoke());
                writer.WriteEndObject();
            }
        }
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Assign.assign_demand_to_road_network", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteString("link_toll_attribute_id", LinkTollAttributeId.Invoke());
                writer.WriteString("times_matrix_id", TimesMatrixId.Invoke());
                writer.WriteString("cost_matrix_id", CostMatrixId.Invoke());
                writer.WriteString("tolls_matrix_id", TollsMatrixId.Invoke());
                writer.WriteString("run_title", RunTitle.Invoke());
                writer.WriteString("mode_list", ModeList.Invoke());
                writer.WriteString("demand_string", DemandString.Invoke());
                writer.WriteNumber("peak_hour_factor", PeakHourFactor.Invoke());
                writer.WriteString("link_cost", LinkCost.Invoke());
                writer.WriteString("toll_weight", TollWeight.Invoke());
                writer.WriteNumber("iterations", Iterations.Invoke());
                writer.WriteNumber("r_gap", rGap.Invoke());
                writer.WriteNumber("br_gap", brGap.Invoke());
                writer.WriteNumber("norm_gap", normGap.Invoke());
                writer.WriteBoolean("performance_flag", PerformanceFlag.Invoke());
                writer.WriteBoolean("sola_flag", SOLAFlag.Invoke());
                writer.WriteString("name_string", NameString.Invoke());
                writer.WriteString("result_attributes", ResultAttributes.Invoke());
                writer.WriteString("analysis_attributes", AnalysisAttributes.Invoke());
                writer.WriteString("analysis_attributes_matrix_id", AnalysisAttributesMatrixId.Invoke());
                writer.WriteString("aggregation_operator", AggregationOperator.Invoke());
                writer.WriteString("lower_bound", LowerBound.Invoke());
                writer.WriteString("upper_bound", UpperBound.Invoke());
                writer.WriteString("path_selection", PathSelection.Invoke());
                writer.WriteString("multiply_path_prop_by_demand", MultiplyPathPropByDemand.Invoke());
                writer.WriteString("multiply_path_prop_by_value", MultiplyPathPropByValue.Invoke());
                writer.WriteString("background_transit", BackgroundTransit.Invoke());
            }), LogbookLevel.Standard);
        }
    }
}