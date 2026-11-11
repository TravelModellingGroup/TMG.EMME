using System;
using System.IO;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace TMG.Emme.Test;

[TestClass]
public class ModellerPipeProtocolTest
{
    [TestMethod]
    [Timeout(30_000)]
    public void ReadPipeString_ReadsUtf8LengthPrefixedMessages()
    {
        var messages = new[]
        {
            "RuntimeError: scenario operation failed",
            "Traceback: café, 東京, and 😀",
            new string('x', 8192)
        };

        using var stream = new MemoryStream();
        foreach (var message in messages)
        {
            var frame = EncodePythonString(message);
            stream.Write(frame, 0, frame.Length);
        }

        stream.Position = 0;
        using var reader = ModellerController.CreatePipeReader(stream);
        foreach (var message in messages)
        {
            Assert.AreEqual(message, reader.ReadString());
        }
        Assert.AreEqual(stream.Length, stream.Position);
    }

    private static byte[] EncodePythonString(string value)
    {
        var payload = Encoding.UTF8.GetBytes(value);
        using var stream = new MemoryStream();
        var length = payload.Length;
        while (length >= 128)
        {
            stream.WriteByte((byte)((length & 127) | 128));
            length >>= 7;
        }
        stream.WriteByte((byte)length);
        stream.Write(payload, 0, payload.Length);
        return stream.ToArray();
    }
}
