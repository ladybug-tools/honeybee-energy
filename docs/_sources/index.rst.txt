Welcome to Honeybee Energy's documentation!
===========================================

.. image:: http://www.ladybug.tools/assets/img/honeybee.png

`EnergyPlus <https://energyplus.net//>`_ extension for `honeybee <https://github.com/ladybug-tools/honeybee-core/>`_

Honeybee-energy adds EnergyPlus/OpenStudio functionalities to honeybee for energy simulation.


Installation
============

``pip install -U honeybee-energy``

If you want to also include the standards library of typical ProgramTypes and
ConstructionSets use.

``pip install -U honeybee-energy[standards]``

To check if the command line interface is installed correctly use ``honeybee-energy --help``


CLI Docs
=============

For command line interface documentation and API documentation see the pages below.


.. toctree::
   :maxdepth: 2

   cli/index


honeybee_energy
=============

.. toctree::
   :maxdepth: 4

   modules

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
