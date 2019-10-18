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
using Newtonsoft.Json;
using System.IO;
using System.Text;

namespace TMG.Emme.Test.Copy
{
    [TestClass]
    public class CopyScenarioTest : TestBase
    {
        [TestMethod]
        public void CopyScenario()
        {
            string GetParameters()
            {
                string ret = null;
                using (MemoryStream backing = new MemoryStream())
                {
                    using (StreamWriter sWriter = new StreamWriter(backing, Encoding.Unicode, 0x4000, true))
                    using (JsonWriter writer = new JsonTextWriter(sWriter))
                    {
                        writer.WriteStartObject();
                        Helper.WriteProperty(writer, "from_scenario", 1);
                        Helper.WriteProperty(writer, "to_scenario", 2);
                        Helper.WriteProperty(writer, "copy_strategy", false);
                        writer.WriteEndObject();
                        writer.Flush();
                        sWriter.Flush();
                    }
                    backing.Position = 0;
                    using (StreamReader reader = new StreamReader(backing))
                    {
                        ret = reader.ReadToEnd();
                    }
                }
                return ret;
            }
            Assert.IsTrue(Helper.Modeller.Run(null, "tmg2.Copy.copy_scenario",
                new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", GetParameters()),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                }));
        }

        [TestMethod]
        public void CopyScenarioModule()
        {
            var module = new Emme.Copy.CopyScenario()
            {
                Name = "CopyScenario",
                FromScenario = Helper.CreateParameter(1, "From"),
                ToScenario = Helper.CreateParameter(2, "To"),
                CopyStrategy = Helper.CreateParameter(false, "Copy Assignments")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
