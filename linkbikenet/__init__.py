"""
LinkBikeNet is a Python package to find links between the disconnected 
components in a city’s bicycle network.

Full documentation at: https://docs.bikenetkit.org/LinkBikeNet/

If you use LinkBikeNet, please cite: https://doi.org/10.1098/rsos.201130
"""

import contextlib
from importlib.metadata import PackageNotFoundError, version

from linkbikenet.linkbikenet import linkbikenet
from . import constants
from . import linkbikenet
from . import osm
from . import settings
from . import functions

__author__ = "LinkBikeNet contributors"
__author_email__ = "michael@szell.net"

with contextlib.suppress(PackageNotFoundError):
    __version__ = version("linkbikenet")