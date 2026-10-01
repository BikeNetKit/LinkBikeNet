Getting started
===============

Get Started in 4 Steps
----------------------

1. Install LinkBikeNet by following the :doc:`installation` guide.

2. Read the :ref:`introducing-linkbikenet` section below.

3. To check that the installation worked, run ``python examples/mwe.py`` or the Jupyter :doc:`mwe`.

4. Consult the :doc:`reference_user` for complete details on using the package.

Finally, if you're not already familiar with `NetworkX`_ and `GeoPandas`_, make sure you read their user guides as LinkBikeNet uses their data structures.

.. _introducing-linkbikenet:

Introducing LinkBikeNet
-----------------------

LinkBikeNet is built on top of `OSMnx`_/`NetworkX`_ and `GeoPandas`_. It takes one mandatory parameter, the city name, which it passes via `Nominatim`_ to `OSMnx`_, to download a city's street network. LinkBikeNet then runs the following operations:

* TBA


To try it out, run the:

.. toctree::
   :maxdepth: 1

   Minimum working example <mwe>


.. _GeoPandas: https://geopandas.org
.. _NetworkX: https://networkx.org
.. _OSMnx: https://osmnx.readthedocs.io
.. _Nominatim: https://nominatim.openstreetmap.org