"""Load all materials from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys
from honeybee_energy.material.gas import EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom
from honeybee_energy.material.shade import EnergyWindowMaterialShade, \
    EnergyWindowMaterialBlind

import os
import json


# empty dictionaries to hold idf-loaded materials and constructions
_idf_opaque_materials = {}
_idf_window_materials = {}

# load materials from the default and user-supplied files
for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path) as json_file:
            data = json.load(json_file)
        for mat_name in data:
            try:
                mat_dict = data[mat_name]
                if mat_dict['type'] == 'EnergyMaterial':
                    _idf_opaque_materials[mat_dict['name']] = \
                        EnergyMaterial.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyMaterialNoMass':
                    _idf_opaque_materials[mat_dict['name']] = \
                        EnergyMaterialNoMass.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialGlazing':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialGlazing.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialSimpleGlazSys':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialSimpleGlazSys.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialGas':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialGas.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialGasMixture':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialGasMixture.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialGasCustom':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialGasCustom.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialShade':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialShade.from_dict(mat_dict)
                elif mat_dict['type'] == 'EnergyWindowMaterialBlind':
                    _idf_window_materials[mat_dict['name']] = \
                        EnergyWindowMaterialBlind.from_dict(mat_dict)
            except KeyError:
                pass  # not a Honeybee JSON file with Materials
