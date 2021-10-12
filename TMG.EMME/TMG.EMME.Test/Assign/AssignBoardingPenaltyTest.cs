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
using System.IO;
using XTMF2;


namespace TMG.Emme.Test.Assign
{
    [TestClass]
    public class AssignBoardingPenaltyTest : TestBase
    {
        [TestMethod]
        public void AssignBoardingPenalty()
        {
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_boarding_penalty",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    //writer.WriteString("scenario_numbers", "1,2");
                    writer.WritePropertyName("scenario_numbers");
                    writer.WriteStartArray();
                    writer.WriteNumberValue(1);
                    //writer.WriteNumberValue(2);
                    writer.WriteEndArray();
                    writer.WriteString("penalty_filter_string", "GO Train: mode=r: 1.0: 1.0: 1.0");

                }), LogbookLevel.Standard));
        }
        [TestMethod]
        public void AssignBoardingPenaltyModule()
        {
            var module = new Emme.Assign.AssignBoardingPenalty()
            {
                Name = "AssignBoardingPenalty",
                //ScenarioNumbers = Helper.CreateParameter("1,2"),
                ScenarioNumbers = Helper.CreateParameter(new int[] { 1, 2 }),
                PenaltyFilterString = Helper.CreateParameter("GO Train: mode=r: 1.0: 1.0: 1.0")
            };
            module.Invoke(Helper.Modeller);
        }
    }
}