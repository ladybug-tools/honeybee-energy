# coding=utf-8
"""Model Energy Properties."""
from honeybee.extensionutil import model_extension_dicts

from ..lib.constructionsets import generic_costruction_set

from ..material.opaque import EnergyMaterial, EnergyMaterialNoMass
from ..material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys
from ..material.gas import EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom
from ..material.shade import EnergyWindowMaterialShade, EnergyWindowMaterialBlind
from ..construction import OpaqueConstruction, WindowConstruction
from ..constructionset import ConstructionSet, WallSet, FloorSet, RoofCeilingSet, \
    ApertureSet, DoorSet

try:
    from itertools import izip as zip  # python 2
except ImportError:
    pass   # python 3


class ModelEnergyProperties(object):
    """Energy Properties for Honeybee Model.

    Properties:
        unique_materials
        unique_constructions
        unique_face_constructions
        unique_construction_sets
        global_construction_set
    """

    def __init__(self, host):
        """Initialize Model energy properties.

        Args:
            host: A honeybee_core Model object that hosts these properties.
        """
        self._host = host

    @property
    def host(self):
        """Get the Model object hosting these properties."""
        return self._host

    @property
    def unique_materials(self):
        """List of all unique materials contained within the model.

        This includes materials across all Faces, Apertures, Doors, Room
        ConstructionSets, and the global_construction_set.
        """
        materials = []
        for constr in self.unique_constructions:
            materials.extend(constr.materials)
        return list(set(materials))

    @property
    def unique_constructions(self):
        """A list of all unique constructions in the model.

        This includes constructions across all Faces, Apertures, Doors, Room
        ConstructionSets, and the global_construction_set.
        """
        room_constrs = []
        for cnstr_set in self.unique_construction_sets:
            room_constrs.extend(cnstr_set.unique_modified_constructions)
        all_constrs = self.global_construction_set.unique_constructions + \
            room_constrs + self.unique_face_constructions
        return list(set(all_constrs))

    @property
    def unique_face_constructions(self):
        """A list of all unique constructions assigned to Faces, Apertures and Doors."""
        constructions = []
        for room in self.host.rooms:
            for face in room.faces:  # check all Face constructions
                if face.properties.energy._construction is not None:
                    if not self._instance_in_array(
                            face.properties.energy._construction, constructions):
                        constructions.append(face.properties.energy._construction)
                for ap in face.apertures:  # check all Aperture constructions
                    if ap.properties.energy._construction is not None:
                        if not self._instance_in_array(
                                ap.properties.energy._construction, constructions):
                            constructions.append(ap.properties.energy._construction)
                for dr in face.doors:  # check all Door constructions
                    if dr.properties.energy._construction is not None:
                        if not self._instance_in_array(
                                dr.properties.energy._construction, constructions):
                            constructions.append(dr.properties.energy._construction)
        return list(set(constructions))

    @property
    def unique_construction_sets(self):
        """A list of all unique Room-Assigned ConstructionSets in the Model."""
        construction_sets = []
        for room in self.host.rooms:
            if room.properties.energy._construction_set is not None:
                if not self._instance_in_array(room.properties.energy._construction_set,
                                               construction_sets):
                    construction_sets.append(room.properties.energy._construction_set)
        return list(set(construction_sets))  # catch equivalent construction sets

    @property
    def global_construction_set(self):
        """A default ConstructionSet object for all unassigned objects in the Model.

        This ConstructionSet will be written in its entirety to the dictionary
        representation of ModelEnergyProperties as well as the resulting OpenStudio
        model.  This is to ensure that all objects lacking a construction specification
        always have a default.
        """
        return generic_costruction_set

    def check_duplicate_construction_set_names(self, raise_exception=True):
        """Check that there are no duplicate ConstructionSet names in the model."""
        con_set_names = set()
        duplicate_names = set()
        for con_set in self.unique_construction_sets + [self.global_construction_set]:
            if con_set.name not in con_set_names:
                con_set_names.add(con_set.name)
            else:
                duplicate_names.add(con_set.name)
        if len(duplicate_names) != 0:
            if raise_exception:
                raise ValueError(
                    'The model has the following duplicated ConstructionSet '
                    'names:\n{}'.format('\n'.join(duplicate_names)))
            return False
        return True

    def check_duplicate_construction_names(self, raise_exception=True):
        """Check that there are no duplicate Construction names in the model."""
        cnstr_names = set()
        duplicate_names = set()
        for cnstr in self.unique_constructions:
            if cnstr.name not in cnstr_names:
                cnstr_names.add(cnstr.name)
            else:
                duplicate_names.add(cnstr.name)
        if len(duplicate_names) != 0:
            if raise_exception:
                raise ValueError(
                    'The model has the following duplicated Construction '
                    'names:\n{}'.format('\n'.join(duplicate_names)))
            return False
        return True

    def check_duplicate_material_names(self, raise_exception=True):
        """Check that there are no duplicate Material names in the model."""
        material_names = set()
        duplicate_names = set()
        for mat in self.unique_materials:
            if mat.name not in material_names:
                material_names.add(mat.name)
            else:
                duplicate_names.add(mat.name)
        if len(duplicate_names) != 0:
            if raise_exception:
                raise ValueError(
                    'The model has the following duplicated Material '
                    'names:\n{}'.format('\n'.join(duplicate_names)))
            return False
        return True

    def apply_properties_from_dict(self, data):
        """Apply the energy properties of a dictionary to the host Model of this object.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
                Note that this dictionary must have ModelEnergyProperties in order
                for this method to successfully apply the energy properties.
        """
        assert 'energy' in data['properties'], \
            'Dictionary possesses no ModelEnergyProperties.'

        # process all materials in the ModelEnergyProperties dictionary
        materials = {}
        for mat in data['properties']['energy']['materials']:
            if mat['type'] == 'EnergyMaterial':
                materials[mat['name']] = EnergyMaterial.from_dict(mat)
            elif mat['type'] == 'EnergyMaterialNoMass':
                materials[mat['name']] = EnergyMaterialNoMass.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialSimpleGlazSys':
                materials[mat['name']] = EnergyWindowMaterialSimpleGlazSys.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGlazing':
                materials[mat['name']] = EnergyWindowMaterialGlazing.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGas':
                materials[mat['name']] = EnergyWindowMaterialGas.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGasMixture':
                materials[mat['name']] = EnergyWindowMaterialGasMixture.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGasCustom':
                materials[mat['name']] = EnergyWindowMaterialGasCustom.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialShade':
                materials[mat['name']] = EnergyWindowMaterialShade.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialBlind':
                materials[mat['name']] = EnergyWindowMaterialBlind.from_dict(mat)
            else:
                raise NotImplementedError(
                    'Material {} is not supported.'.format(mat['type']))

        # process all constructions in the ModelEnergyProperties dictionary
        constructions = {}
        for cnstr in data['properties']['energy']['constructions']:
            mat_layers = [materials[mat_name] for mat_name in cnstr['layers']]
            if cnstr['type'] == 'OpaqueConstructionAbridged':
                constructions[cnstr['name']] = \
                    OpaqueConstruction(cnstr['name'], mat_layers)
            elif cnstr['type'] == 'WindowConstructionAbridged':
                constructions[cnstr['name']] = \
                    WindowConstruction(cnstr['name'], mat_layers)
            else:
                raise NotImplementedError(
                    'Construction {} is not supported.'.format(cnstr['type']))

        # process all construction sets in the ModelEnergyProperties dictionary
        construction_sets = {}
        for c_set in data['properties']['energy']['construction_sets']:
            wall_set = self._make_construction_subset(
                c_set, WallSet(), 'wall_set', constructions)
            floor_set = self._make_construction_subset(
                c_set, FloorSet(), 'floor_set', constructions)
            roof_ceiling_set = self._make_construction_subset(
                c_set, RoofCeilingSet(), 'roof_ceiling_set', constructions)
            aperture_set = self._make_aperture_subset(
                c_set, ApertureSet(), constructions)
            door_set = self._make_door_subset(c_set, DoorSet(), constructions)
            construction_sets[c_set['name']] = ConstructionSet(
                c_set['name'], wall_set, floor_set, roof_ceiling_set,
                aperture_set, door_set)

        # collect lists of energy property dictionaries
        room_e_dicts, face_e_dicts, shd_e_dicts, ap_e_dicts, dr_e_dicts = \
            model_extension_dicts(data, 'energy')

        # apply energy properties to objects uwing the energy property dictionaries
        for room, r_dict in zip(self.host.rooms, room_e_dicts):
            room.properties.energy.apply_properties_from_dict(r_dict, construction_sets)
        for face, f_dict in zip(self.host.faces, face_e_dicts):
            face.properties.energy.apply_properties_from_dict(f_dict, constructions)
        for shade, s_dict in zip(self.host.shades, shd_e_dicts):
            shade.properties.energy.apply_properties_from_dict(s_dict)
        for aperture, a_dict in zip(self.host.apertures, ap_e_dicts):
            aperture.properties.energy.apply_properties_from_dict(a_dict, constructions)
        for aperture, a_dict in zip(self.host.apertures, ap_e_dicts):
            aperture.properties.energy.apply_properties_from_dict(a_dict, constructions)

    def to_dict(self, include_global_construction_set=True):
        """Return Model energy properties as a dictionary.

        include_global_construction_set: Boolean to note whether the
            global_construction_set should be included within the dictionary. This
            will ensure that all objects lacking a construction specification always
            have a default construction. Default: True.
        """
        base = {'energy': {'type': 'ModelEnergyProperties'}}

        # add all ConstructionSets to the dictionary
        base['energy']['construction_sets'] = []
        if include_global_construction_set:
            base['energy']['global_construction_set'] = self.global_construction_set.name
            base['energy']['construction_sets'].append(
                self.global_construction_set.to_dict(abridged=True,
                                                     none_for_defaults=False))
        construction_sets = self.unique_construction_sets
        for cnstr_set in construction_sets:
            base['energy']['construction_sets'].append(cnstr_set.to_dict(abridged=True))

        # add all unique Constructions to the dictionary
        room_constrs = []
        for cnstr_set in construction_sets:
            room_constrs.extend(cnstr_set.unique_modified_constructions)
        all_constrs = room_constrs + self.unique_face_constructions
        if include_global_construction_set:
            all_constrs.extend(self.global_construction_set.unique_constructions)
        constructions = list(set(all_constrs))
        base['energy']['constructions'] = [cnstr.to_dict(abridged=True)
                                           for cnstr in constructions]

        # add all unique Materials to the dictionary
        materials = []
        for cnstr in constructions:
            materials.extend(cnstr.materials)
        base['energy']['materials'] = [mat.to_dict() for mat in set(materials)]
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Model object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return ModelEnergyProperties(_host)

    @staticmethod
    def _instance_in_array(object_instance, object_array):
        """Check if a specific object instance is already in an array.

        This can be much faster than  `if object_instance in object_arrary`
        when you expect to be testing a lot of the same instance of an object for
        inclusion in an array since the builtin method uses an == operator to
        test inclusion.
        """
        for val in object_array:
            if val is object_instance:
                return True
        return False

    @staticmethod
    def _make_construction_subset(c_set, sub_set, sub_set_name, constructions):
        """Make a WallSet, FloorSet, or RoofCeilingSet from dictaionary."""
        if sub_set_name in c_set:
            if 'exterior_construction' in c_set[sub_set_name] and \
                    c_set[sub_set_name]['exterior_construction'] is not None:
                sub_set.exterior_construction = \
                    constructions[c_set[sub_set_name]['exterior_construction']]
            if 'interior_construction' in c_set[sub_set_name] and \
                    c_set[sub_set_name]['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[c_set[sub_set_name]['interior_construction']]
            if 'ground_construction' in c_set[sub_set_name] and \
                    c_set[sub_set_name]['ground_construction'] is not None:
                sub_set.ground_construction = \
                    constructions[c_set[sub_set_name]['ground_construction']]
        return sub_set

    @staticmethod
    def _make_aperture_subset(c_set, sub_set, constructions):
        """Make an ApertureSet from a dictionary."""
        if 'aperture_set' in c_set:
            if 'fixed_window_construction' in c_set['aperture_set'] and \
                    c_set['aperture_set']['fixed_window_construction'] is not None:
                sub_set.fixed_window_construction = \
                    constructions[c_set['aperture_set']['fixed_window_construction']]
            if 'interior_construction' in c_set['aperture_set'] and \
                    c_set['aperture_set']['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[c_set['aperture_set']['interior_construction']]
            if 'skylight_construction' in c_set['aperture_set'] and \
                    c_set['aperture_set']['skylight_construction'] is not None:
                sub_set.skylight_construction = \
                    constructions[c_set['aperture_set']['skylight_construction']]
            if 'operable_window_construction' in c_set['aperture_set'] and \
                    c_set['aperture_set']['operable_window_construction'] is not None:
                sub_set.operable_window_construction = \
                    constructions[c_set['aperture_set']['operable_window_construction']]
            if 'glass_door_construction' in c_set['aperture_set'] and \
                    c_set['aperture_set']['glass_door_construction'] is not None:
                sub_set.glass_door_construction = \
                    constructions[c_set['aperture_set']['glass_door_construction']]
        return sub_set

    @staticmethod
    def _make_door_subset(c_set, sub_set, constructions):
        """Make a WallSet, FloorSet, or RoofCeilingSet from dictaionary."""
        if 'door_set' in c_set:
            if 'exterior_construction' in c_set['door_set'] and \
                    c_set['door_set']['exterior_construction'] is not None:
                sub_set.exterior_construction = \
                    constructions[c_set['door_set']['exterior_construction']]
            if 'interior_construction' in c_set['door_set'] and \
                    c_set['door_set']['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[c_set['door_set']['interior_construction']]
            if 'overhead_construction' in c_set['door_set'] and \
                    c_set['door_set']['overhead_construction'] is not None:
                sub_set.overhead_construction = \
                    constructions[c_set['door_set']['overhead_construction']]
        return sub_set

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Model Energy Properties'
