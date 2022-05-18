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
    [Module(Name = "Generate Hypernetwork From Schema", Description = "Generates a hyper-network to support fare-based transit assignment (FBTA), from an XML schema file.Links and segments with negative fare values will be reported to the Logbook for further inspection. For fare schema specification, please consult TMG documentation. Temporary storage requirements: one transit line extra attribute, one node extra attribute. ",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class GenerateHypernetworkFromSchema : BaseAction<ModellerController>
    {
        [Parameter(Name = "Base Scenario", Description = "The number of the Emme BASE (i.e. non-FBTN-enabled) scenario.",
            Index = 0)]
        public IFunction<int> BaseScenario;
        [Parameter(Name = "New Scenario", Description = "The number of the EMME scenario where Hypernetwork will be created.",
            Index = 1)]
        public IFunction<int> NewScenario;
        [Parameter(Name = "Station Connector Flag", Description = "Should centroid connectors be automatically integrated with stations?",
            Index = 2)]
        public IFunction<bool> StationConnectorFlag;
        [Parameter(Name = "Transfer Mode", Description = "The mode ID to assign to new virtual connector links.",
            Index = 3)]
        public IFunction<string> TransferMode;
        [Parameter(Name = "Virtual Node Domain", Description = "All created virtual nodes will have IDs higher than this number. This will not override an existing node.",
            Index = 4)]
        public IFunction<int> VirtualNodeDomain;
        [Parameter(Name = "Base Schema File", Description = "Base Schema File",
                Index = 5)]
        public IFunction<string> BaseSchemaFile;
        [SubModule(Name = "Fare Classes", Description = "Fare Classes", Index = 6)]
        public IFunction<FareClass>[] FareClasses;

        [Module(Name = "Fare Class", Description = "Fare Class", DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class FareClass : XTMF2.IModule
        {
            [Parameter(Name = "Link Fare Attribute", Description = "A LINK extra attribute in which to store the transfer and boarding fares.",
                Index = 0)]
            public IFunction<string> LinkFareAttribute;
            [Parameter(Name = "Segment Fare Attribute", Description = "A TRANSIT SEGMENT extra attribute in which to store the in-line fares.",
                Index = 1)]
            public IFunction<string> SegmentFareAttribute;
            [Parameter(Name = "Schema File", Description = "Fare Schema File",
                Index = 2)]
            public IFunction<string> SchemaFile;


            public string Name { get; set; }
            public bool RuntimeValidation(ref string error)
            {
                error = "There must be at least one fare class defined.";
                return true;
            }
            public void WriterParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteString("link_fare_attribute", LinkFareAttribute.Invoke());
                writer.WriteString("segment_fare_attribute", SegmentFareAttribute.Invoke());
                writer.WriteString("schema_file", Path.GetFullPath(SchemaFile.Invoke()));
                writer.WriteEndObject();
            }
        }
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Generate.generate_hypernetwork_from_schema",
            JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("base_scenario", BaseScenario.Invoke());
                writer.WriteNumber("new_scenario", NewScenario.Invoke());
                writer.WriteBoolean("station_connector_flag", StationConnectorFlag.Invoke());
                writer.WriteString("transfer_mode", TransferMode.Invoke());
                writer.WriteNumber("virtual_node_domain", VirtualNodeDomain.Invoke());
                writer.WriteStartArray("fare_classes");
                writer.WriteString("base_schema_file", Path.GetFullPath(BaseSchemaFile.Invoke()));
                foreach (var fareClass in FareClasses)
                {
                    fareClass.Invoke().WriterParameters(writer);
                }
                writer.WriteEndArray();
            }), LogbookLevel.Standard);
        }
    }
}