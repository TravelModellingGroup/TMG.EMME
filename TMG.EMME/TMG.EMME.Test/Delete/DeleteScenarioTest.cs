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
using System.IO;
using System.Text.Json;

namespace TMG.Emme.Test.Delete
{
    [TestClass]
    public class DeleteScenarioTest : TestBase
    {
        [TestMethod]
        public void DeleteScenario()
        {
            Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Delete.delete_scenario", JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteNumber("scenario", 2);
                }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void DeleteScenarioModule()
        {
            var module = new Emme.Delete.DeleteScenario()
            {
                Name = "DeleteScenario",
                Scenario = Helper.CreateParameter(2, "Delete"),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
