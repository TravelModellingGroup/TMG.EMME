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
        [Parameter(Name = "I Subarea Link Selection", Description = "",
            Index = 0)]
        public IFunction<string> ISubareaLinkSelection;
        [Parameter(Name = "J Subarea Link Selection", Description = "",
            Index = 1)]
        public IFunction<string> JSubareaLinkSelection;

        [Parameter(Name = "Scenario Number", Description = "",
            Index = 2)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Shapefile Location", Description = "",
            Index = 3)]
        public IFunction<string> ShapefileLocation;

        [Parameter(Name = "Create Nflag From Shapefile", Description = "",
            Index = 4)]
        public IFunction<bool> CreateNflagFromShapefile;

        [Parameter(Name = "Subarea Node Attribute", Description = "",
            Index = 5)]
        public IFunction<string> SubareaNodeAttribute;

        [Parameter(Name = "Subarea Gate Attribute", Description = "",
            Index = 6)]
        public IFunction<string> SubareaGateAttribute;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Export.export_subarea", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteString("i_subarea_link_selection", ISubareaLinkSelection.Invoke());
                writer.WriteString("j_subarea_link_selection", JSubareaLinkSelection.Invoke());
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteString("shape_file_location", ShapefileLocation.Invoke());
                writer.WriteBoolean("create_nflag_from_shapefile", CreateNflagFromShapefile.Invoke());
                writer.WriteString("subarea_node_attribute", SubareaNodeAttribute.Invoke());
                writer.WriteString("subarea_gate_attribute", SubareaGateAttribute.Invoke());
            }), LogbookLevel.Standard);
        }
    }
}
