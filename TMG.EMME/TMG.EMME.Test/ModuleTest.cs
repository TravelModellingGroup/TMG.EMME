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
using System.Collections.Generic;
using System.Text;
using System.Reflection;

namespace TMG.Emme.Test
{
    [TestClass]
    public class ModuleTest
    {
        [TestMethod]
        public void LaunchXTMFRuntime()
        {
            // make sure that all of our module are loadable
            XTMF2.XTMFRuntime runtime = XTMF2.XTMFRuntime.CreateRuntime();
            runtime.SystemConfiguration.LoadAssembly(typeof(ModellerController).GetTypeInfo().Assembly);
        }
    }
}
