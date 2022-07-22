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

using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.Collections.Generic;
using System.Text;
using System.IO;
using XTMF2;

namespace TMG.Emme.Test.Generate
{
    [TestClass]
    public class GenerateTimePeriodNetworksTest : TestBase
    {
        [TestMethod]
        public void GenerateTimePeriodNetworks()
        {
            const int baseScenarioNumber = 1;
            Helper.ImportNetwork(baseScenarioNumber, "TestFiles/test.nwp");

            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Generate.generate_time_period_networks",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("base_scenario_number", baseScenarioNumber);
                    writer.WriteString("transit_service_table_file", "Service Table.csv");
                    writer.WriteString("batch_edit_file", "Batch Line Edit.csv");
                    writer.WriteString("transit_aggregation_selection_table_file", "Aggregation.csv");
                    writer.WriteString("transit_alternative_table_file", "Alt File.csv");
                    writer.WriteString("attribute_aggregator", "vdf: force,length: sum,type: first,lanes: force,ul1: avg,ul2: force,ul3: force,dwt: sum,dwfac: force,ttf: force,us1: avg_by_length,us2: avg,us3: avg,ui1: avg,ui2: avg,ui3: avg,@stop: avg,@lkcap: avg,@lkspd: avg,@stn1: force,@stn2: force,@z407: avg");
                    writer.WriteString("connector_filter_attribute", "None");
                    writer.WriteString("default_aggregation", "Naive");
                    writer.WriteString("line_filter_expression", "line=______ xor line=TS____ xor line=GT____ xor line=T9____ xor line=T601__");
                    writer.WriteString("node_filter_attribute", "None");
                    writer.WriteString("stop_filter_attribute", "@stop");
                    writer.WriteString("transfer_mode_string", "tuy");
                    writer.WriteStartArray("time_periods");
                    writer.WriteStartObject();
                    writer.WriteString("name", "PM");
                    writer.WriteNumber("uncleaned_scenario_number", 30);
                    writer.WriteNumber("cleaned_scenario_number", 31);
                    writer.WriteString("uncleaned_description", "PM - Uncleaned Network");
                    writer.WriteString("cleaned_description", "PM - Cleaned Network");
                    writer.WriteString("start_time", "15:00");
                    writer.WriteString("end_time", "19:00");
                    writer.WriteString("scenario_network_update_file", "");
                    writer.WriteEndObject();
                    writer.WriteStartObject();
                    writer.WriteString("name", "EV");
                    writer.WriteNumber("uncleaned_scenario_number", 40);
                    writer.WriteNumber("cleaned_scenario_number", 41);
                    writer.WriteString("uncleaned_description", "EV - Uncleaned Network");
                    writer.WriteString("cleaned_description", "EV - Cleaned Network");
                    writer.WriteString("start_time", "19:00");
                    writer.WriteString("end_time", "24:00");
                    writer.WriteString("scenario_network_update_file", "");
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("additional_transit_alternative_table");
                    writer.WriteStartObject();
                    writer.WriteString("name", "alt_file_1");
                    writer.WriteString("alternative_table_file", "");
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void GenerateTimePeriodNetworksModule()
        {
            const int baseScenarioNumber = 1;
            Helper.ImportNetwork(baseScenarioNumber, "TestFiles/base_network.nwp");

            var timePeriods = new[]
            {

                new Emme.Generate.GenerateTimePeriodNetworks.TimePeriod()
                {
                    Name = "PM",
                    UncleanedScenarioNumber = Helper.CreateParameter(30),
                    CleanedScenarioNumber = Helper.CreateParameter(31),
                    UncleanedDescription = Helper.CreateParameter("PM - Uncleaned Network"),
                    CleanedDescription = Helper.CreateParameter("PM - Cleaned Network"),
                    StartTime = Helper.CreateParameter("15:00"),
                    EndTime = Helper.CreateParameter("19:00"),
                    ScenarioNetworkUpdateFile = Helper.CreateParameter(""),
                },

                new Emme.Generate.GenerateTimePeriodNetworks.TimePeriod()
                {
                    Name = "EV",
                    UncleanedScenarioNumber = Helper.CreateParameter(40),
                    CleanedScenarioNumber = Helper.CreateParameter(41),
                    UncleanedDescription = Helper.CreateParameter("EV - Uncleaned Network"),
                    CleanedDescription = Helper.CreateParameter("EV - Cleaned Network"),
                    StartTime = Helper.CreateParameter("19:00"),
                    EndTime = Helper.CreateParameter("24:00"),
                    ScenarioNetworkUpdateFile = Helper.CreateParameter(""),
                },

            };

            var addAltFiles = new[]
            {
                new Emme.Generate.GenerateTimePeriodNetworks.AdditionalTransitAlternativeTable()
                {
                    Name = "altFile_1",
                    AlternativeTableFile = Helper.CreateParameter(""),
                }
            };

            var module = new Emme.Generate.GenerateTimePeriodNetworks()
            {
                BaseScenarioNumber = Helper.CreateParameter(baseScenarioNumber),
                TransitServiceTableFile = Helper.CreateParameter(Path.GetFullPath("Service Table.csv")),
                BatchEditFile = Helper.CreateParameter(Path.GetFullPath("Batch Line Edit.csv")),
                TransitAggreggationSelectionTableFile = Helper.CreateParameter(Path.GetFullPath("Aggregation.csv")),
                TransitAlternativeTableFile = Helper.CreateParameter(Path.GetFullPath("Alt File.csv")),
                AttributeAggregator = Helper.CreateParameter(Path.GetFullPath("vdf: force,length: sum,type: first,lanes: force,ul1: avg,ul2: force,ul3: force,dwt: sum,dwfac: force,ttf: force,us1: avg_by_length,us2: avg,us3: avg,ui1: avg,ui2: avg,ui3: avg,@stop: avg,@lkcap: avg,@lkspd: avg,@stn1: force,@stn2: force,@z407: avg")),
                ConnectorFilterAttribute = Helper.CreateParameter(Path.GetFullPath("None")),
                DefaultAggregation = Helper.CreateParameter(Path.GetFullPath("Naive")),
                LineFilterExpression = Helper.CreateParameter(Path.GetFullPath("line=______ xor line=TS____ xor line=GT____ xor line=T9____ xor line=T601__")),
                NodeFilterAttribute = Helper.CreateParameter(Path.GetFullPath("None")),
                StopFilterAttribute = Helper.CreateParameter(Path.GetFullPath("@stop")),
                TransferModeString = Helper.CreateParameter(Path.GetFullPath("tuy")),
                TimePeriods = Helper.CreateParameters(timePeriods),
                AdditionalTransitAlternativeTables = Helper.CreateParameters(addAltFiles),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}

