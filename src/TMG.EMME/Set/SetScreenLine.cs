/*
    Copyright 2026 University of Toronto

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
using TMG.Utilities;
using XTMF2;

namespace TMG.Emme.Set;

[Module(Name = "Set ScreenLine", Description = "Allows you to set an extra attribute given station codes from CSV.",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
public sealed class SetScreenLine : BaseAction<ModellerController>
{
    [Parameter(Name = "Scenario Number", Description = "The scenario number to use.", DefaultValue = "1", Index = 0, Required = true)]
    public IFunction<int> ScenarioNumber = null!;

    [SubModule(Name = "Stream", Description = "The input stream of station codes from CSV.", Index = 1, Required = true)]
    public IFunction<ReadStream> Stream = null!;

    [Parameter(Name = "Screen Line Name", Description = "The name of the screen line.", Index = 2, Required = true)]
    public IFunction<string> ScreenLineName = null!;

    [Parameter(Name = "Screen Line Column", Description = "The column number in the CSV that contains the screen line name.", Index = 3, Required = true)]
    public IFunction<int> ScreenLineColumn = null!;

    [Parameter(Name = "Station Column", Description = "The column number in the CSV that contains the station.", Index = 4, Required = true)]
    public IFunction<int> StationColumn = null!;        

    [SubModule(Name = "Station Attributes", Description = "The station attributes to set.", Index = 5, Required = true)]
    public IFunction<string>[] StationAttributes = null!;

    [SubModule(Name = "Output Attribute", Description = "The output attribute to set.", Index = 6, Required = true)]
    public IFunction<string> OutputAttribute = null!;

    public override void Invoke(ModellerController context)
    {
        // Load the station codes from the stream
        List<int> stationCodes = [];
        CsvReader reader = new(Stream.Invoke());
        var stationColumn = StationColumn.Invoke();
        var screenLineColumn = ScreenLineColumn.Invoke();
        var screenLineName = ScreenLineName.Invoke();

        // Validate the column indices
        if (screenLineColumn < 0)
        {
            throw new XTMFRuntimeException(this, $"Screen line column must be greater than or equal to 0. Current value: {screenLineColumn}");
        }

        if (stationColumn < 0)
        {
            throw new XTMFRuntimeException(this, $"Station column must be greater than or equal to 0. Current value: {stationColumn}");
        }

        while (reader.LoadLine(out int columns))
        {
            reader.Get(out ReadOnlySpan<char> screenLine, screenLineColumn);

            // If the screen line name does not match, skip this line
            if (!screenLineName.Equals(screenLine, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            reader.Get(out int stationCode, stationColumn);
            stationCodes.Add(stationCode);
        }

        if (stationCodes.Count == 0)
        {
            throw new XTMFRuntimeException(this, $"No station codes found in the input stream for Screenline {screenLineName}.");
        }

        var parameters =JSONParameterBuilder.BuildParameters(writer =>
        {
            writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
            writer.WriteString("output_attribute", OutputAttribute.Invoke());
            writer.WriteStartArray("station_attributes");
            foreach (var stationAttribute in StationAttributes)
            {
                writer.WriteStringValue(stationAttribute.Invoke());
            }
            writer.WriteEndArray(); // End station_attributes

            writer.WriteStartArray("station_codes");
            foreach (var stationCode in stationCodes)
            {
                writer.WriteNumberValue(stationCode);
            }
            writer.WriteEndArray(); // End station_codes
        });

        context.Run(this, "tmg2.Set.set_screen_line", parameters, LogbookLevel.Standard);
    }
}
