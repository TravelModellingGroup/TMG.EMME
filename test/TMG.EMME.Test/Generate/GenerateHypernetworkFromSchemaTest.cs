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
using System.IO;

namespace TMG.Emme.Test.Generate;

[TestClass]
public class GenerateHypernetworkFromSchemaTest : TestBase
{
    const int BaseScenario = 1;
    const int HyperNetworkScenario = 2;

    public static void SetupTest()
    {
        Helper.ImportFrabitztownNetwork(BaseScenario);
    }

    [TestMethod]
    public void GenerateHypernetworkFromSchema()
    {
        SetupTest();

        Assert.IsTrue(
            Helper.Modeller.Run(null, "tmg2.Generate.generate_hypernetwork_from_schema",
            JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteNumber("base_scenario", BaseScenario);
                writer.WriteNumber("new_scenario", HyperNetworkScenario);
                writer.WriteString("new_scenario_title", "GTAModel_Hypernetwork");
                writer.WriteBoolean("station_connector_flag", true);
                writer.WriteString("transfer_mode", "t");
                writer.WriteNumber("virtual_node_domain", 100000);
                writer.WriteString("base_schema_file", Path.GetFullPath("TestFiles/FrabitztownNetwork/FareBase.xml"));
                writer.WriteStartArray("fare_classes");
                writer.WriteStartObject();
                writer.WriteString("link_fare_attribute", "@lfare");
                writer.WriteString("segment_fare_attribute", "@sfare");
                writer.WriteString("schema_file", Path.GetFullPath("TestFiles/FrabitztownNetwork/FareClass.xml"));
                writer.WriteEndObject();
                writer.WriteEndArray();
            }), LogbookLevel.Standard));
    }

    [TestMethod]
    public void GenerateHypernetworkFromSchemaModule()
    {
        SetupTest();

        var fareClass = new[]
        {
            new Emme.Generate.GenerateHypernetworkFromSchema.FareClass()
            {
                Name = "FareClass",
                LinkFareAttribute = Helper.CreateParameter("@lfare"),
                SegmentFareAttribute = Helper.CreateParameter("@sfare"),
                SchemaFile = Helper.CreateParameter(Path.GetFullPath("TestFiles/FrabitztownNetwork/FareClass.xml"))
            }
        };

        var generateModule = new Emme.Generate.GenerateHypernetworkFromSchema()
        {
            Name = "Generator",
            BaseScenario = Helper.CreateParameter(BaseScenario),
            NewScenario = Helper.CreateParameter(HyperNetworkScenario),
            NewScenarioTitle = Helper.CreateParameter("GTAModel_Hypernetwork"),
            StationConnectorFlag = Helper.CreateParameter(true),
            TransferMode = Helper.CreateParameter("t"),
            VirtualNodeDomain = Helper.CreateParameter(100000),
            BaseSchemaFile = Helper.CreateParameter(Path.GetFullPath(("TestFiles/FrabitztownNetwork/FareBase.xml"))),
            FareClasses = Helper.CreateParameters(fareClass),
        };
        generateModule.Invoke(Helper.Modeller);
    }
}
