# coding=utf-8
"""Energy Construction Set."""
from __future__ import division

from .material.opaque import EnergyMaterial, EnergyMaterialNoMass
from .material.glazing import EnergyWindowMaterialSimpleGlazSys, \
    EnergyWindowMaterialGlazing
from .material.gas import EnergyWindowMaterialGas, EnergyWindowMaterialGasMixture, \
    EnergyWindowMaterialGasCustom
from .material.shade import EnergyWindowMaterialShade, EnergyWindowMaterialBlind
from .construction import OpaqueConstruction, WindowConstruction
import honeybee_energy.lib.constructions as _lib

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class ConstructionSet(object):
    """Set containing all energy constructions needed to create an energy model.

    Properties:
        name
        wall_set
        floor_set
        roof_ceiling_set
        aperture_set
        door_set
        constructions
        modified_constructions
        unique_constructions
        unique_modified_constructions
        unique_materials
        unique_modified_materials
    """
    __slots__ = ('_name', '_wall_set', '_floor_set', '_roof_ceiling_set',
                 '_aperture_set', '_door_set', '_locked')

    def __init__(self, name, wall_set=None, floor_set=None, roof_ceiling_set=None,
                 aperture_set=None, door_set=None):
        """Initialize energy construction set.

        Args:
            name: Text string for construction set name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            wall_set: An optional WallSet object for this ConstructionSet.
                If None, it will be the honeybee generic default WallSet.
            floor_set: An optional FloorSet object for this ConstructionSet.
                If None, it will be the honeybee generic default FloorSet.
            roof_ceiling_set: An optional RoofCeilingSet object for this ConstructionSet.
                If None, it will be the honeybee generic default RoofCeilingSet.
            aperture_set: An optional ApertureSet object for this ConstructionSet.
                If None, it will be the honeybee generic default ApertureSet.
            door_set: An optional DoorSet object for this ConstructionSet.
                If None, it will be the honeybee generic default DoorSet.
        """
        self._locked = False  # unlocked by default
        self.name = name
        self.wall_set = wall_set
        self.floor_set = floor_set
        self.roof_ceiling_set = roof_ceiling_set
        self.aperture_set = aperture_set
        self.door_set = door_set

    @property
    def name(self):
        """Get or set a text string for construction set name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'construction set name')

    @property
    def wall_set(self):
        """Get or set the WallSet assigned to this ConstructionSet."""
        return self._wall_set

    @wall_set.setter
    def wall_set(self, value):
        if value is not None:
            assert isinstance(value, WallSet), \
                'Expected WallSet. Got {}'.format(type(value))
            self._wall_set = value
        else:
            self._wall_set = WallSet()

    @property
    def floor_set(self):
        """Get or set the FloorSet assigned to this ConstructionSet."""
        return self._floor_set

    @floor_set.setter
    def floor_set(self, value):
        if value is not None:
            assert isinstance(value, FloorSet), \
                'Expected FloorSet. Got {}'.format(type(value))
            self._floor_set = value
        else:
            self._floor_set = FloorSet()

    @property
    def roof_ceiling_set(self):
        """Get or set the RoofCeilingSet assigned to this ConstructionSet."""
        return self._roof_ceiling_set

    @roof_ceiling_set.setter
    def roof_ceiling_set(self, value):
        if value is not None:
            assert isinstance(value, RoofCeilingSet), \
                'Expected RoofCeilingSet. Got {}'.format(type(value))
            self._roof_ceiling_set = value
        else:
            self._roof_ceiling_set = RoofCeilingSet()

    @property
    def aperture_set(self):
        """Get or set the ApertureSet assigned to this ConstructionSet."""
        return self._aperture_set

    @aperture_set.setter
    def aperture_set(self, value):
        if value is not None:
            assert isinstance(value, ApertureSet), \
                'Expected ApertureSet. Got {}'.format(type(value))
            self._aperture_set = value
        else:
            self._aperture_set = ApertureSet()

    @property
    def door_set(self):
        """Get or set the DoorSet assigned to this ConstructionSet."""
        return self._door_set

    @door_set.setter
    def door_set(self, value):
        if value is not None:
            assert isinstance(value, DoorSet), \
                'Expected DoorSet. Got {}'.format(type(value))
            self._door_set = value
        else:
            self._door_set = DoorSet()

    @property
    def constructions(self):
        """List of all constructions contained within the set."""
        return self.wall_set.constructions + \
            self.floor_set.constructions + \
            self.roof_ceiling_set.constructions + \
            self.aperture_set.constructions + \
            self.door_set.constructions

    @property
    def modified_constructions(self):
        """List of all constructions that are not defaulted within the set."""
        return self.wall_set.modified_constructions + \
            self.floor_set.modified_constructions + \
            self.roof_ceiling_set.modified_constructions + \
            self.aperture_set.modified_constructions + \
            self.door_set.modified_constructions

    @property
    def unique_constructions(self):
        """List of all unique constructions contained within the set."""
        return list(set(self.constructions))

    @property
    def unique_modified_constructions(self):
        """List of all unique constructions that are not defaulted within the set."""
        return list(set(self.modified_constructions))

    @property
    def unique_materials(self):
        """List of all unique materials contained within the set."""
        materials = []
        for constr in self.constructions:
            materials.extend(constr.materials)
        return list(set(materials))

    @property
    def unique_modified_materials(self):
        """List of all unique materials that are not defaulted within the set."""
        materials = []
        for constr in self.modified_constructions:
            materials.extend(constr.materials)
        return list(set(materials))

    def get_face_construction(self, face_type, boundary_condition):
        """Get a construction object that will be assigned to a given type of face.

        Args:
            face_type: Text string for the type of face (eg. 'Wall', 'Floor',
                'Roof', 'AirWall').
            boundary_condition: Text string for the boundary condition
                (eg. 'Outdoors', 'Surface', 'Adiabatic', 'Ground')
        """
        if face_type == 'Wall':
            return self._get_constr_from_set(self.wall_set, boundary_condition)
        elif face_type == 'Floor':
            return self._get_constr_from_set(self.floor_set, boundary_condition)
        elif face_type == 'RoofCeiling':
            return self._get_constr_from_set(self.roof_ceiling_set, boundary_condition)
        elif face_type == 'AirWall':
            return _lib.air_wall
        else:
            raise NotImplementedError(
                'Face type {} is not recognized for ConstructionSet'.format(face_type))

    def get_aperture_construction(self, boundary_condition, is_operable,
                                  parent_face_type):
        """Get a construction object that will be assigned to a given type of aperture.

        Args:
            boundary_condition: Text string for the boundary condition
                (eg. 'Outdoors', 'Surface')
            is_operable: Boolean to note whether the aperture is operable.
            parent_face_type: Text string for the type of face to which the aperture
                is a child (eg. 'Wall', 'Floor', 'Roof').
        """
        if boundary_condition == 'Outdoors':
            if not is_operable:
                if parent_face_type == 'Wall':
                    return self.aperture_set.window_construction
                else:
                    return self.aperture_set.skylight_construction
            else:
                return self.aperture_set.operable_construction
        elif boundary_condition == 'Surface':
            return self.aperture_set.interior_construction
        else:
            raise NotImplementedError(
                'Boundary condition {} is not recognized for apertures in '
                'ConstructionSet'.format(boundary_condition))

    def get_door_construction(self, boundary_condition, is_glass, parent_face_type):
        """Get a construction object that will be assigned to a given type of door.

        Args:
            boundary_condition: Text string for the boundary condition
                (eg. 'Outdoors', 'Surface')
            is_glass: Boolean to note whether the door is glass (instead of opaque).
            parent_face_type: Text string for the type of face to which the door
                is a child (eg. 'Wall', 'Floor', 'Roof').
        """
        if boundary_condition == 'Outdoors':
            if not is_glass:
                if parent_face_type == 'Wall':
                    return self.door_set.exterior_construction
                else:
                    return self.door_set.overhead_construction
            else:
                return self.door_set.exterior_glass_construction
        elif boundary_condition == 'Surface':
            if not is_glass:
                return self.door_set.interior_construction
            else:
                return self.door_set.interior_glass_construction
        else:
            raise NotImplementedError(
                'Boundary condition {} is not recognized for doors in '
                'ConstructionSet'.format(boundary_condition))

    @classmethod
    def from_dict(cls, data):
        """Create a ConstructionSet from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: Dictionary describing the ConstructionSet.
        """
        assert data['type'] == 'ConstructionSet', \
            'Expected ConstructionSet. Got {}.'.format(data['type'])

        # gather all material objects
        materials = {}
        for mat in data['materials']:
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

        # gather all construction objects
        constructions = {}
        for cnst in data['constructions']:
            mat_layers = [materials[mat_name] for mat_name in cnst['layers']]
            if cnst['type'] == 'OpaqueConstructionAbridged':
                constructions[cnst['name']] = \
                    OpaqueConstruction(cnst['name'], mat_layers)
            elif cnst['type'] == 'WindowConstructionAbridged':
                constructions[cnst['name']] = \
                    WindowConstruction(cnst['name'], mat_layers)
            else:
                raise NotImplementedError(
                    'Construction {} is not supported.'.format(cnst['type']))
        constructions[None] = None

        # build each of the sub-construction sets
        wall_set = WallSet(
            constructions[data['wall_set']['exterior_construction']],
            constructions[data['wall_set']['interior_construction']],
            constructions[data['wall_set']['ground_construction']])
        floor_set = FloorSet(
            constructions[data['floor_set']['exterior_construction']],
            constructions[data['floor_set']['interior_construction']],
            constructions[data['floor_set']['ground_construction']])
        roof_ceiling_set = RoofCeilingSet(
            constructions[data['roof_ceiling_set']['exterior_construction']],
            constructions[data['roof_ceiling_set']['interior_construction']],
            constructions[data['roof_ceiling_set']['ground_construction']])
        aperture_set = ApertureSet(
            constructions[data['aperture_set']['window_construction']],
            constructions[data['aperture_set']['interior_construction']],
            constructions[data['aperture_set']['skylight_construction']],
            constructions[data['aperture_set']['operable_construction']])
        door_set = DoorSet(
            constructions[data['door_set']['exterior_construction']],
            constructions[data['door_set']['interior_construction']],
            constructions[data['door_set']['exterior_glass_construction']],
            constructions[data['door_set']['interior_glass_construction']],
            constructions[data['door_set']['overhead_construction']])

        return cls(data['name'], wall_set, floor_set, roof_ceiling_set,
                   aperture_set, door_set)

    def to_dict(self, abridged=False, none_for_defaults=True):
        """Get ConstructionSet as a dictionary.

        Args:
            abridged: Boolean noting whether detailed materials and construction
                objects should be written into the ConstructionSet (False) or just
                an abridged version (True). Default: False.
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': 'ConstructionSet'} if not \
            abridged else {'type': 'ConstructionSetAbridged'}
        base['name'] = self.name
        base['wall_set'] = self.wall_set._to_dict(none_for_defaults)
        base['floor_set'] = self.floor_set._to_dict(none_for_defaults)
        base['roof_ceiling_set'] = self.roof_ceiling_set._to_dict(none_for_defaults)
        base['aperture_set'] = self.aperture_set._to_dict(none_for_defaults)
        base['door_set'] = self.door_set._to_dict(none_for_defaults)

        if not abridged:
            if none_for_defaults:
                constructions = self.unique_modified_constructions
                base['constructions'] = [cnst.to_dict(True) for cnst in constructions]
                materials = []
                for cnst in constructions:
                    materials.extend(cnst.materials)
                base['materials'] = [mat.to_dict() for mat in list(set(materials))]
            else:
                constructions = self.unique_constructions
                base['constructions'] = [cnst.to_dict(True) for cnst in constructions]
                materials = []
                for cnst in constructions:
                    materials.extend(cnst.materials)
                base['materials'] = [mat.to_dict() for mat in list(set(materials))]
        return base

    def duplicate(self):
        """Get a copy of this ConstructionSet."""
        return self.__copy__()

    def lock(self):
        """The lock() method to will also lock the WallSet, FloorSet, etc."""
        self._locked = True
        self._wall_set._locked = True
        self._floor_set._locked = True
        self._roof_ceiling_set._locked = True
        self._aperture_set._locked = True
        self._door_set._locked = True

    def unlock(self):
        """The unlock() method will also unlock the WallSet, FloorSet, etc."""
        self._locked = False
        self._wall_set._locked = False
        self._floor_set._locked = False
        self._roof_ceiling_set._locked = False
        self._aperture_set._locked = False
        self._door_set._locked = False

    def _get_constr_from_set(self, face_type_set, boundary_condition):
        """Get a specific construction from a face_type_set."""
        if boundary_condition == 'Outdoors':
            return face_type_set.exterior_construction
        elif boundary_condition == 'Surface' or boundary_condition == 'Adiabatic':
            return face_type_set.interior_construction
        else:
            return face_type_set.ground_construction

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return ConstructionSet(self.name,
                               self.wall_set.duplicate(),
                               self.floor_set.duplicate(),
                               self.roof_ceiling_set.duplicate(),
                               self.aperture_set.duplicate(),
                               self.door_set.duplicate())

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.name,) + tuple(hash(cnstr) for cnstr in self.constructions)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ConstructionSet) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Energy Construction Set: {}'.format(self.name)


@lockable
class _FaceSetBase(object):
    """Base class for the sets assigned to Faces (WallSet, FloorSet, RoofCeilingSet)."""

    __slots__ = ('_exterior_construction', '_interior_construction',
                 '_ground_construction', '_locked')

    def __init__(self, exterior_construction=None, interior_construction=None,
                 ground_construction=None):
        """Initialize set.

        Args:
            exterior_construction: An OpaqueConstruction object for faces with an
                Outdoors boundary condition.
            interior_construction: An OpaqueConstruction object for faces with a
                Surface or Adiabatic boundary condition.
            ground_construction: : An OpaqueConstruction object for faces with a
                Ground boundary condition.
        """
        self._locked = False  # unlocked by default
        self.exterior_construction = exterior_construction
        self.interior_construction = interior_construction
        self.ground_construction = ground_construction

    @property
    def exterior_construction(self):
        """Get or set the OpaqueConstruction for exterior Faces."""
        return self._exterior_construction

    @exterior_construction.setter
    def exterior_construction(self, value):
        self._exterior_construction = value

    @property
    def interior_construction(self):
        """Get or set the OpaqueConstruction for interior Faces."""
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        self._interior_construction = value

    @property
    def ground_construction(self):
        """Get or set the OpaqueConstruction for underground Faces."""
        return self._ground_construction

    @ground_construction.setter
    def ground_construction(self, value):
        self._ground_construction = value

    @property
    def constructions(self):
        """List of all constructions contained within the set."""
        return [self.exterior_construction,
                self.interior_construction,
                self.ground_construction]

    @property
    def modified_constructions(self):
        """List of all constructions that are not defaulted within the set."""
        constructions = []
        if self._exterior_construction is not None:
            constructions.append(self._exterior_construction)
        if self._interior_construction is not None:
            constructions.append(self._interior_construction)
        if self._ground_construction is not None:
            constructions.append(self._ground_construction)
        return constructions

    @property
    def is_modified(self):
        """Boolean noting whether any constructions are modified from the default."""
        return self._exterior_construction is not None or \
            self._interior_construction is not None or \
            self._ground_construction is not None

    def _to_dict(self, none_for_defaults=True):
        """Get the Set as a dictionary.

        Args:
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': self.__class__.__name__ + 'Abridged'}
        if none_for_defaults:
            base['exterior_construction'] = self._exterior_construction.name if \
                self._exterior_construction is not None else None
            base['interior_construction'] = self._interior_construction.name if \
                self._interior_construction is not None else None
            base['ground_construction'] = self._ground_construction.name if \
                self._ground_construction is not None else None
        else:
            base['exterior_construction'] = self.exterior_construction.name
            base['interior_construction'] = self.interior_construction.name
            base['ground_construction'] = self.ground_construction.name
        return base

    def duplicate(self):
        """Get a copy of this set."""
        return self.__copy__()

    def _check_construction(self, value):
        """Check an OpaqueConstruction before assigning it."""
        assert isinstance(value, OpaqueConstruction), \
            'Expected OpaqueConstruction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return 3

    def __iter__(self):
        return iter(self.constructions)

    def __copy__(self):
        return self.__class__(self._exterior_construction, self._interior_construction,
                              self._ground_construction)

    def __repr__(self):
        return 'Base Face Set'


@lockable
class WallSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Walls.

    Properties:
        exterior_construction
        interior_construction
        ground_construction
        constructions
        modified_constructions
        is_modified
    """
    __slots__ = ()

    @property
    def exterior_construction(self):
        """Get or set the OpaqueConstruction for exterior walls."""
        if self._exterior_construction is None:
            return _lib.generic_exterior_wall
        return self._exterior_construction

    @exterior_construction.setter
    def exterior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._exterior_construction = value

    @property
    def interior_construction(self):
        """Get or set the OpaqueConstruction for interior walls."""
        if self._interior_construction is None:
            return _lib.generic_interior_wall
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._interior_construction = value

    @property
    def ground_construction(self):
        """Get or set the OpaqueConstruction for underground walls."""
        if self._ground_construction is None:
            return _lib.generic_underground_wall
        return self._ground_construction

    @ground_construction.setter
    def ground_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._ground_construction = value

    def __repr__(self):
        return 'Wall Construction Set:\n Exterior: {}\n Interior: {}' \
            '\n Ground: {}'.format(self.exterior_construction.name,
                                   self.interior_construction.name,
                                   self.ground_construction.name)


@lockable
class FloorSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Floors.

    Properties:
        exterior_construction
        interior_construction
        ground_construction
        constructions
        modified_constructions
        is_modified
    """
    __slots__ = ()

    @property
    def exterior_construction(self):
        """Get or set the OpaqueConstruction for exterior-exposed floors."""
        if self._exterior_construction is None:
            return _lib.generic_exposed_floor
        return self._exterior_construction

    @exterior_construction.setter
    def exterior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._exterior_construction = value

    @property
    def interior_construction(self):
        """Get or set the OpaqueConstruction for interior floors."""
        if self._interior_construction is None:
            return _lib.generic_interior_floor
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._interior_construction = value

    @property
    def ground_construction(self):
        """Get or set the OpaqueConstruction for ground-contact floor slabs."""
        if self._ground_construction is None:
            return _lib.generic_ground_slab
        return self._ground_construction

    @ground_construction.setter
    def ground_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._ground_construction = value

    def __repr__(self):
        return 'Floor Construction Set:\n Exterior: {}\n Interior: {}' \
            '\n Ground: {}'.format(self.exterior_construction.name,
                                   self.interior_construction.name,
                                   self.ground_construction.name)


@lockable
class RoofCeilingSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Roofs.

    Properties:
        exterior_construction
        interior_construction
        ground_construction
        constructions
        modified_constructions
        is_modified
    """
    __slots__ = ()

    @property
    def exterior_construction(self):
        """Get or set the OpaqueConstruction for exterior roofs."""
        if self._exterior_construction is None:
            return _lib.generic_roof
        return self._exterior_construction

    @exterior_construction.setter
    def exterior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._exterior_construction = value

    @property
    def interior_construction(self):
        """Get or set the OpaqueConstruction for interior ceilings."""
        if self._interior_construction is None:
            return _lib.generic_interior_ceiling
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._interior_construction = value

    @property
    def ground_construction(self):
        """Get or set the OpaqueConstruction for underground roofs."""
        if self._ground_construction is None:
            return _lib.generic_underground_roof
        return self._ground_construction

    @ground_construction.setter
    def ground_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._ground_construction = value

    def __repr__(self):
        return 'RoofCeiling Construction Set:\n Exterior: {}\n Interior: {}' \
            '\n Ground: {}'.format(self.exterior_construction.name,
                                   self.interior_construction.name,
                                   self.ground_construction.name)


@lockable
class ApertureSet(object):
    """Set containing all energy constructions needed to for an energy model's Apertures.

    Properties:
        window_construction
        interior_construction
        skylight_construction
        operable_construction
        constructions
        modified_constructions
        is_modified
    """
    __slots__ = ('_window_construction', '_interior_construction',
                 '_skylight_construction', '_operable_construction', '_locked')

    def __init__(self, window_construction=None, interior_construction=None,
                 skylight_construction=None, operable_construction=None):
        """Initialize aperture set.

        Args:
            window_construction: A WindowConstruction object for apertures
                with an Outdoors boundary condition, False is_operable property,
                and a Wall face type for their parent face.
            interior_construction: A WindowConstruction object for all apertures
                with a Surface boundary condition.
            skylight_construction: : A WindowConstruction object for apertures with a
                Outdoors boundary condition, False is_operable property, and a
                RoofCeiling or Floor face type for their parent face.
            operable_construction: A WindowConstruction object for all apertures
                with an Outdoors boundary condition and True is_operable property.
        """
        self._locked = False  # unlocked by default
        self.window_construction = window_construction
        self.interior_construction = interior_construction
        self.skylight_construction = skylight_construction
        self.operable_construction = operable_construction

    @property
    def window_construction(self):
        """Get or set the WindowConstruction for exterior fixed windows in walls."""
        if self._window_construction is None:
            return _lib.generic_double_pane
        return self._window_construction

    @window_construction.setter
    def window_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._window_construction = value

    @property
    def interior_construction(self):
        """Get or set the WindowConstruction for all interior apertures."""
        if self._interior_construction is None:
            return _lib.generic_single_pane
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._interior_construction = value

    @property
    def skylight_construction(self):
        """Get or set the WindowConstruction for exterior fixed windows in roofs."""
        if self._skylight_construction is None:
            return _lib.generic_double_pane
        return self._skylight_construction

    @skylight_construction.setter
    def skylight_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._skylight_construction = value

    @property
    def operable_construction(self):
        """Get or set the WindowConstruction for all exterior operable windows."""
        if self._operable_construction is None:
            return _lib.generic_double_pane
        return self._operable_construction

    @operable_construction.setter
    def operable_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._operable_construction = value

    @property
    def constructions(self):
        """List of all constructions contained within the set."""
        return [self.window_construction,
                self.interior_construction,
                self.skylight_construction,
                self.operable_construction]

    @property
    def modified_constructions(self):
        """List of all constructions that are not defaulted within the set."""
        constructions = []
        if self._window_construction is not None:
            constructions.append(self._window_construction)
        if self._interior_construction is not None:
            constructions.append(self._interior_construction)
        if self._skylight_construction is not None:
            constructions.append(self._skylight_construction)
        if self._operable_construction is not None:
            constructions.append(self._operable_construction)
        return constructions

    @property
    def is_modified(self):
        """Boolean noting whether any constructions are modified from the default."""
        return self._window_construction is not None or \
            self._interior_construction is not None or \
            self._skylight_construction is not None or \
            self._operable_construction is not None

    def _to_dict(self, none_for_defaults=True):
        """Get ApertureSetAbridged as a dictionary.

        Args:
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': 'ApertureSetAbridged'}
        if none_for_defaults:
            base['window_construction'] = self._window_construction.name if \
                self._window_construction is not None else None
            base['interior_construction'] = self._interior_construction.name if \
                self._interior_construction is not None else None
            base['skylight_construction'] = self._skylight_construction.name if \
                self._skylight_construction is not None else None
            base['operable_construction'] = \
                self._operable_construction.name if \
                self._operable_construction is not None else None
        else:
            base['window_construction'] = self.window_construction.name
            base['interior_construction'] = self.interior_construction.name
            base['skylight_construction'] = self.skylight_construction.name
            base['operable_construction'] = \
                self.operable_construction.name
        return base

    def duplicate(self):
        """Get a copy of this set."""
        return self.__copy__()

    def _check_window_construction(self, value):
        """Check that a construction is valid before assigning it."""
        assert isinstance(value, WindowConstruction), \
            'Expected WindowConstruction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return 4

    def __iter__(self):
        return iter(self.constructions)

    def __copy__(self):
        return self.__class__(
            self._window_construction, self._interior_construction,
            self._skylight_construction, self._operable_construction)

    def __repr__(self):
        return 'Aperture Construction Set:\n Window: {}\n Interior: {}' \
            '\n Skylight: {}\n Operable: {}'.format(
                self.window_construction.name, self.interior_construction.name,
                self.skylight_construction.name, self.operable_construction.name)


@lockable
class DoorSet(object):
    """Set containing all energy constructions needed to for an energy model's Roofs.

    Properties:
        exterior_construction
        interior_construction
        exterior_glass_construction
        interior_glass_construction
        overhead_construction
        constructions
        modified_constructions
        is_modified
    """
    __slots__ = ('_exterior_construction', '_interior_construction',
                 '_exterior_glass_construction', '_interior_glass_construction',
                 '_overhead_construction', '_locked')

    def __init__(self, exterior_construction=None, interior_construction=None,
                 exterior_glass_construction=None, interior_glass_construction=None,
                 overhead_construction=None):
        """Initialize door set.

        Args:
            exterior_construction: An OpaqueConstruction object for opaque doors with an
                Outdoors boundary condition and a Wall face type for their parent face.
            interior_construction: An OpaqueConstruction object for all opaque doors
                with a Surface boundary condition.
            exterior_glass_construction: A WindowConstruction object for all glass
                doors with an Outdoors boundary condition.
            interior_glass_construction: A WindowConstruction object for all glass
                doors with a Surface boundary condition.
            overhead_construction: : An OpaqueConstruction object for opaque doors with
                an Outdoors boundary condition and a RoofCeiling or Floor face type for
                their parent face.
        """
        self._locked = False  # unlocked by default
        self.exterior_construction = exterior_construction
        self.interior_construction = interior_construction
        self.exterior_glass_construction = exterior_glass_construction
        self.interior_glass_construction = interior_glass_construction
        self.overhead_construction = overhead_construction

    @property
    def exterior_construction(self):
        """Get or set the OpaqueConstruction for exterior opaque doors in walls."""
        if self._exterior_construction is None:
            return _lib.generic_exterior_door
        return self._exterior_construction

    @exterior_construction.setter
    def exterior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._exterior_construction = value

    @property
    def interior_construction(self):
        """Get or set the OpaqueConstruction for all interior opaque doors."""
        if self._interior_construction is None:
            return _lib.generic_interior_door
        return self._interior_construction

    @interior_construction.setter
    def interior_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._interior_construction = value

    @property
    def exterior_glass_construction(self):
        """Get or set the WindowConstruction for exterior glass doors."""
        if self._exterior_glass_construction is None:
            return _lib.generic_double_pane
        return self._exterior_glass_construction

    @exterior_glass_construction.setter
    def exterior_glass_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._exterior_glass_construction = value

    @property
    def interior_glass_construction(self):
        """Get or set the WindowConstruction for all interior glass doors."""
        if self._interior_glass_construction is None:
            return _lib.generic_single_pane
        return self._interior_glass_construction

    @interior_glass_construction.setter
    def interior_glass_construction(self, value):
        if value is not None:
            self._check_window_construction(value)
        self._interior_glass_construction = value

    @property
    def overhead_construction(self):
        """Get or set the OpaqueConstruction for exterior opaque doors in roofs/floors.
        """
        if self._overhead_construction is None:
            return _lib.generic_exterior_door
        return self._overhead_construction

    @overhead_construction.setter
    def overhead_construction(self, value):
        if value is not None:
            self._check_construction(value)
        self._overhead_construction = value

    @property
    def constructions(self):
        """List of all constructions contained within the set."""
        return [self.exterior_construction,
                self.interior_construction,
                self.exterior_glass_construction,
                self.interior_glass_construction,
                self.overhead_construction]

    @property
    def modified_constructions(self):
        """List of all constructions that are not defaulted within the set."""
        constructions = []
        if self._exterior_construction is not None:
            constructions.append(self._exterior_construction)
        if self._interior_construction is not None:
            constructions.append(self._interior_construction)
        if self._exterior_glass_construction is not None:
            constructions.append(self._exterior_glass_construction)
        if self._interior_glass_construction is not None:
            constructions.append(self._interior_glass_construction)
        if self._overhead_construction is not None:
            constructions.append(self._overhead_construction)
        return constructions

    @property
    def is_modified(self):
        """Boolean noting whether any constructions are modified from the default."""
        return self._exterior_construction is not None or \
            self._interior_construction is not None or \
            self._exterior_glass_construction is not None or \
            self._interior_glass_construction is not None or \
            self._overhead_construction is None

    def _to_dict(self, none_for_defaults=True):
        """Get the DoorSet as a dictionary.

        Args:
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': 'DoorSetAbridged'}
        if none_for_defaults:
            base['exterior_construction'] = self._exterior_construction.name if \
                self._exterior_construction is not None else None
            base['interior_construction'] = self._interior_construction.name if \
                self._interior_construction is not None else None
            base['exterior_glass_construction'] = \
                self._exterior_glass_construction.name if \
                self._exterior_glass_construction is not None else None
            base['interior_glass_construction'] = \
                self._interior_glass_construction.name if \
                self._interior_glass_construction is not None else None
            base['overhead_construction'] = self._overhead_construction.name if \
                self._overhead_construction is not None else None
        else:
            base['exterior_construction'] = self.exterior_construction.name
            base['interior_construction'] = self.interior_construction.name
            base['exterior_glass_construction'] = self.exterior_glass_construction.name
            base['interior_glass_construction'] = self.interior_glass_construction.name
            base['overhead_construction'] = self.overhead_construction.name
        return base

    def duplicate(self):
        """Get a copy of this set."""
        return self.__copy__()

    def _check_construction(self, value):
        """Check an OpaqueConstruction before assigning it."""
        assert isinstance(value, OpaqueConstruction), \
            'Expected OpaqueConstruction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def _check_window_construction(self, value):
        """Check that a construction is valid before assigning it."""
        assert isinstance(value, WindowConstruction), \
            'Expected WindowConstruction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return 5

    def __iter__(self):
        return iter(self.constructions)

    def __copy__(self):
        return self.__class__(
            self._exterior_construction, self._interior_construction,
            self._exterior_glass_construction, self._interior_glass_construction,
            self._overhead_construction)

    def __repr__(self):
        return 'Door Construction Set:\n Exterior: {}\n Interior: {}' \
            '\n Exterior Glass: {}\n Interior Glass: {}\n Overhead: {}'.format(
                self.exterior_construction.name, self.interior_construction.name,
                self.exterior_glass_construction.name,
                self.interior_glass_construction.name, self.overhead_construction.name)
