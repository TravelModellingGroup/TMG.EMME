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

namespace TMG.Emme.Import
{
    [Module(Name = "Import Transit Lines from GTFS", Description = "Generates transit line itineraries from GTFS data.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ImportTransitLinesFromGtfs : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Import.import_transit_lines_from_gtfs", GetParameters(), LogbookLevel.Standard);
        }

        [Parameter(DefaultValue = "1", Index = 0, Name = "Base Scenario", Description = "The scenario to execute against")]
        public IFunction<int> BaseScenario;

        [Parameter(DefaultValue = "15", Index = 1, Name = "Maximum Interstop Links",
            Description = "Lines requiring links more than the maximum will not be added.")]
        public IFunction<int> MaxNonStopNodes;

        [Parameter(DefaultValue = "", Index = 2, Name = "Link Priority Attribute",
            Description = "The factor to be applied to link speeds.")]
        public IFunction<string> LinkPriorityAttributeId;

        [Parameter(DefaultValue = "FrabtiztownGTFS", Index = 3, Name = "GTFS Folder",
            Description = "The folder that conatins the GTFS feed files.")]
        public IFunction<string> GtfsFolder;

        [Parameter(DefaultValue = "stop_to_node.csv", Index = 4, Name = "Stop-to-node File",
            Description = "The csv file that contains Stop IDs and the corresponding Emme Node IDs.")]
        public IFunction<string> StopToNodeFile;

        [Parameter(DefaultValue = "2", Index = 5, Name = "New Scenario",
            Description = "The scenario ID to publish the new network.")]
        public IFunction<int> NewScenarioId;

        [Parameter(DefaultValue = "Test Transit Network", Index = 6, Name = "New Scenario Title",
            Description = "The title of the new scenario.")]
        public IFunction<string> NewScenarioTitle;

        [Parameter(DefaultValue = "ServiceTable", Index = 7, Name = "Transit Service Table",
            Description = "The file name to store the output service table file.")]
        public IFunction<string> LineServiceTableFile;

        [Parameter(DefaultValue = "mapping", Index = 8, Name = "Mapping file",
            Description = "The file name to store the output that maps between EMME ID and GTFS Trip ID.")]
        public IFunction<string> MappingFileName;

        [Parameter(DefaultValue = "true", Index = 9, Name = "Publish network flag",
            Description = "Set as True to publish the network to the new scenario.")]
        public IFunction<bool> PublishFlag;

        private string GetParameters()
        {
            return JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_id", BaseScenario.Invoke());
                writer.WriteNumber("max_non_stop_nodes", MaxNonStopNodes.Invoke());
                writer.WriteString("link_priority_attribute", LinkPriorityAttributeId.Invoke());
                writer.WriteString("gtfs_folder", Path.GetFullPath(GtfsFolder.Invoke()));
                writer.WriteString("stop_to_node_file", Path.GetFullPath(StopToNodeFile.Invoke()));
                writer.WriteNumber("new_scenario_id", NewScenarioId.Invoke());
                writer.WriteString("new_scenario_title", NewScenarioTitle.Invoke());
                writer.WriteString("service_table_file", LineServiceTableFile.Invoke());
                writer.WriteString("mapping_file", MappingFileName.Invoke());
                writer.WriteBoolean("publish_flag", PublishFlag.Invoke());
            });
        }
    }
}