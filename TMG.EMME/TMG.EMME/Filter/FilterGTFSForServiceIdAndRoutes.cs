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

namespace TMG.Emme.Filter
{
    [Module(Name = "Filter GTFS for Service IDs and Routes", Description = "Cleans a set of GTFS files by Service IDs.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class FilterGTFSForServiceIdAndRoutes : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Filter.filter_gtfs_for_service_id_and_routes", GetParameters(), LogbookLevel.Standard);
        }

        [Parameter(DefaultValue = "FrabtiztownGTFS", Index = 0, Name = "GTFS Folder",
            Description = "The location of the GTFS directory to be cleaned")]
        public IFunction<string> GTFSFolder;

        [Parameter(DefaultValue = "FrabtiztownTransit", Index = 1, Name = "Service ID", 
            Description = "Comma-separated list of Service IDs from the calendar.txt file")]
        public IFunction<string> ServiceID;

        [SubModule(Required = false, Name = "Updated Routes File", Description = "Optional Filtered Routes", Index = 2)]
        public IFunction<string> UpdatedRoutesFile;

        private string GetParameters()
        {
            return JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteString("gtfs_folder", Path.GetFullPath(GTFSFolder.Invoke()));
                writer.WriteString("service_id", ServiceID.Invoke());
                writer.WriteString("routes_file", UpdatedRoutesFile.Invoke());
            });
        }
    }
}