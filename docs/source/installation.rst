=============
Installation
=============

The easy way
~~~~~~~~~~~~

The recommended way to install LinkBikeNet is using `conda <https://docs.conda.io/projects/conda/en/latest/index.html>`__ (or the faster `mamba <https://mamba.readthedocs.io/en/latest/index.html>`__) via the `conda-forge` channel:

::

   conda install linkbikenet -c conda-forge

For more installation options, see below.

With pip
~~~~~~~~

LinkBikeNet can also be installed with pip, if all dependencies can be installed as well:

::

   pip install linkbikenet

.. warning::

    We do not recommend using pip, because you need to make sure that all dependencies of linkbikenet are installed correctly. Using conda, see `above <#the-easy-way>`__, avoids the need to compile the dependencies yourself.


Environment installations
~~~~~~~~~~~~~~~~~~~~~~~~~

Creating a new environment is not strictly necessary, but given that installing other geospatial packages from different channels may cause dependency conflicts, it can be good practice to install in a clean environment starting fresh.

The main step is to set up a virtual environment ``lbnenv`` in which to
install the package, and then to use or run the environment. Use either of the methods below.

With conda
^^^^^^^^^^

Installation with `conda <https://docs.conda.io/projects/conda/en/latest/index.html>`__ (or the faster `mamba <https://mamba.readthedocs.io/en/latest/index.html>`__). The following commands create the ``lbnenv`` environment, configures it to install packages always from conda-forge, and installs LinkBikeNet in it:

::

   conda create -n lbnenv
   conda activate lbnenv
   conda config --env --add channels conda-forge
   conda config --env --set channel_priority strict
   conda install python=3 linkbikenet

With Pixi
^^^^^^^^^

The fastest and cleanest way to install LinkBikeNet is via `Pixi <https://pixi.prefix.dev/latest/#installation>`__:

::

   pixi init
   pixi add linkbikenet

Then use the Pixi environment as so:

::

   pixi shell

.. note::

    The first time you run code with Pixi, it might take a minute longer, as Pixi resolves the environment’s dependencies only at this point.


Run linkbikenet in Jupyter lab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After having set up the environment `above <#environment-installations>`__, if you wish to run
linkbikenet via `JupyterLab <https://pypi.org/project/jupyterlab/>`__,
follow the corresponding instructions below.

With conda
^^^^^^^^^^

Using `conda <https://docs.conda.io/projects/conda/en/latest/index.html>`__ (or the faster `mamba <https://mamba.readthedocs.io/en/latest/index.html>`__), run:

::

   conda activate lbnenv
   ipython kernel install --user --name=lbnenv
   conda deactivate
   jupyter lab

Once Jupyter lab opens, switch the kernel (Kernel > Change Kernel >
lbnenv)

With Pixi
^^^^^^^^^

Once you are in the Pixi shell, see `above <#with-pixi>`__, simply run jupyter lab:

::

   jupyter lab

With pip
^^^^^^^^

Using pip, run:

::

   pip install --user ipykernel
   python -m ipykernel install --user --name=lbnenv
   jupyter lab

Once Jupyter lab opens, switch the kernel (Kernel > Change Kernel >
lbnenv)

Development installation
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to develop the project, `clone this
repository <https://github.com/BikeNetKit/linkbikenet/archive/refs/heads/main.zip>`__
and create the environment via `Pixi <https://pixi.prefix.dev/latest/>`__ and the
``environment-dev.yml`` file:

::

   pixi init --import environment-dev.yml

The development environment is called ``lbnenvdev``. At this point you can run linkbikenet in the environment, for example as
such:

::

   pixi run python examples/mwe.py

.. note::

    The first time you run code with Pixi, it might take a minute longer, as Pixi resolves the environment’s dependencies only at this point.

Alternatively, start a pixi shell:

::

   pixi shell

Make sure to also
read `our contribution
guidelines <https://github.com/BikeNetKit/LinkBikeNet?tab=contributing-ov-file#contributing-to-bikenetkit>`__.
