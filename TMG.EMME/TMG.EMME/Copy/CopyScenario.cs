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
using System.Text.Json;
using XTMF2;

namespace TMG.Emme.Copy
{
    [Module(Name = "Copy Scenario", Description = "Copy an EMME scenario optionally also copying the assignments.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class CopyScenario : BaseAction<ModellerController>
    {
        [Parameter(DefaultValue = "1", Index = 0, Name = "From Scenario", Description = "The scenario to copy from.")]
        public IFunction<int> FromScenario;

        [Parameter(DefaultValue = "2", Index = 1, Name = "To Scenario", Description = "The scenario to copy to.")]
        public IFunction<int> ToScenario;

        [Parameter(DefaultValue = "false", Index = 2, Name = "Copy Strategy", Description = "Should assignment strategies also be copied?")]
        public IFunction<bool> CopyStrategy;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Copy.copy_scenario",
                    JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteNumber("from_scenario", FromScenario.Invoke());
                        writer.WriteNumber("to_scenario", ToScenario.Invoke());
                        writer.WriteBoolean("copy_strategy", CopyStrategy.Invoke());
                    }), LogbookLevel.None);
        }
    }
}
