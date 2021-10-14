/*
    Copyright 2021 University of Toronto

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
using System.Linq;
using System.IO;
using XTMF2;

namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportNetworkShapefileTest : TestBase
    {
        [TestMethod]
        public void ExportNetworkShapefile()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_network_shapefile",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteString("export_path", Path.GetFullPath("OutputTestFiles/exportedSHP.shp"));
                    //----transit_shapes = SEGEMENTS, LINES, OR LINES_AND_SEGMENTS
                    writer.WriteString("transit_shapes", "SEGMENTS");
                }), LogbookLevel.Standard));

        }

        [TestMethod]
        public void ExportNetworkShapefileModule()
        {
            var module = new TMG.Emme.Export.ExportNetworkShapefile()
            {
                ScenarioNumbers = Helper.CreateParameter(1),
                SaveTo = Helper.CreateParameter(Path.GetFullPath("OutputTestFiles/exportedSHP_m.shp")),
                TransitShapes = Helper.CreateParameter("SEGMENTS"),

            };
            module.Invoke(Helper.Modeller);
        }
    }
}