/*
    Copyright 2017-2026 University of Toronto

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
using System.IO.Compression;
using System.IO;

namespace TMG.Emme.Test.Import;

[TestClass]
public class ImportBinaryMatrixTest : TestBase
{
    [TestMethod]
    public void ImportBinaryMatrix()
    {
        Helper.ImportFrabitztownNetwork(1);
        Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));
    }

    [TestMethod]
    public void ImportBinaryMatrixCompressed()
    {
        Helper.ImportFrabitztownNetwork(1);
        var sourceFile = Path.GetFullPath("TestFiles/Test.mtx");
        var compressedFile = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N") + ".mtx.gz");
        try
        {
            using (var source = File.OpenRead(sourceFile))
            using (var destination = File.Create(compressedFile))
            using (var gzip = new GZipStream(destination, CompressionLevel.Optimal))
            {
                source.CopyTo(gzip);
            }

            Helper.ImportBinaryMatrix(1, 10, compressedFile);
        }
        finally
        {
            if (File.Exists(compressedFile))
            {
                File.Delete(compressedFile);
            }
        }
    }

    [TestMethod]
    public void ImportBinaryMatrixModule()
    {
        Helper.ImportFrabitztownNetwork(1);
        var importModule = new Emme.Import.ImportBinaryMatrix()
        {
            Name = "Importer",
            ScenarioNumber = Helper.CreateParameter(1, "Const Number"),
            MatrixNumber = Helper.CreateParameter(10, "Matrix Number"),
            FileLocation = Helper.CreateParameter(Path.GetFullPath("TestFiles/test.mtx"), "Matrix File Name"),
            Description = Helper.CreateParameter("Module Loaded", "Description"),
            MatrixType = Helper.CreateParameter(Emme.Import.ImportBinaryMatrix.MatrixTypes.MF)
        };
        importModule.Invoke(Helper.Modeller);
    }
}
