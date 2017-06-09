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
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Reflection;
using System.Text;
using System.Threading;
using XTMF2;

namespace TMG.Emme
{
    public sealed class ModellerController : IDisposable
    {
        private Process Emme;

        private StreamReader FromEmme;

        private StreamWriter ToEmme;

        /// <summary>
        /// Tell the bridge to clean out the modeller's logbook
        /// </summary>
        private const int SignalCleanLogbook = 6;

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
        /// We will send this signal when we want to start to run a new module
        /// </summary>
        private const int SignalStartModule = 2;

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

        private const int SignalDisableLogbook = 12;

        private const int SignalEnableLogbook = 13;

        public void WriteToLogbook(IModule caller, bool enable)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    BinaryWriter writer = new BinaryWriter(ToEmme.BaseStream);
                    writer.Write(enable ? SignalEnableLogbook : SignalDisableLogbook);
                    writer.Flush();
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with EMME while sending data, with:\r\n" + e.Message);
                }
            }
        }

        private NamedPipeServerStream PipeFromEMME;

        /// <summary>
        /// </summary>
        /// <param name="projectFile"></param>
        /// <param name="performanceAnalysis"></param>
        /// <param name="userInitials"></param>
        public ModellerController(IModule caller, string projectFile, bool performanceAnalysis = false, string userInitials = "XTMF")
        {
            if (!projectFile.EndsWith(".emp") | !File.Exists(projectFile))
            {
                throw new XTMFRuntimeException(caller, AddQuotes(projectFile) + " is not an existing Emme project file (*.emp)");
            }

            FailTimer = 30;
            ProjectFile = projectFile;
            string args = "-ng ";
            string workingDirectory = ProjectFile;

            //Python invocation command:
            //[FullPath...python.exe] -u [FullPath...ModellerBridge.py] [FullPath...EmmeProject.emp] [User initials] [[Performance (optional)]] 

            // Get the path of the Python executable
            string emmePath = Environment.GetEnvironmentVariable("EMMEPATH");
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
            var pipeName = Guid.NewGuid().ToString();
            PipeFromEMME = new NamedPipeServerStream(pipeName, PipeDirection.In);
            //The first argument that gets passed into the Bridge is the name of the Emme project file
            argumentString += " " + AddQuotes(projectFile) + " " + userInitials + " " + (performanceAnalysis ? 1 : 0) + " \"" + pipeName + "\"";

            //Setup up the new process
            // When creating this process, we can not start in our own window because we are re-directing the I/O
            // and windows won't allow us to have a window and take its standard I/O streams at the same time
            Emme = new Process();
            var startInfo = new ProcessStartInfo(pythonPath, "-u " + argumentString);
            startInfo.Environment["PATH"] += ";" + pythonLib + ";" + Path.Combine(emmePath, "programs");
            Emme.StartInfo = startInfo;
            Emme.StartInfo.CreateNoWindow = true;
            Emme.StartInfo.UseShellExecute = false;
            Emme.StartInfo.RedirectStandardInput = true;
            Emme.StartInfo.RedirectStandardOutput = true;

            //Start the new process
            try
            {
                Emme.Start();
            }
            catch
            {
                throw new XTMFRuntimeException(caller, "Unable to create a bridge to EMME to '" + AddQuotes(projectFile) + "'!");
            }
            // Give some short names for the streams that we will be using
            ToEmme = Emme.StandardInput;
            // no more standard out
            PipeFromEMME.WaitForConnection();
            //this.FromEmme = this.Emme.StandardOutput;
        }

        ~ModellerController()
        {
            Dispose(true);
        }

        private bool WaitForEmmeResponce(IModule caller, ref string returnValue, Action<float> updateProgress)
        {
            // now we need to wait
            try
            {
                string toPrint;
                while (true)
                {
                    BinaryReader reader = new BinaryReader(PipeFromEMME);
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

        public bool CheckToolExists(IModule caller, string toolNamespace)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    BinaryWriter writer = new BinaryWriter(ToEmme.BaseStream);
                    writer.Write(SignalCheckToolExists);
                    writer.Write(toolNamespace);
                    writer.Flush();
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with EMME while sending data, with:\r\n" + e.Message);
                }
                // now we need to wait
                string unused = null;
                return WaitForEmmeResponce(caller, ref unused, null);
            }
        }

        public bool Run(IModule caller, string macroName, string arguments)
        {
            string unused = null;
            return Run(caller, macroName, arguments, null, ref unused);
        }

        public bool Run(IModule caller, string macroName, string arguments, ref string returnValue)
        {
            return Run(caller, macroName, arguments, null, ref returnValue);
        }

        public bool Run(IModule caller, string macroName, string arguments, Action<float> progressUpdate, ref string returnValue)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    BinaryWriter writer = new BinaryWriter(ToEmme.BaseStream);
                    writer.Write(SignalStartModule);
                    writer.Write(macroName);
                    writer.Write(arguments);
                    writer.Flush();
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with EMME while sending data, with:\r\n" + e.Message);
                }
                return WaitForEmmeResponce(caller, ref returnValue, progressUpdate);
            }
        }

        /// <summary>
        /// Throws an exception if the bridge has been disposed
        /// </summary>
        private void EnsureWriteAvailable(IModule caller)
        {
            if (ToEmme == null)
            {
                throw new XTMFRuntimeException(caller, "EMME Bridge was invoked even though it has already been disposed.");
            }
        }

        public bool Run(IModule caller, string macroName, ModellerControllerParameter[] arguments)
        {
            string unused = null;
            return Run(caller, macroName, arguments, null, ref unused);
        }

        public bool Run(IModule caller, string macroName, ModellerControllerParameter[] arguments, ref string returnValue)
        {
            return Run(caller, macroName, arguments, null, ref returnValue);
        }

        public bool Run(IModule caller, string macroName, ModellerControllerParameter[] arguments, Action<float> progressUpdate, ref string returnValue)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    BinaryWriter writer = new BinaryWriter(ToEmme.BaseStream);
                    writer.Write(SignalStartModuleBinaryParameters);
                    writer.Write(macroName);
                    if (arguments != null)
                    {
                        writer.Write(arguments.Length.ToString());
                        for (int i = 0; i < arguments.Length; i++)
                        {
                            writer.Write(arguments[i].Name);
                        }
                        for (int i = 0; i < arguments.Length; i++)
                        {
                            writer.Write(arguments[i].Value);
                        }
                    }
                    else
                    {
                        writer.Write("0");
                    }
                    writer.Flush();
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

        private void Dispose(bool finalizer)
        {
            lock (this)
            {
                if (FromEmme != null)
                {
                    FromEmme.Dispose();
                    FromEmme = null;
                }

                if (PipeFromEMME != null)
                {
                    PipeFromEMME.Dispose();
                    PipeFromEMME = null;
                }

                if (ToEmme != null)
                {
                    // Send our termination message first
                    try
                    {
                        BinaryWriter writer = new BinaryWriter(ToEmme.BaseStream);
                        writer.Write(SignalTermination);
                        writer.Flush();
                        ToEmme.Flush();
                        // after our message has been sent then we can go and kill the stream
                        ToEmme.Dispose();
                        ToEmme = null;
                    }
                    catch (IOException)
                    {
                    }
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
            number = number - (int)number;
            if (number > 0)
            {
                var integerSize = builder.Length;
                builder.Append('.');
                for (int i = integerSize; i < 4; i++)
                {
                    number = number * 10;
                    builder.Append((int)number);
                    number = number - (int)number;
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
            number = number - (int)number;
            if (number > 0)
            {
                var integerSize = builder.Length;
                builder.Append('.');
                for (int i = integerSize; i < 4; i++)
                {
                    number = number * 10;
                    builder.Append((int)number);
                    number = number - (int)number;
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
            GC.SuppressFinalize(this);
        }
    }
}