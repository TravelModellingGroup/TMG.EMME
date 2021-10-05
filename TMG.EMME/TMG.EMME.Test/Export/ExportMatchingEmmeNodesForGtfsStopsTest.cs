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
using System;
using System.IO;
using System.Text;
using System.Text.Json;

namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportMatchingEmmeNodesForGtfsStopsTest : TestBase
    {
        [TestMethod]
        public void MappingStopToNode()
        {
            string outputFolderName = Path.GetFullPath("OutputTestFiles");
            
            if (!Directory.Exists(outputFolderName))
            {
                Directory.CreateDirectory(outputFolderName);
            }

            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_matching_emme_nodes_for_gtfs_stops",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteString("input_stop_file", Path.GetFullPath("TestFiles/FrabtiztownGTFS/stops.txt"));
                     writer.WriteString("output_mapping_file", Path.GetFullPath("OutputTestFiles/stop_to_node.csv"));
                 }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void MappingStopToNodeModule()
        {
            var module = new Emme.Export.ExportMatchingEmmeNodesForGtfsStops()
            {
                Name = "MappingGtfsStopsToNodes",
                StopsInputFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabtiztownGTFS/stops.txt"), "Stops Input File"),
                MappingOutputFile = Helper.CreateParameter(Path.GetFullPath("OutputTestFiles/stop_to_node.csv"), "Mapping Output File"),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}