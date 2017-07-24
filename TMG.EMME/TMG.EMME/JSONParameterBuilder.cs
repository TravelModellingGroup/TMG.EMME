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
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using TMG.Emme;
using XTMF2;

namespace TMG.Emme
{
    public static class JSONParameterBuilder
    {
        public static string BuildParameters(Action<JsonWriter> toExecute)
        {
            string ret = null;
            using (MemoryStream backing = new MemoryStream())
            {
                using (StreamWriter sWriter = new StreamWriter(backing, Encoding.Unicode, 0x4000, true))
                using (JsonWriter writer = new JsonTextWriter(sWriter))
                {
                    writer.WriteStartObject();
                    toExecute(writer);
                    writer.WriteEndObject();
                    writer.Flush();
                    sWriter.Flush();
                }
                backing.Position = 0;
                using (StreamReader reader = new StreamReader(backing))
                {
                    ret = reader.ReadToEnd();
                }
            }
            return ret;
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, string value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if(parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, float value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, double value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, int value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, long value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, ulong value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, uint value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, char value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, short value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, ushort value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, byte value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }

        /// <summary>
        /// Write a parameter to the Json stream.
        /// </summary>
        /// <param name="writer">The writer to store to</param>
        /// <param name="parameterName">The name of the parameter</param>
        /// <param name="value">The value to assign to the parameter</param>
        public static void WriteParameter(this JsonWriter writer, string parameterName, bool value)
        {
            if (writer == null)
            {
                throw new ArgumentNullException(nameof(writer));
            }
            if (parameterName == null)
            {
                throw new ArgumentNullException(nameof(parameterName));
            }
            writer.WritePropertyName(parameterName);
            writer.WriteValue(value);
        }
    }
}
