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
using System.Text;
using System.Linq;
using XTMF2;

namespace TMG.Emme.Utilities
{
    [Module(Name = "Network Calculator", Description = "Runs the network calculator tool and returns the sum from the report.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class NetworkCalculator : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "Scenario to run",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Domain", Description = "The Emme domain type in the result. Options: Link, Node, Transit_Line, Transit_Segment",
            Index = 1)]
        public IFunction<Domains> Domain;

        [Parameter(Name = "Expression", Description = "The expression to compute. E.g. sqrt((xi - xj) ^ 2 + (yi - yj) ^ 2)",
            Index = 2)]
        public IFunction<string> Expression;

        [Parameter(Name = "Node Selection", Description = "The nodes to include in the calculation. Default: all", Index = 3)]
        public IFunction<string> NodeSelection;

        [Parameter(Name = "Link Selection", Description = "The links to include in the calculation. Default: all", Index = 4)]
        public IFunction<string> LinkSelection;

        [Parameter(Name = "Transit Line Selection", Description = "The transit lines to include in the calculation. Default: all", Index = 5)]
        public IFunction<string> TransitLineSelection;

        [Parameter(Name = "Result", Description = "The attributes to save the result into, leave blank to not save", Index = 6)]
        public IFunction<string> Result;
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.utilities.network_calculator", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteNumber("domain", (int)Domain.Invoke());
                writer.WriteString("expression", Expression.Invoke());
                writer.WriteString("node_selection", NodeSelection.Invoke());
                writer.WriteString("link_selection", LinkSelection.Invoke());
                writer.WriteString("transit_line_selection", TransitLineSelection.Invoke());
                writer.WriteString("result", Result.Invoke());
            }), LogbookLevel.Standard);

        }
        public enum Domains
        {
            Link = 0, Node = 1, TransitLine = 2, TransitSegment = 3
        }

    }
}
