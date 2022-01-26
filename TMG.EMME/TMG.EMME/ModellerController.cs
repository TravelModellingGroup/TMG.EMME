/*
    Copyright 2017-2022 University of Toronto

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
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using XTMF2;

namespace TMG.Emme
{
    public sealed class ModellerController : IDisposable
    {
        private static readonly char[] LogbookStandard = new[] { 'A', 'L', 'L' };
        private static readonly char[] LogbookDebug = new[] { 'D', 'E', 'B', 'U', 'G' };
        private static readonly char[] LogbookNone = new[] { 'N', 'O', 'N', 'E' };

        private Process _emme;
        private NamedPipeServerStream _emmePipe;

        #region SignalCodes

        /// <summary>
        /// We receive this error if the bridge can not get the parameters to match
        /// the selected tool
        /// </summary>
        private const int SignalParameterError = 4;

        /// <summary>
        /// Receive a signal that contains a progress report
        /// </summary>
        private const int SignalProgressReport = 7;

        /// <summary>
        /// We receive this when the Bridge has completed its module run
        /// </summary>
        private const int SignalRunComplete = 3;

        /// <summary>
        /// We receive this when the Bridge has completed its module run and that there is a return value as well
        /// </summary>
        private const int SignalRunCompleteWithParameter = 8;

        /// <summary>
        /// We revive this error if the tool that we tell the bridge to run throws a
        /// runtime exception that is not handled within the tool
        /// </summary>
        private const int SignalRuntimeError = 5;

        /// <summary>
        /// We will receive this from the ModellerBridge
        /// when it is ready to start processing
        /// </summary>
        private const int SignalStart = 0;

        /// <summary>
        /// We will send this signal when we want to start to run a new module with binary parameters
        /// </summary>
        private const int SignalStartModuleBinaryParameters = 14;

        /// <summary>
        /// This is the message that we will send when it is time to shutdown the bridge.
        /// If we receive it, then we know that the bridge is in a panic and has exited
        /// </summary>
        private const int SignalTermination = 1;

        /// <summary>
        /// Signal the bridge to check if a tool namespace exists
        /// </summary>
        private const int SignalCheckToolExists = 9;

        /// <summary>
        /// Signal from the bridge throwing an exception that the tool namespace could not be found
        /// </summary>
        private const int SignalToolDoesNotExistError = 10;

        /// <summary>
        /// Signal from the bridge that a print statement has been called, to write to the XTMF Console
        /// </summary>
        private const int SignalSentPrintMessage = 11;

        /// <summary>
        /// A signal from the modeller bridge saying that the tool that was requested to execute does not
        /// contain an entry point for a call from XTMF2.
        /// </summary>
        private const int SignalIncompatibleTool = 15;

        #endregion

        public ModellerController(IModule caller, string projectFile, string pipeName,
            bool performanceAnalysis = false, string userInitials = "XTMF", bool launchInNewProcess = true, 
            string databank = null, string emmePath = null)
        {
            if (!projectFile.EndsWith(".emp") | !File.Exists(projectFile))
            {
                throw new XTMFRuntimeException(caller, AddQuotes(projectFile) + " is not an existing Emme project file (*.emp)");
            }

            FailTimer = 30;
            ProjectFile = projectFile;
            string workingDirectory = ProjectFile;

            //Python invocation command:
            //[FullPath...python.exe] -u [FullPath...ModellerBridge.py] [FullPath...EmmeProject.emp] [User initials] [[Performance (optional)]] 

            // Get the path of the Python executable
            emmePath = emmePath ?? Environment.GetEnvironmentVariable("EMMEPATH");
            if (String.IsNullOrWhiteSpace(emmePath))
            {
                throw new XTMFRuntimeException(caller, "Please make sure that EMMEPATH is on the system environment variables!");
            }
            string pythonDirectory = Path.Combine(emmePath, FindPython(caller, emmePath));
            string pythonPath = AddQuotes(Path.Combine(pythonDirectory, @"python.exe"));
            string pythonLib = Path.Combine(pythonDirectory, "Lib");

            // Get the path of ModellerBridge
            // Learn where the modules are stored so we can find the python script
            // The Entry assembly will be the XTMF.GUI or XTMF.RemoteClient
            var codeBase = typeof(ModellerController).GetTypeInfo().Assembly.Location;
            // When EMME is installed it will link the .py to their python interpreter properly
            string argumentString = AddQuotes(Path.Combine(Path.GetDirectoryName(codeBase), "ModellerBridge.py"));
            _emmePipe = new NamedPipeServerStream(pipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
            try
            {
                Parallel.Invoke(() =>
               {
                   // no more standard out
                   _emmePipe.WaitForConnection();
                   using var reader = new BinaryReader(_emmePipe, Encoding.UTF8, true);
                   // wait for the start
                   reader.ReadInt32();
               }, () =>
               {
                   //The first argument that gets passed into the Bridge is the name of the Emme project file
                   argumentString += " " + AddQuotes(projectFile) + " " + userInitials + " " + (performanceAnalysis ? 1 : 0) + " \"" + pipeName + "\"";
                   if (!String.IsNullOrWhiteSpace(databank))
                   {
                       argumentString += " " + AddQuotes(databank);
                   }
                   if (launchInNewProcess)
                   {
                       //Setup up the new process
                       // When creating this process, we can not start in our own window because we are re-directing the I/O
                       // and windows won't allow us to have a window and take its standard I/O streams at the same time
                       _emme = new Process();
                       var startInfo = new ProcessStartInfo(pythonPath, argumentString);
                       startInfo.Environment["PATH"] += ";" + pythonLib + ";" + Path.Combine(emmePath, "programs");
                       _emme.StartInfo = startInfo;
                       _emme.StartInfo.CreateNoWindow = false;
                       _emme.StartInfo.UseShellExecute = false;
                       _emme.StartInfo.RedirectStandardInput = false;
                       _emme.StartInfo.RedirectStandardOutput = false;

                       //Start the new process
                       try
                       {
                           _emme.Start();
                       }
                       catch
                       {
                           throw new XTMFRuntimeException(caller, "Unable to create a bridge to EMME to '" + AddQuotes(projectFile) + "'!");
                       }
                   }
               });
            }
            catch (AggregateException e)
            {
                throw e.InnerException;
            }
        }
        /// <summary>
        /// </summary>
        /// <param name="projectFile"></param>
        /// <param name="performanceAnalysis"></param>
        /// <param name="userInitials"></param>
        public ModellerController(IModule caller, string projectFile, bool performanceAnalysis = false, string userInitials = "XTMF", string emmePath = null)
            : this(caller, projectFile, Guid.NewGuid().ToString(), performanceAnalysis, userInitials, emmePath:emmePath)
        {

        }

        ~ModellerController()
        {
            Dispose(false);
        }

        private bool WaitForEmmeResponce(IModule caller, ref string returnValue, Action<float> updateProgress)
        {
            // now we need to wait
            try
            {
                string toPrint;
                while (true)
                {
                    using var reader = new BinaryReader(_emmePipe, Encoding.Unicode, true);
                    int result = reader.ReadInt32();
                    switch (result)
                    {
                        case SignalStart:
                            {
                                continue;
                            }
                        case SignalRunComplete:
                            {
                                return true;
                            }
                        case SignalRunCompleteWithParameter:
                            {
                                returnValue = reader.ReadString();
                                return true;
                            }
                        case SignalTermination:
                            {
                                throw new XTMFRuntimeException(caller, "The EMME ModellerBridge panicked and unexpectedly shutdown.");
                            }
                        case SignalParameterError:
                            {
                                throw new EmmeToolParameterException(caller, "EMME Parameter Error: " + reader.ReadString());
                            }
                        case SignalRuntimeError:
                            {
                                throw new EmmeToolRuntimeException(caller, "EMME Runtime " + reader.ReadString());
                            }
                        case SignalToolDoesNotExistError:
                            {
                                throw new EmmeToolCouldNotBeFoundException(caller, reader.ReadString());
                            }
                        case SignalIncompatibleTool:
                            {
                                throw new EmmeToolIncompatibleError(caller, reader.ReadString());
                            }
                        case SignalCheckToolExists:
                            {
                                return true;
                            }
                        case SignalSentPrintMessage:
                            {
                                toPrint = reader.ReadString();
                                Console.Write(toPrint);
                                break;
                            }
                        case SignalProgressReport:
                            {
                                var progress = reader.ReadSingle();
                                updateProgress?.Invoke(progress);
                                break;
                            }
                        default:
                            {
                                throw new XTMFRuntimeException(caller, "Unknown message passed back from the EMME ModellerBridge.  Signal number " + result);
                            }
                    }
                }
            }
            catch (EndOfStreamException)
            {
                throw new XTMFRuntimeException(caller, "We were unable to communicate with EMME.  Please make sure you have an active EMME license.  If the problem persists, sometimes rebooting has helped fix this issue with EMME.");
            }
            catch (IOException e)
            {
                throw new XTMFRuntimeException(caller, "I/O Connection with EMME ended while waiting for data, with:\r\n" + e.Message);
            }
        }

        /// <summary>
        /// Throws an exception if the bridge has been disposed
        /// </summary>
        private void EnsureWriteAvailable(IModule caller)
        {
            if (_emmePipe == null)
            {
                throw new XTMFRuntimeException(caller, "EMME Bridge was invoked even though it has already been disposed.");
            }
        }

        public bool Run(IModule caller, string macroName, string jsonParameters, LogbookLevel level)
        {
            string unused = null;
            return Run(caller, macroName, jsonParameters, level, null, ref unused);
        }

        public bool Run(IModule caller, string macroName, string jsonParameters, LogbookLevel level, ref string returnValue)
        {
            return Run(caller, macroName, jsonParameters, level, null, ref returnValue);
        }

        public bool Run(IModule caller, string macroName, string jsonParameters, LogbookLevel level, Action<float> progressUpdate, ref string returnValue)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    using var writer = new BinaryWriter(_emmePipe, Encoding.Unicode, true);
                    writer.Write(SignalStartModuleBinaryParameters);
                    writer.Write(macroName.Length);
                    writer.Write(macroName.ToCharArray());
                    if (jsonParameters == null)
                    {
                        writer.Write((int)0);
                    }
                    else
                    {
                        writer.Write(jsonParameters.Length);
                        writer.Write(jsonParameters.ToCharArray());
                    }
                    var logbookLevel = level switch
                    {
                        LogbookLevel.Standard => LogbookStandard,
                        LogbookLevel.Debug => LogbookDebug,
                        LogbookLevel.None => LogbookNone,
                        _ => LogbookStandard
                    };
                    writer.Write(logbookLevel.Length);
                    writer.Write(logbookLevel);
                    writer.Flush();
                    // make sure the tool exists before continuing
                    if (!WaitForEmmeResponce(caller, ref returnValue, progressUpdate))
                    {
                        // if the tool does not exist, we have failed!
                        return false;
                    }
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with EMME while sending data, with:\r\n" + e.Message);
                }
                return WaitForEmmeResponce(caller, ref returnValue, progressUpdate);
            }
        }

        private string AddQuotes(string fileName)
        {
            return String.Concat("\"", fileName, "\"");
        }

        private void Dispose(bool managed)
        {
            lock (this)
            {
                if (_emmePipe != null)
                {
                    // Send our termination message first
                    try
                    {
                        using var writer = new BinaryWriter(_emmePipe, Encoding.UTF8, true);
                        writer.Write(SignalTermination);
                        writer.Flush();
                        _emmePipe.Flush();
                        // after our message has been sent then we can go and kill the stream
                        _emmePipe.Dispose();
                        _emmePipe = null;
                    }
                    catch (IOException)
                    {
                    }
                }
                if (managed)
                {
                    GC.SuppressFinalize(this);
                }
            }
        }

        private string FindPython(IModule caller, string emmePath)
        {
            if (!Directory.Exists(emmePath))
            {
                throw new XTMFRuntimeException(caller, "We were unable to find an EMME installation in the directory named '" + emmePath + "'!\r\nIf you have just installed EMME please reboot your system.");
            }
            foreach (var dir in Directory.GetDirectories(emmePath))
            {
                var localName = Path.GetFileName(dir);
                if (localName != null && localName.StartsWith("Python"))
                {
                    var remainder = localName.Substring("Python".Length);
                    if (remainder.Length > 0 && char.IsDigit(remainder[0]))
                    {
                        return localName;
                    }
                }
            }
            throw new XTMFRuntimeException(caller, "We were unable to find a version of python inside of EMME!");
        }

        /// <summary>
        /// Process floats to work with emme
        /// </summary>
        /// <param name="number">The float you want to send</param>
        /// <returns>A limited precision non scientific number in a string</returns>
        public static string ToEmmeFloat(float number)
        {
            var builder = new StringBuilder();
            builder.Append((int)number);
            number = (float)Math.Round(number, 6);
            number -= (int)number;
            if (number > 0)
            {
                var integerSize = builder.Length;
                builder.Append('.');
                for (int i = integerSize; i < 4; i++)
                {
                    number *= 10;
                    builder.Append((int)number);
                    number -= (int)number;
                    // ReSharper disable once CompareOfFloatsByEqualityOperator
                    if (number == 0)
                    {
                        break;
                    }
                }
            }
            return builder.ToString();
        }

        /// <summary>
        /// Process floats to work with emme
        /// </summary>
        /// <param name="number">The float you want to send</param>
        /// <param name="builder">A string build to use to make the string</param>
        /// <returns>A limited precision non scientific number in a string</returns>
        public static void ToEmmeFloat(float number, StringBuilder builder)
        {
            builder.Clear();
            builder.Append((int)number);
            number -= (int)number;
            if (number > 0)
            {
                var integerSize = builder.Length;
                builder.Append('.');
                for (int i = integerSize; i < 4; i++)
                {
                    number *= 10;
                    builder.Append((int)number);
                    number -= (int)number;
                    // ReSharper disable once CompareOfFloatsByEqualityOperator
                    if (number == 0)
                    {
                        break;
                    }
                }
            }
        }

        public double FailTimer { get; set; }

        /// <summary>
        ///
        /// </summary>
        public string ProjectFile { get; private set; }

        public void Close()
        {
            Dispose();
        }

        public void Dispose()
        {
            Dispose(true);
        }
    }
}