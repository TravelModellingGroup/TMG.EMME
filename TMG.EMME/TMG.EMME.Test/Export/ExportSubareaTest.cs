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


namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportSubareaTest : TestBase
    {
        [TestMethod]
        public void ExportSubarea()
        {
            Helper.ImportFrabitztownNetwork(3);
            Helper.ImportNetwork(3, "TestFiles/test.nwp", "Frab Subarea Network");
            Helper.ImportBinaryMatrix(3, 10, Path.GetFullPath("TestFiles/Test0.25.mtx"));
            Helper.RunAssignTraffic(3, "mf10", 11);
            Helper.ImportBinaryMatrix(3, 10, Path.GetFullPath("TestFiles/TestHighDemand.mtx"));
            Helper.RunAssignBoardingPenalty(new[] { 3 });
            Helper.RunAssignTransit(3, "mf10");
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_subarea",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("extract_transit", true);
                    writer.WriteBoolean("create_gate_attribute", true);
                    writer.WriteString("i_subarea_link_selection", "i=21,24 or i=27 or i=31,34");
                    writer.WriteString("j_subarea_link_selection", "j=21,24 or j=27 or j=31,34");
                    writer.WriteNumber("scenario_number", 3);
                    writer.WriteString("shape_file_location", Path.GetFullPath("TestFiles/FrabitztownShapefiles/frab_border.shp"));
                    writer.WriteString("subarea_output_folder", Path.GetDirectoryName("TestFiles/Subarea/"));
                    writer.WriteBoolean("create_nflag_from_shapefile", true);
                    writer.WriteString("subarea_node_attribute", "@nflag");
                    writer.WriteString("subarea_gate_attribute", "@gate");
                    writer.WriteBoolean("background_transit", true);
                    writer.WriteNumber("br_gap", 0);
                    writer.WriteNumber("iterations", 4);
                    writer.WriteNumber("norm_gap", 0);
                    writer.WriteBoolean("performance_flag", true);
                    writer.WriteNumber("r_gap", 0);
                    writer.WriteString("run_title", "road assignment");
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
                    writer.WriteString("demand_matrix", "mf10");
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
        [TestMethod]
        public void ExportSubareaModule()
        {

            var module = new Emme.Export.ExportSubarea()
            {
                Name = "Export Subarea",
                ScenarioNumber = Helper.CreateParameter(3),
                ISubareaLinkSelection = Helper.CreateParameter("i=21,24 or i=27 or i=31,34"),
                JSubareaLinkSelection = Helper.CreateParameter("j=21,24 or j=27 or j=31,34"),
                ShapefileLocation = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabitztownShapefiles/frab_border.shp")),
                SubareaOutputFolder = Helper.CreateParameter(Path.GetDirectoryName("TestFiles/SubareaOutput")),
                CreateNflagFromShapefile = Helper.CreateParameter(true),
                SubareaNodeAttribute = Helper.CreateParameter("@nflag"),
                SubareaGateAttribute = Helper.CreateParameter("@gate"),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}