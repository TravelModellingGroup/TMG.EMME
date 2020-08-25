/*
    Copyright 2017 University of Toronto
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
    [Module(Name = "Export Matching Emme Nodes For GTFS Stops", 
        Description = "Export a mapping file that shows the GTFS Stop IDs and their corresponding Node IDs in the EMME network.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ExportMatchingEmmeNodesForGtfsStops : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Export.export_matching_emme_nodes_for_gtfs_stops", GetParameters(), LogbookLevel.Standard);
        }

        [Parameter(DefaultValue = "stops.txt", Index = 0, Name = "Stops Input File",
            Description = "The stops input file in txt or shp format.")]
        public IFunction<string> StopsInputFile;

        [Parameter(DefaultValue = "stop_to_node", Index = 1, Name = "Output File",
            Description = "The output mapping file.")]
        public IFunction<string> MappingOutputFile;

        private string GetParameters()
        {
            return JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteString("input_stop_file", Path.GetFullPath(StopsInputFile.Invoke()));
                writer.WriteString("output_mapping_file", MappingOutputFile.Invoke());
            });
        }
    }
}