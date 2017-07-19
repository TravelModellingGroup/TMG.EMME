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
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using System;
using System.Diagnostics;
using System.IO;

namespace TMG.Emme.Test
{
    internal static class Helper
    {
        internal static readonly string LogbookNone = "NONE";
        internal static readonly string LogbookAll = "ALL";

        static Helper()
        {
            //Load the configuration
            var configFile = new FileInfo("TMG.EMME.Test.Configuration.json");
            if (!configFile.Exists)
            {
                Assert.Fail("Configuration file \"TMG.EMME.Test.Configuration.json\" does not exist please create it to run tests.");
            }
            else
            {
                using (var reader = new JsonTextReader(configFile.OpenText()))
                {
                    while(reader.Read())
                    {
                        if(reader.TokenType == JsonToken.PropertyName)
                        {
                            switch(reader.Value)
                            {
                                case "ProjectFile":
                                    ProjectFile = reader.ReadAsString();
                                    break;
                            }
                        }
                    }
                }
            }
            // in this case we are debugging the unit test
            if (Debugger.IsAttached)
            {
                Modeller = new ModellerController(null, ProjectFile, "DEBUG_EMME", launchInNewProcess:false);
            }
            else
            {
                Modeller = new ModellerController(null, ProjectFile);
            }
        }

        public static string ProjectFile { get; private set; }
        public static ModellerController Modeller { get; private set; }

        public static void WriteProperty<T>(JsonWriter writer, string name, T value)
        {
            writer.WritePropertyName(name);
            if(typeof(T) == typeof(string))
            {
                writer.WriteValue((string)(object)value);
            }
            else if (typeof(T) == typeof(int))
            {
                writer.WriteValue((int)(object)value);
            }
            else if(typeof(T) == typeof(float))
            {
                writer.WriteValue((float)(object)value);
            }
            else if (typeof(T) == typeof(double))
            {
                writer.WriteValue((double)(object)value);
            }
            else if(typeof(T) == typeof(bool))
            {
                writer.WriteValue((bool)(object)value);
            }
            else
            {
                throw new NotSupportedException($"Unsupported type {typeof(T).FullName}!");
            }
        }
    }
}
