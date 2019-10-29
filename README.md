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
of the test project configuration's output directory.  That project will then need to have a 
reference to a the built 'TMG_Toolbox.mtbx' that was created from running either "Build Toolbox.bat"
or "Build Consolidated Toolbox.bat".  If you are going to be editing the toolbox's source code
it is recommended to use "Build Toolbox.bat" so you only need to rebuild it if you add or remove
a tool.

#### Unit Tests

In addition to the command below you will also need to have an active license for EMME.

```
cd TMG.EMME
dotnet test
```

## TMGToolbox2 for EMME tool Format

### Overview

Tools in the TMGToolbox2 are designed to have up to three entry points. They are:

1. run() - An entry point called when using the Modeller interface from within EMME.
2. \_\_call\_\_() - An entry point for scripting the tool into a Python script.
3. xtmf_run() - An entry point for being called from XTMF2.

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

  def __call__(self):
    print "Hello World, Python Script!"

  def xtmf_run(self, xtmf_json, xtmf_logbook_level):
    print "Hello World, XTMF2"
```