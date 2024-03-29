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
    [Module(Name = "Export Boarding And Alighting", Description = "This tool extracts the total boarding and alighting for each transit stop of intrest in a given scenario..",
        DocumentationLink = "https://tmg.utoronto.ca/doc/2.0/tmgtoolbox2_emme/tools/Export/ExportBoardingAndAlighting.html")]
    public class ExportBoardingAndAlighting : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "The scenario number to extract transit information from.",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "File Location", Description = "The location file containing transit stop of intrest to import.",
            Index = 1)]
        public IFunction<string> FileLocation;

        [Parameter(Name = "Save To", Description = "The location to write the output file.",
            Index = 2)]
        public IFunction<string> SaveTo;

        [Parameter(Name = "Write to File", Description = "Tell the tool if you want your input file used or what to create yours",
            Index = 3)]
        public IFunction<bool> WriteToFile;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Export.export_boarding_and_alighting", JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                        writer.WriteString("export_file", Path.GetFullPath(SaveTo.Invoke()));
                        writer.WriteString("input_file", Path.GetFullPath(FileLocation.Invoke()));
                        writer.WriteBoolean("write_to_file", WriteToFile.Invoke());
                    }), LogbookLevel.Standard);
        }
    }
}
