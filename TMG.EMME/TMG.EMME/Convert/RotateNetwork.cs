/*
    Copyright 2021 University of Toronto
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
    [Module(Name = "Rotate Network", Description = "Rotates & translates network based on two corresponding links.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class RotateNetwork : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "Scenario number containing network to rotate",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Reference Link I Node", Description = "I-node of link from network to rotate",
            Index = 1)]
        public IFunction<int> ReferenceLinkINode;

        [Parameter(Name = "Reference Link J Node", Description = "J-node of link from network to rotate",
            Index = 2)]
        public IFunction<int> ReferenceLinkJNode;

        [Parameter(Name = "Corresponding X0", Description = "Corresponding xi coordinate of I-node",
            Index = 3)]
        public IFunction<float> CorrespondingX0;
        [Parameter(Name = "Corresponding Y0", Description = "Corresponding yi coordinate of I-node",
           Index = 4)]
        public IFunction<float> CorrespondingY0;

        [Parameter(Name = "Corresponding X1", Description = "Corresponding xi coordinate of J-node",
            Index = 5)]
        public IFunction<float> CorrespondingX1;

        [Parameter(Name = "Corresponding Y1", Description = "Corresponding yi coordinate of J-node",
            Index = 6)]
        public IFunction<float> CorrespondingY1;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Convert.rotate_network", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteNumber("reference_link_i_node", ReferenceLinkINode.Invoke());
                writer.WriteNumber("reference_link_j_node", ReferenceLinkJNode.Invoke());
                writer.WriteNumber("corresponding_x_0", ReferenceLinkJNode.Invoke());
                writer.WriteNumber("corresponding_y_0", ReferenceLinkJNode.Invoke());
                writer.WriteNumber("corresponding_x_1", ReferenceLinkJNode.Invoke());
                writer.WriteNumber("corresponding_y_1", ReferenceLinkJNode.Invoke());
            }), LogbookLevel.Standard);
        }
    }
}