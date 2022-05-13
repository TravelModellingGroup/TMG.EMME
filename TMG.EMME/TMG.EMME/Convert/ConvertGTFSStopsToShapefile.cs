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

namespace TMG.Emme.Convert
{
    [Module(Name = "Convert GTFS Stops to Shapefile", Description = "Converts the stops.txt file to a shapefile.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ConvertGTFSStopsToShapefile : BaseAction<ModellerController>
    {
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Convert.convert_gtfs_stops_to_shapefile", GetParameters(), LogbookLevel.Standard);
        }

        [Parameter(DefaultValue = "FrabtiztownGTFS", Index = 0, Name = "GTFS Folder",
            Description = "The GTFS folder that contains the stops.txt file")]
        public IFunction<string> GTFSFolder;

        [Parameter(DefaultValue = "FrabtiztownStopShp", Index = 1, Name = "Shapefile Name",
            Description = "The name of the shapefile for export.")]
        public IFunction<string> ShapefileName;

        private string GetParameters()
        {
            return JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteString("gtfs_folder", Path.GetFullPath(GTFSFolder.Invoke()));
                writer.WriteString("shapefile_name", ShapefileName.Invoke());
            });
        }
    }
}