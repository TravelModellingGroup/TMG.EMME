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
using System.Text;
using System.Text.Json;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme
{
    public static class JSONParameterBuilder
    {
        public static string BuildParameters(Action<Utf8JsonWriter> toExecute)
        {
            using var backing = new MemoryStream();
            using var writer = new Utf8JsonWriter(backing);
            writer.WriteStartObject();
            toExecute(writer);
            writer.WriteEndObject();
            writer.Flush();
            return Encoding.UTF8.GetString(backing.GetBuffer().AsSpan(0, (int)backing.Length));
        }
    }
}
