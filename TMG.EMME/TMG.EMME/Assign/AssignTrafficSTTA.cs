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

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Assign
{
    [Module(Name = "Assign Demand To Road Network Using STTA Method", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class AssignTrafficSTTA : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", DefaultValue = "", Description = "The scenario number to execute against.",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Interval Lengths", DefaultValue = "true", Description = "Defines how the assignment time is split into intervals.",
            Index = 1)]
        public IFunction<float[]> IntervalLengths;

        [Parameter(Name = "Start Time", DefaultValue = "00:00", Description = "",
            Index = 2)]
        public IFunction<string> StartTime;

        [Parameter(Name = "ExtraTimeInterval", DefaultValue = "", Description = "",
            Index = 3)]
        public IFunction<float> ExtraTimeInterval;

        [Parameter(Name = "NumberOfExtraTimeIntervals", DefaultValue = "", Description = "",
            Index = 4)]
        public IFunction<int> NumberOfExtraTimeIntervals;

        [Parameter(Name = "BackgroundTraffic", DefaultValue = "", Description = "",
            Index = 5)]
        public IFunction<bool> BackgroundTraffic;

        [Parameter(Name = "Background Traffic Link Component Extra Attribute", DefaultValue = " @tvph", Description = "",
                Index = 5)]
        public IFunction<string> LinkComponentAttribute;

        [Parameter(Name = "Time Dependent Start Index for Attributes", DefaultValue = "1", Description = "Time Dependent Start Indices used to create the alphanumerical attribute name string for attributes in this class.",
            Index = 5)]
        public IFunction<int> StartIndex;

        [Parameter(Name = "Variable Topology", DefaultValue = "", Description = "",
            Index = 6)]
        public IFunction<bool> VariableTopology;

        [Parameter(Name = "Max Outer Iterations", DefaultValue = "", Description = "",
            Index = 7)]
        public IFunction<int> OuterIterations;

        [Parameter(Name = "Max Inner Iterations", DefaultValue = "", Description = "",
            Index = 7)]
        public IFunction<int> InnerIterations;


        [Parameter(Name = "Relative Gap", DefaultValue = "", Description = "",
            Index = 8)]
        public IFunction<float> rGap;

        [Parameter(Name = "Best Relative Gap", DefaultValue = "", Description = "",
            Index = 9)]
        public IFunction<float> brGap;

        [Parameter(Name = "Normalized Gap", DefaultValue = "", Description = "",
            Index = 10)]
        public IFunction<float> normGap;

        [Parameter(Name = "Performance Flag", DefaultValue = "", Description = "",
            Index = 11)]
        public IFunction<bool> PerformanceFlag;

        [Parameter(Name = "Run Title", DefaultValue = "", Description = "",
            Index = 12)]
        public IFunction<string> RunTitle;

        [Parameter(Name = "Mixed Used TTF Ranged", DefaultValue = "3-128", Description = "The TTFs where transit vehicles will occupy"
            + " some capacity on links. The ranges are inclusive.", Index = 13)]
        public IFunction<RangeSet> MixedUseTTFRanges;

        [SubModule(Name = "Traffic Classes", Description = "", Index = 14)]
        public IFunction<TrafficClass>[] TrafficClasses;

        [Module(Name = "Traffic Class", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class TrafficClass : XTMF2.IModule
        {
            [Parameter(Name = "Demand Matrix", DefaultValue = "", Description = "The id of the demand matrix to use.",
                Index = 0)]
            public IFunction<int> DemandMatrixNumber;

            [Parameter(Name = "Mode", DefaultValue = "c", Description = "The mode for this class.",
                Index = 1)]
            public IFunction<char> Mode;

            [Parameter(Name = "Time Matrix", DefaultValue = "0", Description = "The matrix number to save in vehicle travel times",
                Index = 2)]
            public IFunction<int> TimeMatrixNumber;

            [Parameter(Name = "Cost Matrix", DefaultValue = "0", Description = "The matrix number to save the total cost into.",
                Index = 3)]
            public IFunction<int> CostMatrixNumber;

            [Parameter(Name = "Toll Matrix Number", DefaultValue = "0", Description = "The matrix to save the toll costs into.",
                Index = 4)]
            public IFunction<int> TollMatrixNumber;

            [Parameter(Name = "Toll Weight", DefaultValue = "0", Description = "The toll weight",
               Index = 7)]
            public IFunction<float> TollWeight;

            [Parameter(Name = "Toll Weights", DefaultValue = "true", Description = "The toll weight",
            Index = 1)]
            public IFunction<float[]> TollWeights;

            [Parameter(Name = "OD Fixed Cost", DefaultValue = "0", Description = "",
                Index = 4)]
            public IFunction<string> ODFixedCost;

            [Parameter(Name = "Toll Attribute", DefaultValue = " @toll", Description = "The attribute containing the road tolls for this class of vehicle.",
                Index = 6)]
            public IFunction<string> LinkTollAttribute;

            [Parameter(Name = "Peak Hour Factor", DefaultValue = "1", Description = "A factor to apply to the demand in order to build"
                + "a representative hour.",
                Index = 4)]
            public IFunction<float> PeakHourFactor;

            [Parameter(Name = "Volume Attribute", DefaultValue = " @auto_volume", Description = "The name of the attribute to save the volumes into"
                + "(or None for no saving).",
                Index = 5)]
            public IFunction<string> VolumeAttribute;

            [Parameter(Name = "Time Dependent Start Index for Attributes in this Class", DefaultValue = "1", Description = "Time Dependent Start Indices used to create "
                + "the alphanumerical attribute name string for attributes in this class. e.g. if 1 is specified, "
                + "then @auto_volume1, @auto_volume2 etc are created depending on the number of time period intervals).",
                Index = 5)]
            public IFunction<int> AttributeStartIndex;

            [Parameter(Name = "Link Cost", DefaultValue = "0", Description = "The penalty in minutes per dollar to apply when traversing a link.",
                Index = 8)]
            public IFunction<float> LinkCost;

            [SubModule(Name = "Path Analysis", Description = "", Index = 9, Required = false)]
            public IFunction<PathAnalysis>[] PathAnalyses;

            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("name", Name);
                writer.WriteString("mode", Mode.Invoke().ToString());
                writer.WriteNumber("demand_matrix_number", DemandMatrixNumber.Invoke());
                writer.WriteNumber("time_matrix_number", TimeMatrixNumber.Invoke());
                writer.WriteNumber("cost_matrix_number", CostMatrixNumber.Invoke());
                writer.WriteNumber("toll_matrix_number", TollMatrixNumber.Invoke());
                writer.WriteString("od_fixed_cost", ODFixedCost.Invoke());
                writer.WriteString("volume_attribute", VolumeAttribute.Invoke());
                writer.WriteNumber("attribute_start_index", AttributeStartIndex.Invoke());
                writer.WriteNumber("link_cost", LinkCost.Invoke());
                writer.WriteString("link_toll_attribute", LinkTollAttribute.Invoke());
                writer.WriteStartArray("toll_weights");
                foreach (var toll_weight in TollWeights.Invoke())
                {
                    writer.WriteNumberValue(toll_weight);
                }
                writer.WriteEndArray();
                writer.WritePropertyName("interval_length_list");

                writer.WriteStartArray("path_analyses");
                foreach (var pathAnalysis in PathAnalyses)
                {
                    pathAnalysis.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
                writer.WriteEndObject();
            }
        }

        [Module(Name = "Path Analysis", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class PathAnalysis : XTMF2.IModule
        {
            [Parameter(Name = "Attribute ID", DefaultValue = "0", Description = "The attribute to use for analysis",
                Index = 0)]
            public IFunction<string> AttributeId;


            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteEndObject();
            }
        }

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Assign.assign_traffic_stta", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());

                writer.WriteString("start_time", StartTime.Invoke());
                writer.WriteNumber("extra_time_interval", ExtraTimeInterval.Invoke());
                writer.WriteNumber("number_of_extra_time_intervals", NumberOfExtraTimeIntervals.Invoke());
                writer.WriteBoolean("background_traffic", BackgroundTraffic.Invoke());
                writer.WriteString("link_component_attribute", LinkComponentAttribute.Invoke());
                writer.WriteNumber("start_index", StartIndex.Invoke());
                writer.WriteBoolean("variable_topology", VariableTopology.Invoke());
                writer.WriteNumber("max_outer_iterations", OuterIterations.Invoke());
                writer.WriteNumber("max_inner_iterations", InnerIterations.Invoke());
                writer.WriteNumber("r_gap", rGap.Invoke());
                writer.WriteNumber("br_gap", brGap.Invoke());
                writer.WriteNumber("norm_gap", normGap.Invoke());
                writer.WriteBoolean("performance_flag", PerformanceFlag.Invoke());
                writer.WriteString("run_title", RunTitle.Invoke());
                writer.WritePropertyName("interval_length_list");
                writer.WriteStartArray();
                foreach (var interval in IntervalLengths.Invoke())
                {
                    writer.WriteNumberValue(interval);
                }
                writer.WriteEndArray();
                writer.WritePropertyName("mixed_use_ttf_ranges");
                writer.WriteStartArray();
                foreach (var range in MixedUseTTFRanges.Invoke())
                {
                    writer.WriteStartObject();
                    writer.WriteNumber("start", range.Start);
                    writer.WriteNumber("stop", range.Stop);
                    writer.WriteEndObject();
                }
                writer.WriteEndArray();


                writer.WriteStartArray("traffic_classes");
                foreach (var trafficClass in TrafficClasses)
                {
                    trafficClass.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
            }), LogbookLevel.Standard);
        }

    }
}
