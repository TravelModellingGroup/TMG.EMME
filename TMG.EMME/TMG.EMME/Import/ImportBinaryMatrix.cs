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

namespace TMG.Emme.Import
{
    [Module(Name = "Import Binary Package", Description = "Import a binary matrix into EMME.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public class ImportBinaryMatrix : BaseAction<ModellerController>
    {
        [Parameter(Name = "Scenario Number", Description = "The number of the scenario that this matrix is for.",
            Index = 0)]
        public IFunction<int> ScenarioNumber;

        [Parameter(Name = "File Location", Description = "The location of the matrix file to import.",
            Index = 1)]
        public IFunction<string> FileLocation;

        [Parameter(Name = "Matrix Number", Description = "The matrix number to import this matrix to.",
            Index = 2)]
        public IFunction<int> MatrixNumber;

        [Parameter(Name = "Description", Description = "The description to apply to the matrix"
            ,Index = 3)]
        public IFunction<string> Description;

        public override void Invoke(ModellerController context)
        {
            context.Run(this, "tmg2.Import.import_binary_matrix",
                new[]
                {
                    new ModellerControllerParameter("xtmf_JSON", JSONParameterBuilder.BuildParameters(writer =>
                    {
                        writer.WriteParameter("matrix_type", 4);
                        writer.WriteParameter("matrix_number", MatrixNumber.Invoke());
                        writer.WriteParameter("binary_matrix_file", Path.GetFullPath(FileLocation.Invoke()));
                        writer.WriteParameter("scenario_number", ScenarioNumber.Invoke());
                        writer.WriteParameter("matrix_description", Description.Invoke());
                    })),
                    new ModellerControllerParameter("xtmf_logbook_level", ModellerController.LogbookAll)
                });
        }
    }
}
