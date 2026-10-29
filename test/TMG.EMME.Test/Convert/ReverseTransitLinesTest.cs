/*
    Copyright 2022-2026 University of Toronto
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

namespace TMG.Emme.Test.Convert;

[TestClass]
public class ReverseTransitLinesTest : TestBase
{
    const int ScenarioNumber = 1;

    private static void SetupTest()
    {
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
    }   

    [TestMethod]
    public void ReverseTransitLines()
    {
        SetupTest();
        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Convert.reverse_transit_lines",
            JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("scenario_number", ScenarioNumber);
                writer.WriteString("line_selector_expression", "mode=r");
            }), LogbookLevel.Standard));
    }

    [TestMethod]
    public void ReverseTransitLinesModule()
    {
        SetupTest();
        var module = new Emme.Convert.ReverseTransitLines()
        {
            Name = "ReverseTransitLines",
            ScenarioNumber = Helper.CreateParameter(ScenarioNumber),
            LineSelectorExpression = Helper.CreateParameter("mode=r"),
        };
        module.Invoke(Helper.Modeller);
    }
}
