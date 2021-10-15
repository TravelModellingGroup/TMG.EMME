
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
using System.IO;
using XTMF2;

namespace TMG.Emme.Test.Utilities
{
    [TestClass]
    public class NetworkCalculatorTest : TestBase
    {
        [TestMethod]
        public void NetworkCalculator()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.utilities.network_calculator", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteNumber("domain", 0);
                    writer.WriteString("expression", "sqrt((xi - xj) ^ 2 + (yi - yj) ^ 2)");
                    writer.WriteString("node_selection", "all");
                    writer.WriteString("link_selection", "all");
                    writer.WriteString("transit_line_selection", "all");
                    writer.WriteString("result", "None");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void NetworkCalculatorModule()
        {
            var module = new TMG.Emme.Utilities.NetworkCalculator()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                Domain = Helper.CreateParameter(0),
                Expression = Helper.CreateParameter("sqrt((xi - xj) ^ 2 + (yi - yj) ^ 2)"),
                NodeSelection = Helper.CreateParameter("all"),
                LinkSelection = Helper.CreateParameter("all"),
                TransitLineSelection = Helper.CreateParameter("all"),
                Result = Helper.CreateParameter("None")

            };
            module.Invoke(Helper.Modeller);
        }

    }
}