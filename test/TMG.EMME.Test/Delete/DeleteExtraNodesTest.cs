/*
    Copyright 2026 University of Toronto

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
using System.IO;
using System.Text;

namespace TMG.Emme.Test.Delete;

[TestClass]
public class DeleteExtraNodesTest : TestBase
{
    const int ScenarioNumber = 1;
    const string AttributeAggregators = "vdf: force,length: sum,type: first,lanes: avg,ul1: avg,ul2: force,ul3: avg,dwt: sum,dwfac: force,ttf: force,us1: avg_by_length,us2: avg,us3: avg,ui1: avg,ui2: avg,ui3: avg";

    [TestMethod]
    public void TestDeleteExtraNodes()
    {
        Helper.ImportFrabitztownNetwork(ScenarioNumber);

        Assert.IsTrue(
        Helper.Modeller.Run(null, "tmg2.Delete.delete_extra_nodes", JSONParameterBuilder.BuildParameters(writer =>
        {
            writer.WriteNumber("scenario", ScenarioNumber);
            writer.WriteNull("node_filter_attribute_id");
            writer.WriteNull("stop_filter_attribute_id");
            writer.WriteNull("connector_filter_attribute_id");
            writer.WriteString("attribute_aggregator_string", AttributeAggregators);
        }), LogbookLevel.Standard));
    }

}
