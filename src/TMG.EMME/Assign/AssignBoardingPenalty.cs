/*
    Copyright 2022-2026 University of Toronto

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

using XTMF2;

namespace TMG.Emme.Assign;

[Module(Name = "Assign Boarding Penalty", Description = "Assigns line-specific boarding penalties",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
public class AssignBoardingPenalty : BaseAction<ModellerController>
{
    [Parameter(Name = "Scenario Number", Description = "The scenario number to assign boarding penalty to.",
        Index = 0)]
    public IFunction<int[]> ScenarioNumbers = null!;

    [Parameter(Name = "Penalty Filter String", Description = "A colon seperated list of penalty in the order label:filter:initial:transfer:ivttPerception",
        Index = 1)]
    public IFunction<PenaltyFilter[]> PenaltyFilterString = null!;

    public override void Invoke(ModellerController context)
    {
        context.Run(this, "tmg2.Assign.assign_boarding_penalty", JSONParameterBuilder.BuildParameters(writer =>
        {
            writer.WritePropertyName("scenario_numbers");
            writer.WriteStartArray();
            foreach (var scenario in ScenarioNumbers.Invoke())
            {
                writer.WriteNumberValue(scenario);
            }
            writer.WriteEndArray();

            writer.WritePropertyName("penalty_filter_string");
            writer.WriteStartArray();
            foreach (var penaltyFilter in PenaltyFilterString.Invoke())
            {
                writer.WriteStartObject();
                writer.WriteString("label", penaltyFilter.Label.Invoke());
                writer.WriteString("filter", penaltyFilter.Filter.Invoke());
                writer.WriteNumber("initial", penaltyFilter.Initial.Invoke());
                writer.WriteNumber("transfer", penaltyFilter.Transfer.Invoke());
                writer.WriteNumber("ivttPerception", penaltyFilter.IvttPerception.Invoke());
                writer.WriteEndObject();
            }
            writer.WriteEndArray();

        }), LogbookLevel.Standard);

    }

    [Module(Name = "Penalty Filter", Description = "The Assign Boarding Penalty tool for transit assignment estimation.",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class PenaltyFilter : BaseFunction<PenaltyFilter>
    {
        [Parameter(Name = "label", Description = "The line group name e.g. GO Train.",
            Index = 0)]
        public IFunction<string> Label = null!;

        [Parameter(Name = "filter", Description = "The network selector expression",
            Index = 1)]
        public IFunction<string> Filter = null!;

        [Parameter(Name = "initial", Description = "The number representing the initial boarding penalty",
            Index = 2)]
        public IFunction<float> Initial = null!;

        [Parameter(Name = "transfer", Description = "The number representing the transfer boarding penalty",
            Index = 3)]
        public IFunction<float> Transfer = null!;

        [Parameter(Name = "ivttPerception", Description = "The number representing the IVTT perception Factor",
            Index = 4)]
        public IFunction<float> IvttPerception = null!;

        public override PenaltyFilter Invoke()
        {
            return this;
        }
    }
}