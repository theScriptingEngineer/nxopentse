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

> **NOTE:** You need to have configured NX/Simcenter to work with the external python interpreter.

## nxopen.cad
CAD functionality


## nxopan.cae
CAE functionality


## nxopen.tools
General tools which can be used in different NX applications.


## NX versions
### SC2212:


# Documentation
Documentation from source using Sphinx
```sphinx-build -M html docs/source/ docs/build/```

# Development
There is a build pipeline in Github which automatically publishes to test.pypi and pypi (the latter only on tagged commits)
So there is no need to manually build an upload to either test.pypi or pypi

## Tagging
``` git tag -a v0.0.1a1 -m "pre-release - can be used. Partially tested. Will still contain lots of bugs" ```
> **NOTE:** Tags don't get pushed automatically. Use ```git push origin --tags```
> 
> 
> or configure "git.followTagsWhenSync": true
> preferences -> extensions -> git -> check Follow tags when sync

workflow (VSCode):
  - increase the version number so that it doesn't clash with test.pypi or pypi
  - local commit
  - tag the commit, with the same version number as above
  - push/sync wioth github


## Build the package manually (for reference only)
install locally by navigating to folder and then
```pip install .```

uninstall:
```pip uninstall nxopentse```

update: uninstall and reinstall

required installations:
```
python -m pip install --upgrade twine
pip install build
```

Building the package:
```
python -m build
```

manually publish to test.pypi:
```
py -m twine upload --repository testpypi dist/*
```

manually publish to pypi:
This has to be done manual on the first time, as 'non user identities cannot create new projects'
```
py -m twine upload dist/*
```

tag 
