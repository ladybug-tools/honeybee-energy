![Honeybee](http://www.ladybug.tools/assets/img/honeybee.png)

[![Build Status](https://github.com/ladybug-tools/honeybee-energy/workflows/CI/badge.svg)](https://github.com/ladybug-tools/honeybee-energy/actions)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/honeybee-energy/badge.svg?branch=master)](https://coveralls.io/github/ladybug-tools/honeybee-energy)

[![Python 3.10](https://img.shields.io/badge/python3.10-green.svg)](https://www.python.org/downloads/release/python-3100/) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

# honeybee-energy

Honeybee extension for energy simulation.

Honeybee-energy leverages the [EnergyPlus](https://github.com/NREL/EnergyPlus)
simulation engine and the [OpenStudio](https://github.com/NREL/OpenStudio)
SDK in order to add energy simulation properties and capabilities to
[honeybee-core](https://github.com/ladybug-tools/honeybee-core). The package can also
use the [honeybee-openstudio](https://github.com/ladybug-tools/honeybee-openstudio)
Python package to translate honeybee Models to OpenStudio format.

All of these dependencies are contained within the [honeybee-energy Docker image](https://hub.docker.com/r/ladybugtools/honeybee-energy)

Honeybee-energy is also used by other honeybee extensions that translate honeybee
models to building energy simulation engines, including
[honeybee-doe2](https://github.com/ladybug-tools/honeybee-doe2) and
[honeybee_ph](https://github.com/PH-Tools/honeybee_ph).

## Installation

`pip install -U honeybee-energy`

If you want to also include the standards library of typical ProgramTypes and
ConstructionSets use:

`pip install -U honeybee-energy[standards]`

If you want to also include the honeybee-openstudio library to perform translations
to OpenStudio use:

`pip install -U honeybee-energy[openstudio]`

To check if the command line interface is installed correctly use `honeybee-energy --help`.

## [API Documentation](http://ladybug-tools.github.io/honeybee-energy/docs)

## Local Development

1. Clone this repo locally
```console
git clone git@github.com:ladybug-tools/honeybee-energy

# or

git clone https://github.com/ladybug-tools/honeybee-energy
```
2. Install dependencies:
```console
cd honeybee-energy
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

3. Run Tests:
```console
python -m pytest tests/
```

4. Generate Documentation:
```console
sphinx-apidoc -f -e -d 4 -o ./docs ./honeybee_energy
sphinx-build -b html ./docs ./docs/_build/docs
```
