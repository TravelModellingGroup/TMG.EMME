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

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Export
{
    [Module(Name = "Export Subarea", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ExportSubarea : BaseAction<ModellerController>
    {
        [Parameter(Name = "I Subarea Link Selection", Description = "The outgoing connectors used to tag the centroids within the subarea. results are stored in the gate link attribute specified eg. \"i=21,24 or i=27 or i=31,34\"",
            Index = 0)]
        public IFunction<string> ISubareaLinkSelection;
        [Parameter(Name = "J Subarea Link Selection", Description = "The incoming connectors used to tag the centroids within the subarea. results are stored in the gate link attribute specified eg. \"j=21,24 or j=27 or j=31,34\"",
            Index = 1)]
        public IFunction<string> JSubareaLinkSelection;

        [Parameter(Name = "Scenario Number", Description = "The scenario number to execute against",
            Index = 2)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Shapefile Location", Description = "The shapefile name containing the boundary of the subarea polygon",
            Index = 3)]
        public IFunction<string> ShapefileLocation;

        [Parameter(Name = "Create Nflag From Shapefile", Description = "set to False if subarea node attribute is already defined in the network",
            Index = 4)]
        public IFunction<bool> CreateNflagFromShapefile;

        [Parameter(Name = "Subarea Node Attribute", Description = "The node attribute that will be used to define the subarea.",
            Index = 5)]
        public IFunction<string> SubareaNodeAttribute;

        [Parameter(Name = "Subarea Gate Attribute", Description = "The link extra attribute that defines your gate numbers",
            Index = 6)]
        public IFunction<string> SubareaGateAttribute;

        [Parameter(Name = "Subarea Output Folder", Description = "Folder directory to write output of the subarea database",
            Index = 7)]
        public IFunction<string> SubareaOutputFolder;

        [Parameter(Name = "Background Transit", DefaultValue = "true", Description = "Set this to false to not assign transit vehicles on the roads",
            Index = 8)]
        public IFunction<bool> BackgroundTransit;

        [Parameter(Name = "br Gap", DefaultValue = "0", Description = "The minimum gap required to terminate the algorithm.",
            Index = 9)]
        public IFunction<float> brGap;

        [Parameter(Name = "Iterations", DefaultValue = "100", Description = "The maximum number of iterations to run.",
            Index = 10)]
        public IFunction<int> Iterations;

        [Parameter(Name = "norm Gap", DefaultValue = "0", Description = "The minimum gap required to terminate the algorithm.",
            Index = 11)]
        public IFunction<float> normGap;

        [Parameter(Name = "Performance Flag", DefaultValue = "true", Description = "Set this to false to leave a free core for other work",
            Index = 12)]
        public IFunction<bool> PerformanceFlag;

        [Parameter(Name = "r Gap", DefaultValue = "0", Description = "The minimum gap required to terminate the algorithm.",
            Index = 13)]
        public IFunction<float> rGap;

        [Parameter(Name = "Run Title", DefaultValue = "road assignment", Description = "The name of the run to appear in the logbook.",
            Index = 14)]
        public IFunction<string> RunTitle;

        [Parameter(Name = "SOLA Flag", DefaultValue = "true", Description = "Sola flag",
            Index = 15)]
        public IFunction<bool> SOLAFlag;

        [Parameter(Name = "Mixed Used TTF Ranged", DefaultValue = "3-128", Description = "The TTFs where transit vehicles will occupy some capacity on links. The ranges are inclusive.",
            Index = 16)]
        public IFunction<RangeSet> MixedUseTTFRanges;

        [Parameter(Name = "ExtractTransit", DefaultValue = "true", Description = "Set this to TRUE to export the subarea transit",
                Index = 17)]
        public IFunction<bool> ExtractTransit;

        [Parameter(Name = "Create Gate Attribute", DefaultValue = "false", Description = "Set this to TRUE to create gate labels for your network. NOTE: i & j link selections must be defined",
               Index = 18)]
        public IFunction<bool> CreateGateAttribute;

        [SubModule(Name = "Traffic Classes", Description = "Traffic classes", Index = 19)]
        public IFunction<TrafficClass>[] TrafficClasses;

        [Module(Name = "Traffic Class", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class TrafficClass : XTMF2.IModule
        {
            [Parameter(Name = "Mode", DefaultValue = "c", Description = "The mode for this class.",
                Index = 0)]
            public IFunction<char> Mode;

            [Parameter(Name = "Demand Matrix", DefaultValue = "0", Description = "The id of the demand matrix to use.",
                Index = 1)]
            public IFunction<string> DemandMatrixNumber;

            [Parameter(Name = "Time Matrix", DefaultValue = "0", Description = "The matrix number to save in vehicle travel times",
                Index = 2)]
            public IFunction<string> TimeMatrix;

            [Parameter(Name = "Cost Matrix", DefaultValue = "0", Description = "The matrix number to save the total cost into.",
                Index = 3)]
            public IFunction<string> CostMatrix;

            [Parameter(Name = "Toll Matrix", DefaultValue = "0", Description = "The matrix to save the toll costs into.",
                Index = 4)]
            public IFunction<string> TollMatrix;

            [Parameter(Name = "Peak Hour Factor", DefaultValue = "1", Description = "A factor to apply to the demand in order to build a representative hour.",
            Index = 4)]
            public IFunction<float> PeakHourFactor;

            [Parameter(Name = "Volume Attribute", DefaultValue = " @auto_volume1", Description = "The name of the attribute to save the volumes into (or None for no saving).",
                Index = 5)]
            public IFunction<string> VolumeAttribute;

            [Parameter(Name = "Toll Attribute", DefaultValue = " @toll", Description = "The attribute containing the road tolls for this class of vehicle.",
                Index = 6)]
            public IFunction<string> LinkTollAttribute;

            [Parameter(Name = "Toll Weight", DefaultValue = "0", Description = "The toll weight",
                Index = 7)]
            public IFunction<float> TollWeight;

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
                writer.WriteString("demand_matrix", DemandMatrixNumber.Invoke());
                writer.WriteString("time_matrix", TimeMatrix.Invoke());
                writer.WriteString("cost_matrix", CostMatrix.Invoke());
                writer.WriteString("toll_matrix", TollMatrix.Invoke());
                writer.WriteNumber("peak_hour_factor", PeakHourFactor.Invoke());
                writer.WriteString("volume_attribute", VolumeAttribute.Invoke());
                writer.WriteString("link_toll_attribute", LinkTollAttribute.Invoke());
                writer.WriteNumber("toll_weight", TollWeight.Invoke());
                writer.WriteNumber("link_cost", LinkCost.Invoke());
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

            [Parameter(Name = "Aggregation Matrix", DefaultValue = "0", Description = "The matrix number to store the results into",
                Index = 1)]
            public IFunction<string> AggregationMatrix;

            [Parameter(Name = "Operator", DefaultValue = "+", Description = "The operator to use to aggregate the matrix. Example:'+' for emissions",
                Index = 2)]
            public IFunction<string> AggregationOperator;

            [Parameter(Name = "Lower Bound for Path Selector", DefaultValue = "None", Description = "Lower Bound for Path Selector None The number to use for the lower bound in path selection",
                Index = 3)]
            public IFunction<string> LowerBound;

            [Parameter(Name = "Upper Bound for Path Selector", DefaultValue = "None", Description = "Upper Bound for Path Selector None The number to use for the upper bound in path selection",
                Index = 4)]
            public IFunction<string> UpperBound;

            [Parameter(Name = "Path Selection", DefaultValue = "ALL", Description = "The paths that will be used for analysis",
                Index = 5)]
            public IFunction<string> PathSelection;

            [Parameter(Name = "Multiply Path Prop By Demand", DefaultValue = "true", Description = "Choose whether to multiply the path proportion by the analyzed demand",
                Index = 6)]
            public IFunction<string> MultiplyPathPropByDemand;

            [Parameter(Name = "Multiply Path Prop By Value", DefaultValue = "true", Description = "Choose whether to multiply the path proportion by the path value",
                Index = 7)]
            public IFunction<string> MultiplyPathPropByValue;

            [Parameter(Name = "Analysis Attributes", DefaultValue = "@auto_volume", Description = "The analysis attributes",
                Index = 8)]
            public IFunction<string> AnalysisAttributes;

            [Parameter(Name = "Analysis Attributes Matrix Id", DefaultValue = "0", Description = "The matrix number to store the results into",
                Index = 21)]
            public IFunction<string> AnalysisAttributesMatrixId;

            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("attribute_id", AttributeId.Invoke());
                writer.WriteString("aggregation_matrix", AggregationMatrix.Invoke());
                writer.WriteString("aggregation_operator", AggregationOperator.Invoke());
                writer.WriteString("lower_bound", LowerBound.Invoke());
                writer.WriteString("upper_bound", UpperBound.Invoke());
                writer.WriteString("path_selection", PathSelection.Invoke());
                writer.WriteString("multiply_path_prop_by_demand", MultiplyPathPropByDemand.Invoke());
                writer.WriteString("multiply_path_prop_by_value", MultiplyPathPropByValue.Invoke());
                writer.WriteString("analysis_attributes", AnalysisAttributes.Invoke());
                writer.WriteString("analysis_attributes_matrix", AnalysisAttributesMatrixId.Invoke());
                writer.WriteEndObject();
            }
        }


        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Export.export_subarea", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteBoolean("extract_transit", ExtractTransit.Invoke());
                writer.WriteBoolean("create_gate_attribute", CreateGateAttribute.Invoke());
                writer.WriteString("i_subarea_link_selection", ISubareaLinkSelection.Invoke());
                writer.WriteString("j_subarea_link_selection", JSubareaLinkSelection.Invoke());
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteString("shape_file_location", ShapefileLocation.Invoke());
                writer.WriteBoolean("create_nflag_from_shapefile", CreateNflagFromShapefile.Invoke());
                writer.WriteString("subarea_output_folder", SubareaOutputFolder.Invoke());
                writer.WriteString("subarea_node_attribute", SubareaNodeAttribute.Invoke());
                writer.WriteString("subarea_gate_attribute", SubareaGateAttribute.Invoke());
                writer.WriteNumber("iterations", Iterations.Invoke());
                writer.WriteNumber("r_gap", rGap.Invoke());
                writer.WriteNumber("br_gap", brGap.Invoke());
                writer.WriteNumber("norm_gap", normGap.Invoke());
                writer.WriteBoolean("performance_flag", PerformanceFlag.Invoke());
                writer.WriteBoolean("sola_flag", SOLAFlag.Invoke());
                writer.WriteBoolean("background_transit", BackgroundTransit.Invoke());
                writer.WriteString("run_title", RunTitle.Invoke());
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
