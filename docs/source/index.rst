.. LinkBikeNet documentation master file, created by
   sphinx-quickstart on Thu Feb 12 15:01:19 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

LinkBikeNet |version| documentation
===================================

The Python package ``linkbikenet`` finds links between the disconnected components in a city's bicycle network. You can download street and bike network data with a single line of code, simulate different bicycle network linking scenarios, and export and plot the resulting prioritized linking steps. It is hosted on `Github <https://github.com/BikeNetKit/LinkBikeNet>`__, part of `BikeNetKit <https://bikenetkit.org>`__.

LinkBikeNet is a decision support tool for urban planners. It is also useful for proactive citizens to help inform their city about data-driven improvements, and it aims to foster research on bicycle networks.

When to use
-----------

LinkBikeNet works well for cities that have some bicycle infrastructure in the form of disconnected components. This is the case for most cities in Europe. Recommended example cities to link components: Budapest, Dublin, Tirana

For alternative approaches, consider using `FixBikeNet <https://github.com/BikeNetKit/FixBikeNet>`__ or extending the existing network with `GrowBikeNet <https://github.com/BikeNetKit/GrowBikeNet>`__.

Setup and use
-------------

To set up LinkBikeNet, see the :doc:`installation` page.
To use LinkBikeNet, the :doc:`getting_started` page
is a good place to start, which also explains how the package works in detail. For technical documentation, consult the :doc:`reference_user`.

Origin
------

The source code builds on `the code from the
research paper <https://github.com/nateraluis/bicycle-network-growth>`__ *Data-driven strategies for optimal bicycle network growth*.

How to cite
-----------

If you use LinkBikeNet in your research, please cite `the paper <https://doi.org/10.1098/rsos.201130>`__:

   L.G. Natera Orozco, F. Battiston, G. Iñiguez, M. Szell. Data-driven strategies for optimal bicycle network growth. Royal Society Open Science 7:201130 (2020)

Contributing
------------

If you want to contribute to the development of LinkBikeNet, please read the
`CONTRIBUTING.md <https://github.com/BikeNetKit/LinkBikeNet?tab=contributing-ov-file#contributing-to-bikenetkit>`__
file.

Supported by
------------

Development of BikeNetKit/LinkBikeNet was supported by the Innovation Fund Denmark
and the EU HORIZON grant JUST STREETS.

|Innovation Fund Denmark|    |European Union|   |JUST STREETS|

Developed by
|NERDS|

.. |Innovation Fund Denmark| image:: _static/logo_innovationfund.png
   :target: https://innovationsfonden.dk/en
.. |European Union| image:: _static/logo_eu.png
   :target: https://commission.europa.eu/index_en
.. |JUST STREETS| image:: _static/logo_juststreets.png
   :target: https://www.just-streets.eu/
.. |NERDS| image:: _static/logo_nerds.png
   :width: 240px
   :target: https://nerds.itu.dk/


Documentation contents
----------------------

.. toctree::
   :maxdepth: 1

   Home <self>
   installation
   getting_started
   reference_user
   reference_developer
   changelog
