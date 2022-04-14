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

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme.Assign
{
    [Module(Name = "Assign Transit To Road Network", Description = "Runs a multi-class transit assignment which executes a congested transit assignment procedure for the GTAModel V4.0.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class AssignTransit : BaseAction<ModellerController>
    {
        [Parameter(Name = "Calculate Congested Ivtt Flag", Description = "Set to TRUE to extract the congestion matrix and add its weighted value to the in vehicle time (IVTT) matrix.",
            Index = 0)]
        public IFunction<bool> CalculateCongestedIvttFlag;

        [Parameter(Name = "Node Logit Scale", Description = "This is the scale parameter for the logit model at critical nodes. Set it to 1 to turn it off logit. Set it to 0 to ensure equal proportion on all connected auxiliary transfer links. Critical nodes are defined as the non centroid end of centroid connectors and nodes that have transit lines from more than one agency",
            Index = 1)]
        public IFunction<float> NodeLogitScale;

        [Parameter(Name = "Effective Headway Attribute Id", Description = "The name of the attribute to use for the effective headway",
            Index = 2)]
        public IFunction<string> EffectiveHeadwayAttributeId;

        [Parameter(Name = "Effective Headway Slope", Description = "Effective Headway Slope",
            Index = 3)]
        public IFunction<float> EffectiveHeadwaySlope;

        [Parameter(Name = "Headway Fraction Attribute Id", Description = "The ID of the NODE extra attribute in which to store headway fraction. Should have a default value of 0.5.",
            Index = 4)]
        public IFunction<string> HeadwayFractionAttributeId;

        [Parameter(Name = "Iterations", Description = "Convergence criterion: The maximum number of iterations performed by the transit assignment.",
            Index = 5)]
        public IFunction<int> Iterations;

        [Parameter(Name = "Norm Gap", Description = "Convergence criterion.",
            Index = 6)]
        public IFunction<float> NormalizedGap;

        [Parameter(Name = "Rel Gap", Description = "Convergence criterion.",
            Index = 7)]
        public IFunction<float> RelativeGap;

        [Parameter(Name = "Scenario Number", Description = "Emme Scenario Number to execute against",
            Index = 8)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Walk Speed", Description = "Walking speed in km/hr. Applied to all walk (aux. transit) modes in the Emme scenario.",
            Index = 9)]
        public IFunction<float> WalkSpeed;

        [Parameter(Name = "Congestion Exponent", Description = "The congestion exponent to apply to this TTF.",
            Index = 26)]
        public IFunction<string> CongestionExponent;

        [Parameter(Name = "Assignment Period", Description = "A multiplier applied to the demand matrix to scale it to match" +
                    " the transit line capacity period. This is similar to the peak hour factor used in auto assignment.",
            Index = 27)]
        public IFunction<float> AssignmentPeriod;

        [Parameter(Name = "Name String", Description = "Name String",
            Index = 28)]
        public IFunction<string> NameString;

        [Parameter(Name = "Congested Assignment", Description = "Set this to false in order to not apply congestion during assignment.",
            Index = 29)]
        public IFunction<bool> CongestedAssignment;

        [Parameter(Name = "CSV File", Description = "A link to the csv file that will specify iterational information",
            Index = 30)]
        public IFunction<string> CSVFile;

        [Parameter(Name = "Origin Distribution Logit Scale", Description = "Scale parameter for logit model at origin connectors.",
            Index = 31)]
        public IFunction<float> OriginDistributionLogitScale;

        [Parameter(Name = "Surface Transit Speed", Description = "Set to TRUE to allow surface transit speed to be used in the assignment",
            Index = 33)]
        public IFunction<bool> SurfaceTransitSpeed;

        [Parameter(Name = "Walk All Way Flag", Description = "Set to TRUE to allow walk all way in the assignment",
            Index = 34)]
        public IFunction<bool> WalkAllWayFlag;

        [Parameter(Name = "Xrow TTF Range", Description = "Set this to the TTF, TTFs or range of TTFs (seperated by commas) that represent going in an exclusive right of way. This is for use in STSU",
            Index = 35)]
        public IFunction<string> XRowTTFRange;

        [SubModule(Name = "Transit Classes", Description = "The classes for this multi-class assignment.", Index = 36)]
        public IFunction<TransitClass>[] TransitClasses;

        [SubModule(Name = "Surface Transit Speed Model", Description = "Surface Transit Speed Model",
            Index = 37)]
        public IFunction<SurfaceTransitSpeedModel>[] SurfaceTransitSpeeds;

        [SubModule(Name = "TTF Definitions", Description = "The TTF's to apply in the assignment.",
            Index = 38)]
        public IFunction<TTFDefinition>[] TTFDefinitions;

        [Module(Name = "Transit Class", Description = "The classes for this multi-class assignment.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]

        public class TransitClass : XTMF2.IModule
        {
            [Parameter(Name = "Board Penalty Matrix", Description = "The number of the FULL matrix in which to save the applied boarding penalties.  Enter 0 to skip this matrix.",
                Index = 0)]
            public IFunction<string> BoardPenaltyMatrix;

            [Parameter(Name = "Board Penalty Perception", Description = "Perception factor applied to boarding penalty component.",
                Index = 1)]
            public IFunction<float> BoardingPenaltyPerception;

            [Parameter(Name = "Congestion Matrix", Description = "The ID of the FULL matrix in which to save transit congestion. Enter 0 to skip saving this matrix",
                Index = 2)]
            public IFunction<string> CongestionMatrix;

            [Parameter(Name = "Demand Matrix", Description = "The ID of the full matrix containing transit demand ODs",
                Index = 3)]
            public IFunction<string> DemandMatrix;

            [Parameter(Name = "Fare Matrix", Description = "The ID of the FULL matrix in which to save transit fares. Enter 0 to skip saving this matrix",
                Index = 4)]
            public IFunction<string> FareMatrix;

            [Parameter(Name = "Fare Perception", Description = "Perception factor applied to path transit fares, in $/hr.",
                Index = 5)]
            public IFunction<float> FarePerception;

            [Parameter(Name = "InVehicle Time Matrix", Description = "The ID of the FULL matrix in which to save in-vehicle travel time. Enter 0 to skip saving this matrix",
                Index = 6)]
            public IFunction<string> InVehicleTimeMatrix;

            [Parameter(Name = "Impedance Matrix", Description = "The ID of the FULL matrix in which to save the impedance.",
            Index = 25)]
            public IFunction<string> ImpedanceMatrix;

            [Parameter(Name = "Link Fare Attribute Id", Description = "The ID of the LINK extra attribute containing actual fare costs.",
                Index = 7)]
            public IFunction<string> LinkFareAttributeId;

            [Parameter(Name = "Mode", Description = "A character array of all the modes applied to this class. \'*\' selects all.",
                Index = 8)]
            public IFunction<string> Mode;

            [Parameter(Name = " Perceived Travel Time Matrix", Description = "The ID of the FULL matrix in which to save the incurred penalties. Enter 0 to skip saving this matrix",
                Index = 9)]
            public IFunction<string> PerceivedTravelTimeMatrix;

            [Parameter(Name = "Segment Fare Attribute Id", Description = "The ID of the SEGMENT extra attribute containing actual fare costs.",
                Index = 10)]
            public IFunction<string> SegmentFareAttributeId;

            [Parameter(Name = "Wait Time Perception", Description = "Perception factor applied to wait time component.",
                Index = 11)]
            public IFunction<float> WaitTimePerception;

            [Parameter(Name = "Wait Time Matrix", Description = "The ID of the FULL matrix in which to save total waiting time. Enter 0 to skip saving this matrix",
                Index = 12)]
            public IFunction<string> WaitTimeMatrix;

            [Parameter(Name = "Walk Time Perception Attribute Id", Description = "The ID of the LINK extra attribute in which to store walk time perception. Should have a default value of 1.0.",
                Index = 13)]
            public IFunction<string> WalkTimePerceptionAttributeId;

            [Parameter(Name = "Walk Time Matrix", Description = "The ID of the FULL matrix in which to save total walk time. Enter 0 to skip saving this matrix",
                Index = 14)]
            public IFunction<string> WalkTimeMatrix;

            [SubModule(Name = "Walk Perceptions", Description = "Contains the walk perception values fo this multi-class assignment", Index = 9, Required = false)]
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
                writer.WriteString("link_fare_attribute_id", LinkFareAttributeId.Invoke());
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
            [Parameter(Name = "Filter", Description = "The filter expression for links that the perception applies to e.g.: i=10000,20000 or j=10000,20000",
                Index = 0)]
            public IFunction<string> Filter;

            [Parameter(Name = "Walk Perception Value", Description = "The walk perception on links.",
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

        [Module(Name = "Surface Transit Speed Model", Description = "Model used to update surface transit speed",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class SurfaceTransitSpeedModel : XTMF2.IModule
        {
            [Parameter(Name = "Alighting Duration", Description = "The alighting duration in seconds per passenger to apply.",
                Index = 0)]
            public IFunction<float> AlightingDuration;

            [Parameter(Name = "Boarding Duration", Description = "The boarding duration in seconds per passenger to apply.",
                Index = 1)]
            public IFunction<float> BoardingDuration;

            [Parameter(Name = "Default Duration", Description = "The default duration in seconds per stop to apply.",
                Index = 2)]
            public IFunction<float> DefaultDuration;

            [Parameter(Name = "Global EROW Speed", Description = "The speed to use in segments that have Exclusive Right of Way for transit and do not have @erow_speed defined. Note that the speed includes accelaration and decelaration time.",
                Index = 3)]
            public IFunction<float> GlobalEROWSpeed;

            [Parameter(Name = "Line Filter Expression", Description = "he line filter that will be used to determing which lines will get surface transit speed applied to them. To select all lines, leave this and the line filter blank",
                Index = 4)]
            public IFunction<string> LineFilterExpression;

            [Parameter(Name = "Mode Filter Expression", Description = "The modes that will get surface transit speed updating applied to them. To select all lines, leave this and the line filter blank",
                Index = 5)]
            public IFunction<string> ModeFilterExpression;

            [Parameter(Name = "Transit Auto Correlation", Description = "The multiplier to auto time to use to find transit time.",
                Index = 6)]
            public IFunction<float> TransitAutoCorrelation;
            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteNumber("alighting_duration", AlightingDuration.Invoke());
                writer.WriteNumber("boarding_duration", BoardingDuration.Invoke());
                writer.WriteNumber("default_duration", DefaultDuration.Invoke());
                writer.WriteNumber("global_erow_speed", GlobalEROWSpeed.Invoke());
                writer.WriteString("line_filter_expression", LineFilterExpression.Invoke());
                writer.WriteString("mode_filter_expression", ModeFilterExpression.Invoke());
                writer.WriteNumber("transit_auto_correlation", TransitAutoCorrelation.Invoke());
                writer.WriteEndObject();
            }
        }

        [Module(Name = "TTF Definitions", Description = "The TTF's to apply in the assignment.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
        public class TTFDefinition : XTMF2.IModule
        {
            [Parameter(Name = "Congestion Exponent", Description = "The congestion exponent to apply to this TTF.",
                Index = 0)]
            public IFunction<float> CongestionExponent;

            [Parameter(Name = "Congestion Perception", Description = "The congestion perception to apply to this TTF.",
                Index = 1)]
            public IFunction<int> CongestionPerception;

            [Parameter(Name = "TTF", Description = "The TTF number to assign to. 1 would mean TTF1.",
                Index = 2)]
            public IFunction<int> TTF;
            public string Name { get; set; }

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }

            public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
            {
                writer.WriteStartObject();
                writer.WriteNumber("congestion_exponent", CongestionExponent.Invoke());
                writer.WriteNumber("congestion_perception", CongestionPerception.Invoke());
                writer.WriteNumber("ttf", TTF.Invoke());
                writer.WriteEndObject();
            }
        }
        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Assign.assign_transit", JSONParameterBuilder.BuildParameters(writer =>
            {
                writer.WriteBoolean("calculate_congested_ivtt_flag", CalculateCongestedIvttFlag.Invoke());
                writer.WriteNumber("node_logit_scale", NodeLogitScale.Invoke());
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
                writer.WriteBoolean("congested_assignment", CongestedAssignment.Invoke());
                writer.WriteString("csvfile", CSVFile.Invoke());
                writer.WriteNumber("origin_distribution_logit_scale", OriginDistributionLogitScale.Invoke());
                writer.WriteBoolean("surface_transit_speed", SurfaceTransitSpeed.Invoke());
                writer.WriteBoolean("walk_all_way_flag", WalkAllWayFlag.Invoke());
                writer.WriteString("xrow_ttf_range", XRowTTFRange.Invoke());
                writer.WriteStartArray("transit_classes");
                foreach (var transitClass in TransitClasses)
                {
                    transitClass.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
                writer.WriteStartArray("surface_transit_speeds");
                foreach (var surfaceSpeed in SurfaceTransitSpeeds)
                {
                    surfaceSpeed.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();
                writer.WriteStartArray("ttf_definitions");
                foreach (var ttfDefinition in TTFDefinitions)
                {
                    ttfDefinition.Invoke().WriteParameters(writer);
                }
                writer.WriteEndArray();

            }), LogbookLevel.Standard);
        }
    }
}
