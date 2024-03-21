# the below should be removed, in combination with setuptools in the pyproject.toml
# such that only the imports from the subpackages are available.
# this should make nxopentse much more clean
from .cad import code
from .cae import postprocessing, preprocessing
from .tools import excel, general