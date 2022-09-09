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


namespace TMG.Emme.Test.Export
{
    [TestClass]
    public class ExportSubareaTest : TestBase
    {
        [TestMethod]
        public void ExportSubarea()
        {
            Helper.ImportFrabitztownNetwork(1);
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Export.export_subarea",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteString("i_subarea_link_selection", "i=21,24 or i=27 or i=31,34");
                    writer.WriteString("j_subarea_link_selection", "j=21,24 or j=27 or j=31,34");
                    writer.WriteNumber("scenario_number", 1);
                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void ExportSubareaModule()
        {

            var module = new Emme.Export.ExportSubarea()
            {
                Name = "Export Subarea",
                ScenarioNumber = Helper.CreateParameter(1),
                ISubareaLinkSelection = Helper.CreateParameter("i=21,24 or i=27 or i=31,34"),
                JSubareaLinkSelection = Helper.CreateParameter("j=21,24 or j=27 or j=31,34")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}