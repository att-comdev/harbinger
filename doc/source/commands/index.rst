=================================================================
Commands
=================================================================

harbinger help
    print detailed help for another command

..

harbinger run <location of standardized input yaml>
    extracts all the appropriate frameworks and environment
    data from the yaml file and proceeds to run the relevant
    frameworks

..

harbinger list frameworks
    Lists all the frameworks that have been provided
    through the provided yaml file

..

harbinger list tests <framework name>
    Lists all the available tests in the framework provided
    through an argument --framework-name

..

harbinger scaffold <new framework name>
    Creates boiler plate framework file and
    harbinger.cfg option for the framework

..

harbinger teardown <existing framework name>
    Removes and deletes all framework related files
    and references, including harbinger.cfg section
