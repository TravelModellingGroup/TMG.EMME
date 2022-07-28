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

namespace TMG.Emme.Generate
{
    [Module(Name = "Generate Full Network Set", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class GenerateTimePeriodNetworks : BaseAction<ModellerController>
    {
        [Parameter(Name = "BaseScenarioNumber", Description = "The scenario number for the base network.",
            Index = 0)]
        public IFunction<int> BaseScenarioNumber;

        [Parameter(Name = "Transit Service Table File", Description = "A link to the file containing transit service data.",
                Index = 1)]
        public IFunction<string> TransitServiceTableFile;

        [Parameter(Name = "Attribute Aggregator", Description = "The formatted string to aggregate attributes.",
            Index = 2)]
        public IFunction<string> AttributeAggregator;

        [Parameter(Name = "Connector Filter Attribute", Description = "The name of the attribute to use as a filter.",
            Index = 3)]
        public IFunction<string> ConnectorFilterAttribute;

        [Parameter(Name = "Default Aggregation", Description = "The name of the attribute to use as a filter.",
            Index = 4)]
        public IFunction<string> DefaultAggregation;

        [Parameter(Name = "Line Filter Expression", Description = "The formatted string to use as an expression to filter lines. Leave blank to skip prorating transit speeds.",
            Index = 5)]
        public IFunction<string> LineFilterExpression;

        [Parameter(Name = "NodeFilterAttribute", Description = "A string of the transfer mode IDs.",
            Index = 6)]
        public IFunction<string> NodeFilterAttribute;

        [Parameter(Name = "Stop Filter Attribute", Description = "The name of the attribute to use as a filter.",
            Index = 7)]
        public IFunction<string> StopFilterAttribute;

        [Parameter(Name = "Transfer Mode String", Description = "The name of the attribute to use as a filter.",
            Index = 8)]
        public IFunction<string> TransferModeString;

        [Parameter(Name = "Batch Edit File", Description = "A path to the batch edit file.",
            Index = 9)]
        public IFunction<string> BatchEditFile;

        [Parameter(Name = "Transit Aggreggation Selection Table File", Description = "A link to the file containing how to aggregate schedules.",
            Index = 10)]
        public IFunction<string> TransitAggreggationSelectionTableFile;

        [Parameter(Name = "Transit Alternative Table", Description = "A link to the file containing how to modify transit schedules.",
            Index = 11)]
        public IFunction<string> TransitAlternativeTableFile;

        [SubModule(Name = "Time Periods", Description = "Time periods to consider.", Index = 12)]
        public IFunction<TimePeriod>[] TimePeriods;

        [SubModule(Name = "Additional Transit Alternative Tables", Description = "Additional files containing how to modify transit schedules. Each will be applied in order.", Index = 13)]
        public IFunction<AdditionalTransitAlternativeTable>[] AdditionalTransitAlternativeTables;

        [Module(Name = "Additional Transit Alternative Table Time Periods", Description = "",
            DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class AdditionalTransitAlternativeTable : XTMF2.IModule
        {
            [Parameter(Name = "Alternative Table File", Description = "",
               Index = 0)]
            public IFunction<string> AlternativeTableFile;

            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("name", Name);
                writer.WriteString("alternative_table_file", AlternativeTableFile.Invoke());
                writer.WriteEndObject();
            }
        }

        [Module(Name = "Time Periods", Description = "Time periods to consider.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class TimePeriod : XTMF2.IModule
        {
            [Parameter(Name = "Uncleaned Scenario Number", Description = "The scenario number for the uncleaned network",
               Index = 0)]
            public IFunction<int> UncleanedScenarioNumber;

            [Parameter(Name = "Uncleaned Description", Description = "The description for the uncleaned scenario",
                Index = 1)]
            public IFunction<string> UncleanedDescription;

            [Parameter(Name = "Cleaned Scenario Number", Description = "The scenario number for the cleaned network",
               Index = 2)]
            public IFunction<int> CleanedScenarioNumber;

            [Parameter(Name = "Cleaned Description", Description = "The description for the cleaned scenario",
                Index = 3)]
            public IFunction<string> CleanedDescription;

            [Parameter(Name = "Start Time", Description = "The start time for this scenario",
               Index = 4)]
            public IFunction<string> StartTime;

            [Parameter(Name = "End Time", Description = "The end time for this scenario",
               Index = 5)]
            public IFunction<string> EndTime;

            [Parameter(Name = "Scenario Network Update File", Description = "The location of the network update file for this time period.",
                Index = 6)]
            public IFunction<string> ScenarioNetworkUpdateFile;

            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("name", Name);
                writer.WriteNumber("uncleaned_scenario_number", UncleanedScenarioNumber.Invoke());
                writer.WriteNumber("cleaned_scenario_number", CleanedScenarioNumber.Invoke());
                writer.WriteString("uncleaned_description", UncleanedDescription.Invoke());
                writer.WriteString("cleaned_description", CleanedDescription.Invoke());
                writer.WriteString("start_time", StartTime.Invoke());
                writer.WriteString("end_time", EndTime.Invoke());
                writer.WriteString("scenario_network_update_file", ScenarioNetworkUpdateFile.Invoke());
                writer.WriteEndObject();
            }
        }

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Generate.generate_time_period_networks", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteStartObject();
                writer.WriteNumber("base_scenario_number", BaseScenarioNumber.Invoke());
                writer.WriteString("transit_service_table_file", Path.GetFullPath(TransitServiceTableFile.Invoke()));
                writer.WriteString("attribute_aggregator", AttributeAggregator.Invoke());
                writer.WriteString("connector_filter_attribute", ConnectorFilterAttribute.Invoke());
                writer.WriteString("default_aggregation", DefaultAggregation.Invoke());
                writer.WriteString("line_filter_expression", LineFilterExpression.Invoke());
                writer.WriteString("node_filter_attribute", NodeFilterAttribute.Invoke());
                writer.WriteString("stop_filter_attribute", StopFilterAttribute.Invoke());
                writer.WriteString("transfer_mode_string", TransferModeString.Invoke());
                writer.WriteString("batch_edit_file", Path.GetFullPath(BatchEditFile.Invoke()));
                writer.WriteString("transit_aggregation_selection_table_file", TransitAggreggationSelectionTableFile.Invoke());
                writer.WriteString("transit_alternative_table_file", Path.GetFullPath(TransitAlternativeTableFile.Invoke()));
                writer.WriteStartArray("time_periods");
                foreach (var timePeriod in TimePeriods)
                {
                    timePeriod.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
                writer.WriteStartArray("additional_transit_alternative_table");
                foreach (var additionalTransitAlternativeTable in AdditionalTransitAlternativeTables)
                {
                    additionalTransitAlternativeTable.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
                writer.WriteEndObject();

            }), LogbookLevel.Standard);
        }
    }
}
