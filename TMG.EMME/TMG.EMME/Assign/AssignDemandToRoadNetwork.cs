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

namespace TMG.Emme.Assign
{
    [Module(Name = "Assign Demand To Road Assignment", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class AssignDemandToRoadAssignment : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "", Description = "", Index = )]
        public IFunction<sring> ;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Assign.assign_demand_to_road_network", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("", ScenarioNumber.Invoke());
            }), LogbookLevel.Standard);
        }
    }
}