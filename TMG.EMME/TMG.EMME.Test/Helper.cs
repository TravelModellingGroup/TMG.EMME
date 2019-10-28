﻿/*
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
using System.Text.Json;
using XTMF2;
using XTMF2.RuntimeModules;

namespace TMG.Emme.Test
{
    internal static class Helper
    {
        private const string ProjectFileProperty = "ProjectFile";

        internal static void InitializeEMME()
        {
            if (Modeller == null)
            {
                lock (typeof(Helper))
                {
                    if (Modeller == null)
                    {
                        //Load the configuration
                        var configFile = new FileInfo("TMG.EMME.Test.Configuration.json");
                        if (!configFile.Exists)
                        {
                            Assert.Fail("Configuration file \"TMG.EMME.Test.Configuration.json\" does not exist please create it to run tests.");
                        }
                        else
                        {
                            var reader = new Utf8JsonReader(File.ReadAllBytes(configFile.FullName));
                            while (reader.Read())
                            {
                                if (reader.TokenType == JsonTokenType.PropertyName)
                                {
                                    if(reader.ValueTextEquals(ProjectFileProperty))
                                    {
                                        reader.Read();
                                        ProjectFile = reader.GetString();
                                    }
                                }
                            }
                        }
                        // in this case we are debugging the unit test
                        if (Debugger.IsAttached)
                        {
                            Modeller = new ModellerController(null, ProjectFile, "DEBUG_EMME", launchInNewProcess: false);
                        }
                        else
                        {
                            Modeller = new ModellerController(null, ProjectFile);
                        }
                    }
                }
            }
        }

        public static string ProjectFile { get; private set; }
        public static ModellerController Modeller { get; private set; }

        internal static IFunction<T> CreateParameter<T>(T value, string moduleName = null)
        {
            return new BasicParameter<T>()
            {
                Name = moduleName,
                Value = value
            };
        }
    }
}
