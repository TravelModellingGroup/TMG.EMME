/*
    Copyright 2023 University of Toronto

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

namespace TMG.Emme.Test.Calculate
{
    [TestClass]
    public class CalculateBackgroundTrafficTest : TestBase
    {
        [TestMethod]
        public void CalculateBackgroundTraffic()
        {
            var scenarioNumber = 2;
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Calculate.calculate_background_traffic",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WritePropertyName("interval_length_list");
                    writer.WriteStartArray();
                    writer.WriteNumberValue(60);
                    writer.WriteNumberValue(60);
                    writer.WriteNumberValue(60);
                    writer.WriteEndArray();
                    writer.WriteString("link_component_attribute", "@tvph");
                    writer.WriteNumber("start_index", 1);
                    writer.WritePropertyName("mixed_use_ttf_ranges");
                    writer.WriteStartArray();
                    writer.WriteStartObject();
                    writer.WriteNumber("start", 3);
                    writer.WriteNumber("stop", 128);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void CalculateBackgroundTrafficModule()
        {
            var module = new Emme.Calculate.CalculateBackgroundTraffic()
            {};
            module.Invoke(Helper.Modeller);
        }
    }
}
