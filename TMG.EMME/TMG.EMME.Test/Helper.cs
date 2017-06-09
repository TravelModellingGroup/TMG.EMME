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
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace TMG.Emme.Test
{
    internal static class Helper
    {
        static Helper()
        {
            //Load the configuration
            var configFile = new FileInfo("TMG.EMME.Test.Configuration.json");
            if (!configFile.Exists)
            {
                Assert.Fail("Configuration file \"TMG.EMME.Test.Configuration.json\" does not exist please create it to run tests.");
            }
            else
            {
                using (var reader = new JsonTextReader(configFile.OpenText()))
                {
                    while(reader.Read())
                    {
                        if(reader.TokenType == JsonToken.PropertyName)
                        {
                            switch(reader.Value)
                            {
                                case "ProjectFile":
                                    ProjectFile = reader.ReadAsString();
                                    break;
                            }
                        }
                    }
                }
            }
            Modeller = new ModellerController(null, ProjectFile);
        }

        public static string ProjectFile { get; private set; }
        public static ModellerController Modeller { get; private set; }
    }
}
