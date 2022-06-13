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

namespace TMG.Emme.Test.Convert
{
    [TestClass]
    public class ConvertOldNCS2NewNCSTest : TestBase
    {
        [TestMethod]
        public void ConvertOldNCS2NewNCS()
        {
            const int scenarioNumber = 1;
            Helper.ImportNetwork(scenarioNumber, "TestFiles/base_network.nwp");
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Convert.convert_old_ncs_to_new_ncs",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("old_ncs_scenario", scenarioNumber);
                    writer.WriteNumber("new_ncs_scenario", 2);
                    writer.WriteString("station_centroid_file", "TestFiles/zone_centriods.csv");
                    writer.WriteString("zone_centroid_file", "TestFiles/zone_centriods_map.csv");

                }), LogbookLevel.Standard));

        }
        [TestMethod]
        public void ConvertOldNCS2NewNCSModule()
        {

            const int scenarioNumber = 1;
            Helper.ImportNetwork(scenarioNumber, "TestFiles/base_network.nwp");
            var module = new Emme.Convert.ConvertOldNCS2NewNCS()
            {
                OldScenarioNumber = Helper.CreateParameter(scenarioNumber),
                NewScenarioNumber = Helper.CreateParameter(2),
                StationCentroidFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/zone_centriods_map.csv")),
                ZoneCentroidFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/zone_centriods.csv")),

            };

            module.Invoke(Helper.Modeller);
        }
    }
}

