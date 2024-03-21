# nxopentse (by theScriptingEngineer)
This package contains functions which you can use in your own scripts, so you don't have to write everything from scratch.
``` pip install nxopentse```

Then in your script add 
``` import nxopentse``` 

Simple example:
```
import NXOpen
import nxopentse as tse


# next line not required for nxopen, but every NXOpen journal needs an NXOpen.Session object
the_session: NXOpen.Session = NXOpen.Session.GetSession()


def main():
    tse.tools.hello()


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
  - the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession() -> AttributeError: module 'NXOpen' has no attribute 'UF'


## dev
install locally by navigating to folder and then
```pip install .```

uninstall:
```pip uninstall nxopentse```

update: uninstall and reinstall