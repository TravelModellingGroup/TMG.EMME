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
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using XTMF2;

namespace TMG.Emme.Export
{
    [Module(Name = "Export Binary Matrix", Description = "Export a binary matrix from EMME.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ExportBinaryMatrix : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "The scenario number of export the matrix from.",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "Matrix Number", Description = "The matrix number to export.",
            Index = 1)]
        public IFunction<int> MatrixNumber;

        [Parameter(Name = "Save To", Description = "The location to write the file.",
            Index = 2)]
        public IFunction<string> SaveTo;

        public override void Invoke(ModellerController context)
        {
            context.Run(null, "tmg2.Export.export_binary_matrix", new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteNumber("matrix_type", 4);
                        writer.WriteNumber("matrix_number", MatrixNumber.Invoke());
                        writer.WriteString("file_location", Path.GetFullPath(SaveTo.Invoke()));
                        writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
                    })),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                });
        }
    }
}
