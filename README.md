# nxopentse (by theScriptingEngineer)
## Learning NXOpen
I currently have 2 courses available for learning NXOpen. A beginner course in python to get you started by setting up your developer environment and teach some basic concepts:

[Siemens NX beginner NXOpen course (Python)](https://www.udemy.com/course/siemens-nx-beginner-nxopen-course-python/?referralCode=DEE8FAB445765802FEDC)

An in depth course walking you through a complete structural analysis, step by step, towardw a fully automated analysis from load/bc application till postprocessing:

[SimCenter 3D basic NXOpen course (C#)](https://www.udemy.com/course/simcenter3d-basic-nxopen-course/?referralCode=4ABC27CFD7D2C57D220B%20)

>Use the code **NXOPEN_PYTHON_SEP24** or **NXOPEN_CSHARP_SEP24** to get the current best price (replace *SEP* with the current 3 letter month eg. DEC if the current month is December)
>

If you’re using my scripts in your daily work, saving you a lot of work and time, buy me a coffe so I can continue developing awesome scripts.
[Buy me a coffe](https://www.buymeacoffee.com/theScriptingEngineer)

## nxopentse
This package contains functions which you can use in your own scripts, so you don't have to write everything from scratch.
```
pip install nxopentse
```

> **NOTE:** You need to have configured NX/Simcenter to work with the external python interpreter.
> 

Then in your script add 
``` 
import nxopentse
``` 

Simple example:
```
import NXOpen
import nxopentse as tse


# Every NXOpen journal needs an NXOpen.Session object
the_session: NXOpen.Session = NXOpen.Session.GetSession()


def main():
    tse.cad.nx_hello()


if __name__ == '__main__':
    main()

```



## nxopen.cad
CAD functionality


## nxopan.cae
CAE functionality


## nxopen.tools
General tools which can be used in different NX applications.


## NX versions
### SC2212:
### SC2312:


# Documentation
[nxopentse documentation](https://nxopentsedocumentation.thescriptingengineer.com/)

Documentation from source using Sphinx
```sphinx-build -M html docs/source/ docs/build/```

# Using intelligent code completion (aka intellisense) for NXOpen in python

One of the advantages of python is that it is dynamically typed. The consequence is that the IDE (eg. PyCharm, VSCode) does not know
the object type of the variable.
While writing NXOpen code in python I found this a huge disadvantage, because during coding I rely heavily on code completion (aka intellisense)
to know the available methods on the objects.
Apart from an older document from siemens explaining how to get this to work with Eclipse and PyDev add-on, which only works partially, I'm not aware of any other resource to get code completion to work.

This is why I created my own stub files for the NXOpen libraries.

>From NX2406 onwards, the stub files are provided by Siemens in the installation directory. Make sure to check the *Programming tools* during NX installation.
>

## Visual Studio Code

Demo: [Code completion in python (VSCode)](https://youtu.be/ODsZF7x7UoQ)

From [this blog](https://www.emmanuelgautier.com/blog/enable-vscode-python-type-checking)

In VSCode go to settings.json (ctrl + P -> settings.json) 
or locate settings.json under the folder .vscode an add the following entry:
*"python.analysis.typeCheckingMode": "basic"*

In VSCode go to settings.json (ctrl + P -> settings.json) 
or locate settings.json under the folder .vscode an add the following entry:

**"python.analysis.stubPath": "path_to_the_stub_files/Release2023/"**

Please contact me for a copy of the stub files.

Successful configuration should give no errors after opening **intellisense.py** (might need to restart VSCode)

## PyCharm

Demo: [Code completion in python (PyCharm)](https://youtu.be/468SGBALQQM)

Add the location of the stub files to the interpreter path. Instructions on how to do this can be found [here](https://www.jetbrains.com/help/pycharm/installing-uninstalling-and-reloading-interpreter-paths.html)

Please contact me for a copy of the stub files.