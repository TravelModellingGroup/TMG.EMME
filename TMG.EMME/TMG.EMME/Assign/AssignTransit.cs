/*
    Copyright 2021 University of Toronto

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

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Assign
{
    [Module(Name = "Assign Demand To Road Network", Description = "",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class AssignTransit : BaseAction<ModellerController>
    {
		[Parameter(Name = "Calculate Congested Ivtt Flag", Description = "",
			Index = 0)]
		public IFunction<bool> CalculateCongestedIvttFlag;

		[Parameter(Name = "Node Logit Scale", Description = "",
			Index = 1)]
		public IFunction<bool> NodeLogitScale;

		[Parameter(Name = "Effective Headway Attribute Id", Description = "",
			Index = 2)]
		public IFunction<string> EffectiveHeadwayAttributeId;

		[Parameter(Name = "Effective Headway Slope", Description = "",
			Index = 3)]
		public IFunction<float> EffectiveHeadwaySlope;

		[Parameter(Name = "Headway Fraction Attribute Id", Description = "",
			Index = 4)]
		public IFunction<string> HeadwayFractionAttributeId;

		[Parameter(Name = "Iterations", Description = "",
			Index = 5)]
		public IFunction<int> Iterations;

		[Parameter(Name = "Norm Gap", Description = "",
			Index = 6)]
		public IFunction<float> NormalizedGap;

		[Parameter(Name = "Rel Gap", Description = "",
			Index = 7)]
		public IFunction<float> RelativeGap;

		[Parameter(Name = "Scenario Number", Description = "",
			Index = 8)]
		public IFunction<int> ScenarioNumber;

		[Parameter(Name = "Walk Speed", Description = "",
			Index = 9)]
		public IFunction<float> WalkSpeed;
		
		[Parameter(Name = "Congestion Exponent", Description = "",
			Index = 26)]
		public IFunction<string> CongestionExponent;

		[Parameter(Name = "Assignment Period", Description = "",
			Index = 27)]
		public IFunction<float> AssignmentPeriod;

		[Parameter(Name = "Name String", Description = "",
			Index = 28)]
		public IFunction<string> NameString;

		[Parameter(Name = "Congested Assignment", Description = "",
			Index = 29)]
		public IFunction<string> CongestedAssignment;

		[Parameter(Name = "CSV File", Description = "",
			Index = 30)]
		public IFunction<string> CSVFile;

		[Parameter(Name = "Origin Distribution Logit Scale", Description = "",
			Index = 31)]
		public IFunction<float> OriginDistributionLogitScale;

		[Parameter(Name = "Walk Distribution Logit Scale", Description = "",
			Index = 32)]
		public IFunction<float> WalkDistributionLogitScale;

		[Parameter(Name = "Surface Transit Speed", Description = "",
			Index = 33)]
		public IFunction<string> SurfaceTransitSpeed;

		[Parameter(Name = "Walk All Way Flag", Description = "",
			Index = 34)]
		public IFunction<bool> WalkAllWayFlag;

		[Parameter(Name = "Xrow TTF Range", Description = "",
			Index = 35)]
		public IFunction<string> XRowTTFRange;

		[SubModule(Name = "Transit Classes", Description = "", Index = 0)]
		public IFunction<TransitClass>[] TransitClasses;

		[Module(Name = "Transit Class", Description = "",
		DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
		
		public class TransitClass : XTMF2.IModule
		{
			[Parameter(Name = "Board Penalty Matrix", Description = "",
				Index = 0)]
			public IFunction<string> BoardPenaltyMatrix;

			[Parameter(Name = "Board Penalty Perception", Description = "",
				Index = 1)]
			public IFunction<float> BoardingPenaltyPerception;

			[Parameter(Name = "Congestion Matrix", Description = "",
				Index = 2)]
			public IFunction<string> CongestionMatrix;

			[Parameter(Name = "Demand Matrix", Description = "",
				Index = 3)]
			public IFunction<string> DemandMatrix;

			[Parameter(Name = "Fare Matrix", Description = "",
				Index = 4)]
			public IFunction<string> FareMatrix;

			[Parameter(Name = "Fare Perception", Description = "",
				Index = 5)]
			public IFunction<float> FarePerception;

			[Parameter(Name = "InVehicle Time Matrix", Description = "",
				Index = 6)]
			public IFunction<string> InVehicleTimeMatrix;

			[Parameter(Name = "Impedance Matrix", Description = "",
			Index = 25)]
			public IFunction<string> ImpedanceMatrix;

			[Parameter(Name = "Link Fare Attribute Id", Description = "",
				Index = 7)]
			public IFunction<string> LinkFareAttributeId;

			[Parameter(Name = "Mode", Description = "",
				Index = 8)]
			public IFunction<string> Mode;

			[Parameter(Name = " Perceived Travel Time Matrix", Description = "",
				Index = 9)]
			public IFunction<string> PerceivedTravelTimeMatrix;

			[Parameter(Name = "Segment Fare Attribute Id", Description = "",
				Index = 10)]
			public IFunction<string> SegmentFareAttributeId;

			[Parameter(Name = "Wait Time Perception", Description = "",
				Index = 11)]
			public IFunction<float> WaitTimePerception;

			[Parameter(Name = "Wait Time Matrix", Description = "",
				Index = 12)]
			public IFunction<string> WaitTimeMatrix;

			[Parameter(Name = "Walk Time Perception Attribute Id", Description = "",
				Index = 13)]
			public IFunction<string> WalkTimePerceptionAttributeId;

			[Parameter(Name = "Walk Time Matrix", Description = "",
				Index = 14)]
			public IFunction<string> WalkTimeMatrix;

			[SubModule(Name = "Walk Perceptions", Description = "", Index = 9, Required = false)]
			public IFunction<WalkPerceptions>[] WalkPerceptions;

			public string Name { get; set; }

			public bool RuntimeValidation(ref string error)
			{
				return true;
			}

			public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
			{
				writer.WriteStartObject();
				writer.WriteString("name", Name);
				writer.WriteString("board_penalty_matrix", BoardPenaltyMatrix.Invoke());
				writer.WriteNumber("board_penalty_perception", BoardingPenaltyPerception.Invoke());
				writer.WriteString("congestion_matrix", CongestionMatrix.Invoke());
				writer.WriteString("demand_matrix", DemandMatrix.Invoke());
				writer.WriteString("fare_matrix", FareMatrix.Invoke());
				writer.WriteNumber("fare_perception", FarePerception.Invoke());
				writer.WriteString("in_vehicle_time_matrix", InVehicleTimeMatrix.Invoke());
				writer.WriteString("impedance_matrix", ImpedanceMatrix.Invoke());
				writer.WriteString("link_fare_attribute", LinkFareAttributeId.Invoke());
				writer.WriteString("mode", Mode.Invoke());
				writer.WriteString("perceived_travel_time_matrix", PerceivedTravelTimeMatrix.Invoke());
				writer.WriteString("segment_fare_attribute", SegmentFareAttributeId.Invoke());
				writer.WriteNumber("wait_time_perception", WaitTimePerception.Invoke());
				writer.WriteString("wait_time_matrix", WaitTimeMatrix.Invoke());
				writer.WriteString("walk_time_perception_attribute", WalkTimePerceptionAttributeId.Invoke());
				writer.WriteString("walk_time_matrix", WalkTimeMatrix.Invoke());
				writer.WriteStartArray("walk_perceptions");
				foreach (var walkPerceptions in WalkPerceptions)
				{
					walkPerceptions.Invoke().WriteParameters(writer);
				}
				writer.WriteEndArray();
				writer.WriteEndObject();
			}
		}

		[Module(Name = "Walk Perceptions", Description = "",
		DocumentationLink = "http://tzmg.utoronto.ca/doc/2.0")]
		public class WalkPerceptions : XTMF2.IModule
		{
			[Parameter(Name = "Filter", Description = "",
				Index = 0)]
			public IFunction<string> Filter;

			[Parameter(Name = "Walk Perception Value", Description = "",
				Index = 1)]
			public IFunction<float> WalkPerceptionValue;

			public string Name { get; set; }

			public bool RuntimeValidation(ref string error)
			{
				return true;
			}
			public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
			{
				writer.WriteStartObject();
				writer.WriteString("filter", Filter.Invoke());
				writer.WriteNumber("walk_perception_value", WalkPerceptionValue.Invoke());
				writer.WriteEndObject();
			}
		}
		public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Assign.assign_transit", JSONParameterBuilder.BuildParameters(writer =>
            {
				writer.WriteBoolean("calculate_congested_ivtt_flag", CalculateCongestedIvttFlag.Invoke());
				writer.WriteBoolean("node_logit_scale", NodeLogitScale.Invoke());
				writer.WriteString("effective_headway_attribute", EffectiveHeadwayAttributeId.Invoke());
				writer.WriteNumber("effective_headway_slope", EffectiveHeadwaySlope.Invoke());
				writer.WriteString("headway_fraction_attribute", HeadwayFractionAttributeId.Invoke());
				writer.WriteNumber("iterations", Iterations.Invoke());
				writer.WriteNumber("norm_gap", NormalizedGap.Invoke());
				writer.WriteNumber("rel_gap", RelativeGap.Invoke());
				writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
				writer.WriteNumber("walk_speed", WalkSpeed.Invoke());
				writer.WriteString("congestion_exponent", CongestionExponent.Invoke());
				writer.WriteNumber("assignment_period", AssignmentPeriod.Invoke());
				writer.WriteString("name_string", NameString.Invoke());
				writer.WriteString("congested_assignment", CongestedAssignment.Invoke());
				writer.WriteString("csvfile", CSVFile.Invoke());
				writer.WriteNumber("origin_distribution_logit_scale", OriginDistributionLogitScale.Invoke());
				writer.WriteNumber("walk_distribution_logit_scale", WalkDistributionLogitScale.Invoke());
				writer.WriteString("surface_transit_speed", SurfaceTransitSpeed.Invoke());
				writer.WriteBoolean("walk_all_way_flag", WalkAllWayFlag.Invoke());
				writer.WriteString("xrow_ttf_range", XRowTTFRange.Invoke());
				writer.WriteStartArray("transit_classes");
				foreach (var transitClass in TransitClasses)
				{
					transitClass.Invoke().WriteParameters(writer);
				}
				writer.WriteEndArray();

			}), LogbookLevel.Standard);
        }
    }
}
