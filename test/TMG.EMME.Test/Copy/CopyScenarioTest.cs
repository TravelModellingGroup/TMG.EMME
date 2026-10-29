/*
    Copyright 2017-2026 University of Toronto

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

namespace TMG.Emme.Test.Copy;

[TestClass]
public class CopyScenarioTest : TestBase
{
    const int BaseScenario = 1;
    const int WriteToScenario = 2;

    [TestMethod]
    public void CopyScenario()
    {
        Helper.ImportFrabitztownNetwork(BaseScenario);
        Assert.IsTrue(
        Helper.Modeller.Run(null, "tmg2.Copy.copy_scenario", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("from_scenario", BaseScenario);
                writer.WriteNumber("to_scenario", WriteToScenario);
                writer.WriteBoolean("copy_strategy", false);
            }), LogbookLevel.Standard));
    }

    [TestMethod]
    public void CopyScenarioModule()
    {
        Helper.ImportFrabitztownNetwork(BaseScenario);
        var module = new Emme.Copy.CopyScenario()
        {
            Name = "CopyScenario",
            FromScenario = Helper.CreateParameter(BaseScenario, "From"),
            ToScenario = Helper.CreateParameter(WriteToScenario, "To"),
            CopyStrategy = Helper.CreateParameter(false, "Copy Assignments")
        };
        module.Invoke(Helper.Modeller);
    }
}
