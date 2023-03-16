/*
    Copyright 2023 University of Toronto

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

namespace TMG.Emme.Calculate
{
    [Module(Name = "Calculate Background Traffic", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class CalculateBackgroundTraffic : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", DefaultValue = "0", Description = "The scenario number to execute against.",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Interval Lengths", DefaultValue = "", Description = "Defines how the assignment time is split into intervals.",
            Index = 1)]
        public IFunction<float[]> IntervalLengths;

        [Parameter(Name = "Background Traffic Link Component Extra Attribute", DefaultValue = "@tvph", Description = "",
                Index = 5)]
        public IFunction<string> LinkComponentAttribute;
        
        [Parameter(Name = "Time Dependent Start Index for Attributes", DefaultValue = "0", Description = "Time Dependent Start Indices used to create the alphanumerical attribute name string for attributes in this class.",
            Index = 5)]
        public IFunction<int> StartIndex;

        [Parameter(Name = "Mixed Used TTF Ranged", DefaultValue = "3-128", Description = "The TTFs where transit vehicles will occupy"
            + " some capacity on links. The ranges are inclusive.", Index = 3)]
        public IFunction<RangeSet> MixedUseTTFRanges;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Calculate.calculate_background_traffic", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                writer.WriteString("link_component_attribute", LinkComponentAttribute.Invoke());
                writer.WriteNumber("start_index", StartIndex.Invoke());
                writer.WritePropertyName("interval_length_list");
                writer.WriteStartArray();
                foreach (var interval in IntervalLengths.Invoke())
                {
                    writer.WriteNumberValue(interval);
                }
                writer.WriteEndArray();
                writer.WritePropertyName("mixed_use_ttf_ranges");
                writer.WriteStartArray();
                foreach (var range in MixedUseTTFRanges.Invoke())
                {
                    writer.WriteStartObject();
                    writer.WriteNumber("start", range.Start);
                    writer.WriteNumber("stop", range.Stop);
                    writer.WriteEndObject();
                }
                writer.WriteEndArray();
            }), LogbookLevel.Standard);
        }

    }
}
