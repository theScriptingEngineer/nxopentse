# nxopentse (by theScriptingEngineer)
> **LEARN NXOPEN**
>
>[Siemens NX beginner NXOpen course (Python)](https://www.udemy.com/course/siemens-nx-beginner-nxopen-course-python/?referralCode=DEE8FAB445765802FEDC)
>
>[SimCenter 3D basic NXOpen course (C#)](https://www.udemy.com/course/simcenter3d-basic-nxopen-course/?referralCode=4ABC27CFD7D2C57D220B%20)

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


# Documentation
[nxopentse documentation](https://nxopentsedocumentation.thescriptingengineer.com/)

Documentation from source using Sphinx
```sphinx-build -M html docs/source/ docs/build/```
