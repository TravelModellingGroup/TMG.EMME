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
using System.Text;
using System.Linq;
using System.IO;
using XTMF2;

namespace TMG.Emme.Export
{
    [Module(Name = "Export Network Shapefile", Description = "Export Emme Network as Shapefile",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ExportNetworkShapefile : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "The scenario number containing network to export.",
            Index = 0)]
        public IFunction<int> ScenarioNumbers;

        [Parameter(Name = "Save To", Description = "The location to write the file.",
            Index = 1)]
        public IFunction<string> SaveTo;

        [Parameter(Name = "TransitShapes", Description = "Type of geometry or transit shape to export",
            Index = 2)]
        public IFunction<string> TransitShapes;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Export.export_network_shapefile", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumbers.Invoke());
                writer.WriteString("export_path", Path.GetFullPath(SaveTo.Invoke()));
                writer.WriteString("transit_shapes", TransitShapes.Invoke());
            }), LogbookLevel.Standard);
        }
    }
}