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
using System.IO;
using System.Text;
using System.Text.Json;

namespace TMG.Emme.Test.Import
{
    [TestClass]
    public class ImportTransitLinesFromGtfsTest : TestBase
    {
        [TestMethod]
        public void ImportGTFS()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Import.import_transit_lines_from_gtfs",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteNumber("scenario_id", 1);
                     writer.WriteNumber("max_non_stop_nodes", 15);
                     writer.WriteString("link_priority_attribute", "");
                     writer.WriteString("gtfs_folder", Path.GetFullPath("TestFiles/FrabtiztownGTFS"));
                     writer.WriteString("stop_to_node_file", Path.GetFullPath("TestFiles/FrabtiztownGTFS/stop_to_node.csv"));
                     writer.WriteNumber("new_scenario_id", 2);
                     writer.WriteString("new_scenario_title", "Test Transit Network");
                     writer.WriteString("service_table_file", "ServiceTable");
                     writer.WriteString("mapping_file", "mapping");
                     writer.WriteBoolean("publish_flag", true);
                 }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void ImportGTFSModule()
        {
            var module = new Emme.Import.ImportTransitLinesFromGtfs()
            {
                Name = "ImportGTFS",
                BaseScenario = Helper.CreateParameter(1, "Base Scenario ID"),
                MaxNonStopNodes = Helper.CreateParameter(15, "Max Interstop Links"),
                LinkPriorityAttributeId = Helper.CreateParameter("", "Link Priority Attribute"),
                GtfsFolder = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabtiztownGTFS"), "GTFS Folder Names"),
                StopToNodeFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabtiztownGTFS/stop_to_node.csv"), "Stop-to-node File"),
                NewScenarioId = Helper.CreateParameter(2, "New Scenario ID"),
                NewScenarioTitle = Helper.CreateParameter("Test Transit Network", "New Scenario Title"),
                LineServiceTableFile = Helper.CreateParameter("ServiceTable", "Service Table Output File"),
                MappingFileName = Helper.CreateParameter("mapping", "Mapping File"),
                PublishFlag = Helper.CreateParameter(true, "Publish Network"),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}