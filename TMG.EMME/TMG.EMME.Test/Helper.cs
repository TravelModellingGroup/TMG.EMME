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
        private const string EmmePathProperty = "EmmePath";

        internal static void InitializeEMME()
        {
            if (Modeller == null)
            {
                lock (typeof(Helper))
                {
                    if (Modeller == null)
                    {
                        string emmePath = null;
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
                                    else if (reader.ValueTextEquals(EmmePathProperty))
                                    {
                                        reader.Read();
                                        emmePath = reader.GetString();
                                    }
                                }
                            }
                        }
                        // in this case we are debugging the unit test
                        if (Debugger.IsAttached)
                        {
                            Modeller = new ModellerController(null, ProjectFile, "DEBUG_EMME", launchInNewProcess: false, emmePath: emmePath);
                        }
                        else
                        {
                            Modeller = new ModellerController(null, ProjectFile, emmePath: emmePath);
                        }
                    }
                }
            }
        }

        internal static void ShutdownEMME()
        {
            lock (typeof(Helper))
            {
                Helper.Modeller?.Dispose();
                Helper.Modeller = null;
            }
        }

        internal static void RunAssignBoardingPenalty(int[] scenarioNumbers)
        {
            Assert.IsTrue(
               Helper.Modeller.Run(null, "tmg2.Assign.assign_boarding_penalty",
               JSONParameterBuilder.BuildParameters(writer =>
               {
                   writer.WritePropertyName("scenario_numbers");
                   writer.WriteStartArray();
                   foreach (var s in scenarioNumbers)
                   {
                       writer.WriteNumberValue(s);
                   }
                   writer.WriteEndArray();
                   writer.WritePropertyName("penalty_filter_string");
                   writer.WriteStartArray();
                   writer.WriteStartObject();
                   writer.WriteString("label", "transit");
                   writer.WriteString("filter", "mode=brqmsl");
                   writer.WriteNumber("initial", 1.0);
                   writer.WriteNumber("transfer", 1.0);
                   writer.WriteNumber("ivttPerception", 1.0);
                   writer.WriteEndObject();
                   writer.WriteEndArray();
               }), LogbookLevel.Standard));
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

        internal static void ImportNetwork(int scenarioNumber, string filePath, string scenarioDescription = "toolbox2")
        {
            Assert.IsTrue(
               Helper.Modeller.Run(null, "tmg2.Import.import_network_package",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteString("network_package_file", Path.GetFullPath(filePath));
                    writer.WriteString("scenario_description", scenarioDescription);
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
                     writer.WriteNumber("matrix_type", (int)Emme.Import.ImportBinaryMatrix.MatrixTypes.MF);
                     writer.WriteNumber("matrix_number", matrixNumber);
                     writer.WriteString("binary_matrix_file", filePath);
                     writer.WriteNumber("scenario_number", scenarioNumber);
                     writer.WriteString("matrix_description", "Test Matrix");
                 }), LogbookLevel.Standard));

        }
        internal static void ExportNetwork(int scenarioNumber, string filePath)
        {

            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_network_package",
                JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteString("export_file", Path.GetFullPath(filePath));
                        writer.WriteNumber("scenario_number", scenarioNumber);
                        writer.WriteString("extra_attributes", "all");
                    }), LogbookLevel.Standard));
        }
        internal static void RunAssignTransit(int scenarioNumber, string demandMatrixId)
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_transit",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("calculate_congested_ivtt_flag", true);
                    writer.WriteNumber("node_logit_scale", 1f);
                    writer.WriteString("effective_headway_attribute", "@ehdw");
                    writer.WriteNumber("effective_headway_slope", 0.165f);
                    writer.WriteString("headway_fraction_attribute", "@hfrac");
                    writer.WriteNumber("iterations", 5);
                    writer.WriteNumber("norm_gap", 0.0f);
                    writer.WriteNumber("rel_gap", 0.0f);
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WriteNumber("walk_speed", 4.0f);
                    writer.WriteStartArray("transit_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "transit_class_1");
                    writer.WriteString("board_penalty_matrix", "mf0");
                    writer.WriteNumber("board_penalty_perception", 1.0f);
                    writer.WriteString("congestion_matrix", "mf0");
                    writer.WriteString("demand_matrix", demandMatrixId);
                    writer.WriteString("fare_matrix", "mf0");
                    writer.WriteNumber("fare_perception", 20.0f);
                    writer.WriteString("in_vehicle_time_matrix", "mf0");
                    writer.WriteString("impedance_matrix", "mf0");
                    writer.WriteString("link_fare_attribute_id", "@lfare");
                    writer.WriteString("mode", "*");
                    writer.WriteString("perceived_travel_time_matrix", "mf0");
                    writer.WriteString("segment_fare_attribute", "@sfare");
                    writer.WriteNumber("wait_time_perception", 2.299f);
                    writer.WriteString("wait_time_matrix", "mf0");
                    writer.WriteString("walk_time_perception_attribute", "@walkp");
                    writer.WriteString("walk_time_matrix", "mf0");
                    writer.WriteStartArray("walk_perceptions");
                    writer.WriteStartObject();
                    writer.WriteString("filter", "i=1,999999");
                    writer.WriteNumber("walk_perception_value", 2.0f);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("surface_transit_speeds");
                    writer.WriteStartObject();
                    writer.WriteNumber("alighting_duration", 1.1f);
                    writer.WriteNumber("boarding_duration", 1.9f);
                    writer.WriteNumber("default_duration", 0.1f);
                    writer.WriteNumber("global_erow_speed", 10f);
                    writer.WriteString("line_filter_expression", "");
                    writer.WriteString("mode_filter_expression", "b");
                    writer.WriteNumber("transit_auto_correlation", 2.0f);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("ttf_definitions");

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 1);
                    writer.WriteEndObject();

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 2);
                    writer.WriteEndObject();

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 3);
                    writer.WriteEndObject();

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 5);
                    writer.WriteEndObject();

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 4);
                    writer.WriteEndObject();

                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 1.1f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 6);
                    writer.WriteEndObject();

                    writer.WriteEndArray();
                    writer.WriteNumber("assignment_period", 1f);
                    writer.WriteString("name_string", "");
                    writer.WriteBoolean("congested_assignment", true);
                    writer.WriteString("csvfile", "");
                    writer.WriteNumber("origin_distribution_logit_scale", 0.2f);
                    writer.WriteBoolean("surface_transit_speed", true);
                    writer.WriteBoolean("walk_all_way_flag", false);
                    writer.WriteString("xrow_ttf_range", "2");
                }), LogbookLevel.Standard));
        }

        internal static void RunAssignTraffic(int scenarioNumber, string demandMatrixId, int iteration)
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_traffic",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("background_transit", true);
                    writer.WriteNumber("br_gap", 0);
                    writer.WriteNumber("iterations", iteration);
                    writer.WriteNumber("norm_gap", 0);
                    writer.WriteBoolean("performance_flag", true);
                    writer.WriteNumber("r_gap", 0);
                    writer.WriteString("run_title", "road assignment");
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WriteBoolean("sola_flag", true);
                    writer.WritePropertyName("mixed_use_ttf_ranges");
                    writer.WriteStartArray();
                    writer.WriteStartObject();
                    writer.WriteNumber("start", 3);
                    writer.WriteNumber("stop", 128);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("traffic_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "traffic class 1");
                    writer.WriteString("mode", "c");
                    writer.WriteString("demand_matrix", demandMatrixId);
                    writer.WriteString("time_matrix", "mf0");
                    writer.WriteString("cost_matrix", "mf4");
                    writer.WriteString("toll_matrix", "mf0");
                    writer.WriteNumber("peak_hour_factor", 1);
                    writer.WriteString("volume_attribute", "@auto_volume1");
                    writer.WriteString("link_toll_attribute", " @toll");
                    writer.WriteNumber("toll_weight", 1.0);
                    writer.WriteNumber("link_cost", 0.0);
                    writer.WriteStartArray("path_analyses");
                    writer.WriteStartObject();
                    writer.WriteString("attribute_id", "1");
                    writer.WriteString("aggregation_matrix", "");
                    writer.WriteString("aggregation_operator", "max");
                    writer.WriteString("lower_bound", "7");
                    writer.WriteString("upper_bound", "7");
                    writer.WriteString("path_selection", "all");
                    writer.WriteString("multiply_path_prop_by_demand", "7");
                    writer.WriteString("multiply_path_prop_by_value", "7");
                    writer.WriteString("analysis_attributes", "");
                    writer.WriteString("analysis_attributes_matrix", "mf0");
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();
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
