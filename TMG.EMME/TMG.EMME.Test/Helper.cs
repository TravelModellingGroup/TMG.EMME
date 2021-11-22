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
using System.Text.Json;
using XTMF2;
using XTMF2.RuntimeModules;
using System.Linq;

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
                                    if (reader.ValueTextEquals(ProjectFileProperty))
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

        internal static void ImportFrabitztownNetwork(int scenarioNumber)
        {
            Helper.ImportNetwork(scenarioNumber, Path.GetFullPath("TestFiles/test.nwp"));
        }

        internal static void ImportNetwork(int scenarioNumber, string filePath)
        {
            Assert.IsTrue(
               Helper.Modeller.Run(null, "tmg2.Import.import_network_package",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteString("network_package_file", filePath);
                    writer.WriteString("scenario_description", "Test Network");
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WriteString("conflict_option", "PRESERVE");
                }), LogbookLevel.Standard));
        }

        internal static void ImportBinaryMatrix(int scenarioNumber, int matrixNumber, string filePath)
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Import.import_binary_matrix",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteNumber("matrix_type", 4);
                     writer.WriteNumber("matrix_number", matrixNumber);
                     writer.WriteString("binary_matrix_file", filePath);
                     writer.WriteNumber("scenario_number", scenarioNumber);
                     writer.WriteString("matrix_description", "Test Matrix");
                 }), LogbookLevel.Standard));

        }

        /// <summary>
        /// Creates an array of basic parameters with the given values.
        /// </summary>
        /// <typeparam name="T">The type of parameter.</typeparam>
        /// <param name="values">The values to provide</param>
        /// <param name="moduleNames">Optional the names for all of the parameters</param>
        /// <returns>An array of basic parameters containing the values.</returns>
        internal static IFunction<T>[] CreateParameters<T>(T[] values, string[] moduleNames = null)
        {
            if (moduleNames != null && moduleNames.Length != values.Length)
            {
                throw new ArgumentException("The size of the values and modules names must be the same!", nameof(moduleNames));
            }
            return values.Select
                (
                (v, i) => new BasicParameter<T>()
                {
                    Name = moduleNames?[i] ?? null,
                    Value = v
                }
                ).ToArray();
        }
    }
}
