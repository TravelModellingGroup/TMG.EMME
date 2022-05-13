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
using XTMF2;

namespace TMG.Emme.Test.Convert
{
    [TestClass]
    public class RotateNetworkTest : TestBase
    {
        [TestMethod]
        public void RotateNetwork()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Convert.rotate_network",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 2);

                    writer.WriteNumber("reference_link_i_node", 10048);
                    writer.WriteNumber("reference_link_j_node", 11);

                    writer.WriteNumber("corresponding_x_0", 511713.7);
                    writer.WriteNumber("corresponding_y_0", 9161352);

                    writer.WriteNumber("corresponding_x_1", 511722.1);
                    writer.WriteNumber("corresponding_y_1", 9161122);
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void RotateNetworkModule()
        {
            var module = new Emme.Convert.RotateNetwork()
            {
                Name = "RotateNetwork",
                ScenarioNumber = Helper.CreateParameter(2),

                ReferenceLinkINode = Helper.CreateParameter(10048),
                ReferenceLinkJNode = Helper.CreateParameter(11),

                CorrespondingX0 = Helper.CreateParameter(511713.7f),
                CorrespondingY0 = Helper.CreateParameter(9161352f),
                CorrespondingX1 = Helper.CreateParameter(511722.1f),
                CorrespondingY1 = Helper.CreateParameter(9161122f)
            };
            module.Invoke(Helper.Modeller);
        }
    }
}