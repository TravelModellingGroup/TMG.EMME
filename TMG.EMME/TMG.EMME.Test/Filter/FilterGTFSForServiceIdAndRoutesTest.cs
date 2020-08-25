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

namespace TMG.Emme.Test.Filter
{
    [TestClass]
    public class FilterGTFSForServiceIdAndRoutesTest : TestBase
    {
        [TestMethod]
        public void CleanGTFS()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Filter.filter_gtfs_for_service_id_and_routes",
                 JSONParameterBuilder.BuildParameters(writer =>
                 {
                     writer.WriteString("gtfs_folder", Path.GetFullPath("TestFiles/FrabtiztownGTFS"));
                     writer.WriteString("service_id", "FrabtiztownTransit");
                     writer.WriteString("routes_file", "");
                 }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void CleanGTFSModule()
        {
            var module = new Emme.Filter.FilterGTFSForServiceIdAndRoutes()
            {
                Name = "FilterGTFS",
                GTFSFolder = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabtiztownGTFS"), "GTFS Folder Names"),
                ServiceID = Helper.CreateParameter("FrabtiztownTransit", "Service ID"),
                UpdatedRoutesFile = Helper.CreateParameter("", "Routes File")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}