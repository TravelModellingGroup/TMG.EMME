
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

namespace TMG.Emme.Test.Calculate
{
    [TestClass]
    public class CalculateNetworkAttributeTest : TestBase
    {
        [TestMethod]
        public void CalculateNetworkAttributeLink()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Calculate.calculate_network_attribute", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteNumber("domain", (int)Emme.Calculate.CalculateNetworkAttribute.Domains.Link);
                    writer.WriteString("expression", "sqrt((xi - xj) ^ 2 + (yi - yj) ^ 2)");
                    writer.WriteString("node_selection", "all");
                    writer.WriteString("link_selection", "all");
                    writer.WriteString("transit_line_selection", "all");
                    writer.WriteString("result", "None");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void NetworkCalculatorModuleLink()
        {
            var module = new TMG.Emme.Calculate.CalculateNetworkAttribute()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                Domain = Helper.CreateParameter(Emme.Calculate.CalculateNetworkAttribute.Domains.Link),
                Expression = Helper.CreateParameter("sqrt((xi - xj) ^ 2 + (yi - yj) ^ 2)"),
                NodeSelection = Helper.CreateParameter("all"),
                LinkSelection = Helper.CreateParameter("all"),
                TransitLineSelection = Helper.CreateParameter("all"),
                Result = Helper.CreateParameter("None")
            };
            module.Invoke(Helper.Modeller);
        }
        [TestMethod]
        public void NetworkCalculatorNode()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Calculate.calculate_network_attribute", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteNumber("domain", (int)Emme.Calculate.CalculateNetworkAttribute.Domains.Node);
                    writer.WriteString("expression", "sqrt((xi) ^ 2 + (yi ) ^ 2)");
                    writer.WriteString("node_selection", "all");
                    writer.WriteString("link_selection", "all");
                    writer.WriteString("transit_line_selection", "all");
                    writer.WriteString("result", "None");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void NetworkCalculatorModuleNode()
        {
            var module = new TMG.Emme.Calculate.CalculateNetworkAttribute()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                Domain = Helper.CreateParameter(Emme.Calculate.CalculateNetworkAttribute.Domains.Node),
                Expression = Helper.CreateParameter("sqrt((xi) ^ 2 + (yi) ^ 2)"),
                NodeSelection = Helper.CreateParameter("all"),
                LinkSelection = Helper.CreateParameter("all"),
                TransitLineSelection = Helper.CreateParameter("all"),
                Result = Helper.CreateParameter("None")
            };
            module.Invoke(Helper.Modeller);
        }
        [TestMethod]
        public void NetworkCalculatorTransitLine()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Calculate.calculate_network_attribute", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteNumber("domain", (int)Emme.Calculate.CalculateNetworkAttribute.Domains.TransitLine);
                    writer.WriteString("expression", "ut1");
                    writer.WriteString("node_selection", "None");
                    writer.WriteString("link_selection", "None");
                    writer.WriteString("transit_line_selection", "all");
                    writer.WriteString("result", "ut2");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void NetworkCalculatorModuleTransitLine()
        {
            var module = new TMG.Emme.Calculate.CalculateNetworkAttribute()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                Domain = Helper.CreateParameter(Emme.Calculate.CalculateNetworkAttribute.Domains.TransitLine),
                Expression = Helper.CreateParameter("ut1"),
                NodeSelection = Helper.CreateParameter("None"),
                LinkSelection = Helper.CreateParameter("None"),
                TransitLineSelection = Helper.CreateParameter("all"),
                Result = Helper.CreateParameter("ut2")
            };
            module.Invoke(Helper.Modeller);
        }
        [TestMethod]
        public void NetworkCalculatorTransitSegment()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Calculate.calculate_network_attribute", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario_number", 1);
                    writer.WriteNumber("domain", (int)Emme.Calculate.CalculateNetworkAttribute.Domains.TransitSegment);
                    writer.WriteString("expression", "sqrt((xi) ^ 2 + (yi ) ^ 2)");
                    writer.WriteString("node_selection", "None");
                    writer.WriteString("link_selection", "all");
                    writer.WriteString("transit_line_selection", "all");
                    writer.WriteString("result", "us1");
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void NetworkCalculatorModuleTransitSegment()
        {
            var module = new TMG.Emme.Calculate.CalculateNetworkAttribute()
            {
                ScenarioNumber = Helper.CreateParameter(1),
                Domain = Helper.CreateParameter(Emme.Calculate.CalculateNetworkAttribute.Domains.TransitSegment),
                Expression = Helper.CreateParameter("sqrt((xi) ^ 2 + (yi ) ^ 2)"),
                NodeSelection = Helper.CreateParameter("None"),
                LinkSelection = Helper.CreateParameter("all"),
                TransitLineSelection = Helper.CreateParameter("all"),
                Result = Helper.CreateParameter("us1")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}