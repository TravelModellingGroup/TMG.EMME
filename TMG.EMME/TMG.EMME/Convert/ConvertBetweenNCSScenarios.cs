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
    [Module(Name = "Convert OldNCS 2 NewNCS Standards", Description = "Converts the old NCS standards to the most recent.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ConvertBetweenNCSScenarios : BaseAction<ModellerController>
    {
        [Parameter(Name = "Old NCS Scenario", Description = "",
            Index = 0)]
        public IFunction<int> OldScenarioNumber;
        [Parameter(Name = "New NCS Scenario", Description = "",
            Index = 1)]
        public IFunction<int> NewScenarioNumber;
        [Parameter(Name = "Station Centroid File", Description = "",
            Index = 2)]
        public IFunction<string> StationCentroidFile;
        [Parameter(Name = "Station Centroid File", Description = "",
            Index = 3)]
        public IFunction<string> ZoneCentroidFile;
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Convert.convert_between_ncs_scenarios", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("old_ncs_scenario", OldScenarioNumber.Invoke());
                writer.WriteNumber("new_ncs_scenario", NewScenarioNumber.Invoke());
                writer.WriteString("station_centroid_file", Path.GetFullPath(StationCentroidFile.Invoke()));
                writer.WriteString("zone_centroid_file", Path.GetFullPath(ZoneCentroidFile.Invoke()));

            }), LogbookLevel.Standard);
        }
    }
}
