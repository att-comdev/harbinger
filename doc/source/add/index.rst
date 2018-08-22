=================================================================
How to support new Frameworks
=================================================================

Supporting a new framework in Harbinger is easily achieved by following three steps

Scaffold
^^^^^^^^
First you must run the scaffold command *{ hints assume container directory structure }*

**harbinger scaffold <new framework name>**

Once this command is run it will

* add a framework section to harbinger.cfg *{ /opt/harbinger-src/harbinger/etc/harbinger.cfg }*
* create framework directory *{ /opt/harbinger/frameworks/<framework> }*
* create virtual environment directory *{ /opt/harbinger/venvs/<framework> }*
* create framework executor file *{ /opt/harbinger-src/harbinger/executors/<framework>.py }*

This will setup all of your directories, options, and boiler plate code

Docker install
^^^^^^^^^^^^^^
Add an install directive to the docker file. Each framework may differe in how they are installed. For reference look
for existing supported frameworks.

Harbinger.cfg
^^^^^^^^^^^^^
You must populate the newly added harbinger.cfg section with options that the particular framework needs. for reference
you should look for existing supported frameworks.

Executor file
^^^^^^^^^^^^^
You must write additional code in the newly created executor file. This file handles all the functionality of producing
a file that is readable by the framework, and passing that into the framework. For reference look for existing supported
framework e.g. shaker.py or yardstick.py
