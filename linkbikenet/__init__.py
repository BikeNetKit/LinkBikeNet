import contextlib
from importlib.metadata import PackageNotFoundError, version

from . import config
from . import functions
from linkbikenet.linkbikenet import linkbikenet

__author__ = "MS, MK"
__author_email__ = "email@domain.com"

with contextlib.suppress(PackageNotFoundError):
    __version__ = version("linkbikenet")