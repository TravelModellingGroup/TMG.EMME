# TMG.EMME

This repository contains two tightly integrated software packages.
The first is TMGToolbox2 for EMME, a toolbox for working with [Inro's EMME](https://www.inrosoftware.com/en/products/emme/) software.
The second is TMG.EMME a set of modules for [XTMF2](https://github.com/TravelModellingGroup/XTMF2) to
call the TMGToolbox2 in order to iterate them into larger model systems.

In addition to [XTMF2](https://github.com/TravelModellingGroup/XTMF2) this repository
depends on the [TMG-Framework](https://github.com/TravelModellingGroup/TMG-Framework) repository
for integrating into larger model systems.

## Building TMG.EMME

### Requirements

1. DotNet Core 3.0 SDK
2. EMME version 4.4.2 or above.

### Clone the TMG.EMME repository

> git clone https://github.com/TravelModellingGroup/TMG.EMME

### Update Submodules

> git submodule update --recursive --remote

### Building

There are two steps for compiling.  First we can compile TMG.EMME's modules for XTMF2.
The second step is to create a toolbox for EMME.  There are two batch files for automating
that call inside of the TMGToolbox2.  "Build Toolbox.bat" will create a toolbox that references
the files within the TMGToolbox2 project. This toolbox is not portable to other machines.  In order
to compile a portable toolbox use "Build Consolidated Toolbox.bat".  If you build a consolidated
toolbox you will need to rebuild it every time you alter the TMGToolbox2 source code.

```
cd TMG.EMME
dotnet build --configuration Release
cd TMGToolbox2
"Build Toolbox.bat"
```

### Testing

#### Initial Setup

TMG.EMME's unit tests are currently setup to expect a EMME project named __DebugProject__ inside
of the test project configuration's output directory. 

The path to the location of the DebugProject folder is the following:
```
~\TMG.EMME\TMG.EMME\TMG.EMME.Test\bin\Debug\net10.0\DebugProject
```
**Note:** The reason the Debug project is in the Debug folder is because it wasn't compiled to a Release build. 

Use Emme software to create a new Emme project with the database dimensions below. Do not the name of the project 
must be named **DebugProject**. Note for the city use Toronto (GTA) for the map of interest (initially). 

That project will then need to have a reference to a the built 'TMG_Toolbox.mtbx' that was created from running either "Build Toolbox.bat"
or "Build Consolidated Toolbox.bat". If you are going to be editing the toolbox's source code
it is recommended to use "Build Toolbox.bat" so you only need to rebuild it if you add or remove
a tool.

The recommended database dimensions for the __DebugProject__ is shown below:

| Component    | Dimension  |
|----------|-------|
| Scenarios | 5 |
| Full matrices | 10 |
| Centroids | 3750 |
| Regular nodes | 43124 |
| Links | 187500 |
| Transit vehicles | 30 |
| Transit lines | 15000 |
| Transit segments | 600000 |
| Extra attribute values | 5000000 |

Upon succesfully creating the Emme project. click the modeller icon in Emme (the blue cube icon) and then upload the TMGToolbox2.
Use the TMGToolbox2 tool import network and upload the Frabitztown network located in this repo called test.nwp. 

Ensure the Emme system path is correct under your system environment varaibles and set the EMME system path to the following: 
```
C:\Program Files\Bentley\OpenPaths\EMME 25.00.00
```
You do need to sign-out or restart the machine for the path effect change to take effect. 


#### Unit Tests

In addition to the command below you will also need to have an active license for EMME.

```
cd TMG.EMME
dotnet test
```

In some instances you may wish to run the unittests in debug mode for debugging purpose. To run the project in debug mode
the following steps are needed: 
1. Open the same project TMG.Emme again so you have two instances of the visual studio project. 
1. On the left side open the test explorer and run a test in debug mode like ImportBinaryMatrix. 
1. if successful the system will hang 
1. On the right side, right click the TMGToolBox2 and select **set it as startup project**
1. Then click F5 to run the Python instance and both sides should now work. 

Note: In the instance the system crashes (which can happen sometimes), you can delete the emme.lock file located in the 
Emme Database folder:
```
~\TMG.EMME\TMG.EMME\TMG.EMME.Test\bin\Debug\net10.0\DebugProject\Database
```

### Updating DotNet version (If Applicable and Required) 
Check to make sure the TMG.EMME and TMG.EMME.Tests projects are working on the most current version of dotnet.
To modify the project dotnet version in Visual Studio right click on project and click **Edit Project Settings**.
From there under TargetFramework change the value the recent version of dotnet. 
As of the time of writing this tutorial the current version net10. 
```  
<PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
```

### Setting up Python Environment 
It may be necessary to setup a Python virtual environment for this project. These are the steps to setup a Python virtual 
environment in Visual Studio.
- Right click on **python environment** (under TMGToolbox2) and select **add environment**
- Select *existing environment* tab/section
- Under the section seelect **custom path, path to existing environment**
- Then find and search for the Bentley Python path. The path is the following: 
- ```C:\Program Files\Bentley\OpenPaths\EMME 25.00.00\Python311```
- click Add and your new python environment using the Bentley version of Python will be setup and ready to use.



## TMGToolbox2 for EMME tool Format

### Overview

Tools in the TMGToolbox2 are designed to have up to three entry points. They are:

1. run() - An entry point called when using the Modeller interface from within EMME.
2. \_\_call\_\_() - An entry point for scripting the tool into a Python script.
3. run_xtmf() - An entry point for being called from XTMF2.

### Example

In the following example we are going to see a tool that implements all three
entry points.  If a tool does not make sense to be included with a Python script, or XTMF2
please do not implement those functions.

```python
import inro.modeller as _m
_tmg_tpb = _MODELLER.module('tmg2.utilities.TMG_tool_page_builder')
class HelloWorld(m.tool()):

  version = '1.0.0'

  def __init__(self):
    pass

  def page(self):
    pb = _tmg_tpb.TmgToolPageBuilder(self, 
             title="Hello World v%s" % self.version,
             description="Prints out a Hello world for each entry point.",
             branding_text="- TMG Toolbox")
    return pb.render()

  # The entry point for Modeller
  def run(self):
    print "Hello World, Modeller!"

  # The entry point for a Python script
  def __call__(self):
    print "Hello World, Python Script!"

  # The entry point for a call from XTMF2
  def run_xtmf(self, parameters):
    # parameters is a parsed JSON object
    print "Hello World, XTMF2"
```