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
using System;
using System.IO;
using System.Text;
using System.Text.Json;

namespace TMG.Emme.Test.Import
{
    [TestClass]
    public class ImportNetworkPackageTest : TestBase
    {
        [TestMethod]
        public void ImportNetworkPackage()
        {
            Helper.ImportFrabitztownNetwork(1);
        }

        [TestMethod]
        public void ImportNetworkPackageModule()
        {
            var importModule = new Emme.Import.ImportNetworkPackage()
            {
                Name = "Importer",
                ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
                NetworkPackageFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/test.nwp"), "NWP File Name"),
                ScenarioDescription = Helper.CreateParameter("From XTMF","Description")
            };
            importModule.Invoke(Helper.Modeller);
        }
    }
}
