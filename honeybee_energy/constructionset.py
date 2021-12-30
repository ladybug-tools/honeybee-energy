# coding=utf-8
"""Energy Construction Set."""
from __future__ import division

from .construction.dictutil import dict_to_construction
from .construction.opaque import OpaqueConstruction
from .construction.window import WindowConstruction
from .construction.windowshade import WindowConstructionShade
from .construction.dynamic import WindowConstructionDynamic
from .construction.shade import ShadeConstruction
from .construction.air import AirBoundaryConstruction
import honeybee_energy.lib.constructions as _lib

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, clean_rad_string


@lockable
class ConstructionSet(object):
    """Set containing all energy constructions needed to create an energy model.

    Args:
        identifier: Text string for a unique ConstructionSet ID. Must be < 100
            characters and not contain any EnergyPlus special characters. This
            will be used to identify the object across a model and in the
            exported IDF.
        wall_set: An optional WallConstructionSet object for this ConstructionSet.
            If None, it will be the honeybee generic default WallConstructionSet.
        floor_set: An optional FloorConstructionSet object for this ConstructionSet.
            If None, it will be the honeybee generic default FloorConstructionSet.
        roof_ceiling_set: An optional RoofCeilingConstructionSet object for this
            ConstructionSet. If None, it will be the honeybee generic default
            RoofCeilingConstructionSet.
        aperture_set: An optional ApertureConstructionSet object for this
            ConstructionSet. If None, it will be the honeybee generic default
            ApertureConstructionSet.
        door_set: An optional DoorConstructionSet object for this ConstructionSet.
            If None, it will be the honeybee generic default DoorConstructionSet.
        shade_construction: An optional ShadeConstruction to set the reflectance
            properties of all outdoor shades to which this ConstructionSet is
            assigned. If None, it will be the honeybee generic shade construction.
        air_boundary_construction: An optional AirBoundaryConstruction or
            OpaqueConstruction to set the properties of Faces with an AirBoundary
            type. If None, it will be the honeybee generic air boundary construction.

    Properties:
        * identifier
        * display_name
        * wall_set
        * floor_set
        * roof_ceiling_set
        * aperture_set
        * door_set
        * shade_construction
        * air_boundary_construction
        * constructions
        * modified_constructions
        * constructions_unique
        * modified_constructions_unique
        * materials_unique
        * modified_materials_unique
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_wall_set', '_floor_set',
                 '_roof_ceiling_set', '_aperture_set', '_door_set',
                 '_shade_construction', '_air_boundary_construction',
                 '_locked', '_user_data')

    def __init__(self, identifier, wall_set=None, floor_set=None, roof_ceiling_set=None,
                 aperture_set=None, door_set=None, shade_construction=None,
                 air_boundary_construction=None):
        """Initialize energy construction set."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.wall_set = wall_set
        self.floor_set = floor_set
        self.roof_ceiling_set = roof_ceiling_set
        self.aperture_set = aperture_set
        self.door_set = door_set
        self.shade_construction = shade_construction
        self.air_boundary_construction = air_boundary_construction
        self._user_data = None

    @property
    def identifier(self):
        """Get or set a text string for a unique construction set identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'construction set identifier')

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def wall_set(self):
        """Get or set the WallConstructionSet assigned to this ConstructionSet."""
        return self._wall_set

    @wall_set.setter
    def wall_set(self, value):
        if value is not None:
            assert isinstance(value, WallConstructionSet), \
                'Expected WallConstructionSet. Got {}'.format(type(value))
            self._wall_set = value
        else:
            self._wall_set = WallConstructionSet()

    @property
    def floor_set(self):
        """Get or set the FloorConstructionSet assigned to this ConstructionSet."""
        return self._floor_set

    @floor_set.setter
    def floor_set(self, value):
        if value is not None:
            assert isinstance(value, FloorConstructionSet), \
                'Expected FloorConstructionSet. Got {}'.format(type(value))
            self._floor_set = value
        else:
            self._floor_set = FloorConstructionSet()

    @property
    def roof_ceiling_set(self):
        """Get or set the RoofCeilingConstructionSet assigned to this ConstructionSet."""
        return self._roof_ceiling_set

    @roof_ceiling_set.setter
    def roof_ceiling_set(self, value):
        if value is not None:
            assert isinstance(value, RoofCeilingConstructionSet), \
                'Expected RoofCeilingConstructionSet. Got {}'.format(type(value))
            self._roof_ceiling_set = value
        else:
            self._roof_ceiling_set = RoofCeilingConstructionSet()

    @property
    def aperture_set(self):
        """Get or set the ApertureConstructionSet assigned to this ConstructionSet."""
        return self._aperture_set

    @aperture_set.setter
    def aperture_set(self, value):
        if value is not None:
            assert isinstance(value, ApertureConstructionSet), \
                'Expected ApertureConstructionSet. Got {}'.format(type(value))
            self._aperture_set = value
        else:
            self._aperture_set = ApertureConstructionSet()

    @property
    def door_set(self):
        """Get or set the DoorConstructionSet assigned to this ConstructionSet."""
        return self._door_set

    @door_set.setter
    def door_set(self, value):
        if value is not None:
            assert isinstance(value, DoorConstructionSet), \
                'Expected DoorConstructionSet. Got {}'.format(type(value))
            self._door_set = value
        else:
            self._door_set = DoorConstructionSet()

    @property
    def shade_construction(self):
        """Get or set the ShadeConstruction assigned to this ConstructionSet."""
        if self._shade_construction is None:
            return _lib.generic_shade
        return self._shade_construction

    @shade_construction.setter
    def shade_construction(self, value):
        if value is not None:
            assert isinstance(value, ShadeConstruction), \
                'Expected ShadeConstruction. Got {}'.format(type(value))
            value.lock()   # lock editing in case construction has multiple references
        self._shade_construction = value

    @property
    def air_boundary_construction(self):
        """Get or set the AirBoundaryConstruction assigned to this ConstructionSet."""
        if self._air_boundary_construction is None:
            return _lib.air_boundary
        return self._air_boundary_construction

    @air_boundary_construction.setter
    def air_boundary_construction(self, value):
        if value is not None:
            assert isinstance(value, (AirBoundaryConstruction, OpaqueConstruction)), \
                'Expected AirBoundaryConstruction or OpaqueConstruction. ' \
                'Got {}'.format(type(value))
            value.lock()   # lock editing in case construction has multiple references
        self._air_boundary_construction = value

    @property
    def constructions(self):
        """List of all constructions contained within the set."""
        return self.wall_set.constructions + \
            self.floor_set.constructions + \
            self.roof_ceiling_set.constructions + \
            self.aperture_set.constructions + \
            self.door_set.constructions + \
            [self.shade_construction, self.air_boundary_construction]

    @property
    def modified_constructions(self):
        """List of all constructions that are not defaulted within the set."""
        mod_constructions = self.wall_set.modified_constructions + \
            self.floor_set.modified_constructions + \
            self.roof_ceiling_set.modified_constructions + \
            self.aperture_set.modified_constructions + \
            self.door_set.modified_constructions
        if self._shade_construction is not None:
            mod_constructions.append(self._shade_construction)
        if self._air_boundary_construction is not None:
            mod_constructions.append(self._air_boundary_construction)
        return mod_constructions

    @property
    def constructions_unique(self):
        """List of all unique constructions contained within the set."""
        return list(set(self.constructions))

    @property
    def modified_constructions_unique(self):
        """List of all unique constructions that are not defaulted within the set."""
        return list(set(self.modified_constructions))

    @property
    def materials_unique(self):
        """List of all unique materials contained within the set."""
        materials = []
        for constr in self.constructions:
            try:
                materials.extend(constr.materials)
            except AttributeError:
                pass  # ShadeConstruction or AirBoundaryConstruction
        return list(set(materials))

    @property
    def modified_materials_unique(self):
        """List of all unique materials that are not defaulted within the set."""
        materials = []
        for constr in self.modified_constructions:
            try:
                materials.extend(constr.materials)
            except AttributeError:
                pass  # ShadeConstruction or AirBoundaryConstruction
        return list(set(materials))

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        if self._user_data is not None:
            return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value    

    def get_face_construction(self, face_type, boundary_condition):
        """Get a construction object that will be assigned to a given type of face.

        Args:
            face_type: Text string for the type of face (eg. 'Wall', 'Floor',
                'Roof', 'AirBoundary').
            boundary_condition: Text string for the boundary condition
                (eg. 'Outdoors', 'Surface', 'Adiabatic', 'Ground')
        """
        if face_type == 'Wall':
            return self._get_constr_from_set(self.wall_set, boundary_condition)
        elif face_type == 'Floor':
            return self._get_constr_from_set(self.floor_set, boundary_condition)
        elif face_type == 'RoofCeiling':
            return self._get_constr_from_set(self.roof_ceiling_set, boundary_condition)
        elif face_type == 'AirBoundary':
            return self.air_boundary_construction
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
            data: Dictionary describing the ConstructionSet with the
                format below.

        .. code-block:: python

            {
            "type": 'ConstructionSet',
            "identifier": str,  # ConstructionSet identifier
            "display_name": str,  # ConstructionSet display name
            "wall_set": {},  # A WallConstructionSet dictionary
            "floor_set": {},  # A FloorConstructionSet dictionary
            "roof_ceiling_set": {},  # A RoofCeilingConstructionSet dictionary
            "aperture_set": {},  # A ApertureConstructionSet dictionary
            "door_set": {},  # A DoorConstructionSet dictionary
            "shade_construction": {},  # ShadeConstruction dictionary
            "air_boundary_construction": {},  # AirBoundaryConstruction dictionary
            }
        """
        assert data['type'] == 'ConstructionSet', \
            'Expected ConstructionSet. Got {}.'.format(data['type'])

        # build each of the sub-construction sets
        wall_set = WallConstructionSet.from_dict(data['wall_set']) if 'wall_set' \
            in data and data['wall_set'] is not None else None
        floor_set = FloorConstructionSet.from_dict(data['floor_set']) if 'floor_set' \
            in data and data['floor_set'] is not None else None
        roof_ceiling_set = \
            RoofCeilingConstructionSet.from_dict(data['roof_ceiling_set']) \
            if 'roof_ceiling_set' in data and data['roof_ceiling_set'] \
            is not None else None
        aperture_set = ApertureConstructionSet.from_dict(data['aperture_set']) if \
            'aperture_set' in data and data['aperture_set'] is not None else None
        door_set = DoorConstructionSet.from_dict(data['door_set']) if \
            'door_set' in data and data['door_set'] is not None else None
        shade_con = ShadeConstruction.from_dict(data['shade_construction']) if \
            'shade_construction' in data and data['shade_construction'] is not None \
            else None
        air_con = None
        if 'air_boundary_construction' in data and \
                data['air_boundary_construction'] is not None:
            if data['air_boundary_construction']['type'] == 'AirBoundaryConstruction':
                air_con = AirBoundaryConstruction.from_dict(
                    data['air_boundary_construction'])
            else:
                air_con = OpaqueConstruction.from_dict(data['air_boundary_construction'])

        new_obj = cls(data['identifier'], wall_set, floor_set, roof_ceiling_set,
                      aperture_set, door_set, shade_con, air_con)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, construction_dict):
        """Create a ConstructionSet from an abridged dictionary.

        Args:
            data: A ConstructionSetAbridged dictionary.
            construction_dict: A dictionary with construction identifiers as keys and
                honeybee construction objects as values. These will be used to
                assign the constructions to the ConstructionSet object.

        .. code-block:: python

            {
            "type": 'ConstructionSetAbridged',
            "identifier": str,  # ConstructionSet identifier
            "display_name": str,  # ConstructionSet display name
            "wall_set": {},  # A WallConstructionSetAbridged dictionary
            "floor_set": {},  # A FloorConstructionSetAbridged dictionary
            "roof_ceiling_set": {},  # A RoofCeilingConstructionSetAbridged dictionary
            "aperture_set": {},  # A ApertureConstructionSetAbridged dictionary
            "door_set": {},  # A DoorConstructionSetAbridged dictionary
            "shade_construction": str,  # ShadeConstruction identifier
            "air_boundary_construction": str  # AirBoundaryConstruction identifier
            }
        """
        assert data['type'] == 'ConstructionSetAbridged', \
            'Expected ConstructionSetAbridged. Got {}.'.format(data['type'])
        try:
            wall_set, floor_set, roof_ceiling_set, aperture_set, door_set, shade_con, \
                air_con = cls._get_subsets_from_abridged(data, construction_dict)
        except KeyError as e:
            raise ValueError(
                'The following construction is missing from the model: {}'.format(e)
            )
        new_obj = cls(data['identifier'], wall_set, floor_set, roof_ceiling_set,
                      aperture_set, door_set, shade_con, air_con)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

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
        base['identifier'] = self.identifier
        base['wall_set'] = self.wall_set.to_dict(abridged, none_for_defaults)
        base['floor_set'] = self.floor_set.to_dict(abridged, none_for_defaults)
        base['roof_ceiling_set'] = \
            self.roof_ceiling_set.to_dict(abridged, none_for_defaults)
        base['aperture_set'] = self.aperture_set.to_dict(abridged, none_for_defaults)
        base['door_set'] = self.door_set.to_dict(abridged, none_for_defaults)
        if none_for_defaults:
            if abridged:
                base['shade_construction'] = self._shade_construction.identifier \
                    if self._shade_construction is not None else None
            else:
                base['shade_construction'] = self._shade_construction.to_dict() \
                    if self._shade_construction is not None else None
        else:
            base['shade_construction'] = self.shade_construction.identifier \
                if abridged else self.shade_construction.to_dict()
        if none_for_defaults:
            if abridged:
                base['air_boundary_construction'] = \
                    self._air_boundary_construction.identifier if \
                    self._air_boundary_construction is not None else None
            else:
                base['air_boundary_construction'] = \
                    self._air_boundary_construction.to_dict() if \
                    self._air_boundary_construction is not None else None
        else:
            base['air_boundary_construction'] = \
                self.air_boundary_construction.identifier \
                if abridged else self.air_boundary_construction.to_dict()

        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def to_radiance_solar_interior(self):
        """Honeybee Radiance modifier set for the interior solar properties."""
        # convert all interior constructions into modifiers
        unique_mods = {}
        for constr in self.constructions_unique:
            unique_mods[constr.identifier] = constr.to_radiance_solar_interior() \
                if isinstance(constr, OpaqueConstruction) else constr.to_radiance_solar()
        return self._create_modifier_set('Solar_Interior', unique_mods)

    def to_radiance_visible_interior(self):
        """Honeybee Radiance modifier set for the interior visible properties."""
        # convert all interior constructions into modifiers
        unique_mods = {}
        for constr in self.constructions_unique:
                unique_mods[constr.identifier] = constr.to_radiance_visible_interior() \
                    if isinstance(constr, OpaqueConstruction) \
                    else constr.to_radiance_visible()
        return self._create_modifier_set('Visible_Interior', unique_mods)

    def to_radiance_solar_exterior(self):
        """Honeybee Radiance modifier set for the exterior solar properties."""
        # convert all exterior constructions into modifiers
        unique_mods = {}
        for constr in self.constructions_unique:
            unique_mods[constr.identifier] = constr.to_radiance_solar_exterior() \
                if isinstance(constr, OpaqueConstruction) else constr.to_radiance_solar()
        return self._create_modifier_set('Solar_Exterior', unique_mods)

    def to_radiance_visible_exterior(self):
        """Honeybee Radiance modifier set for the exterior visible properties."""
        # convert all exterior constructions into modifiers
        unique_mods = {}
        for constr in self.constructions_unique:
            unique_mods[constr.identifier] = constr.to_radiance_visible_exterior() \
                    if isinstance(constr, OpaqueConstruction) \
                    else constr.to_radiance_visible()
        return self._create_modifier_set('Visible_Exterior', unique_mods)

    def duplicate(self):
        """Get a copy of this ConstructionSet."""
        return self.__copy__()

    def lock(self):
        """The lock() method to will also lock the WallConstructionSet, etc."""
        self._locked = True
        self._wall_set.lock()
        self._floor_set.lock()
        self._roof_ceiling_set.lock()
        self._aperture_set.lock()
        self._door_set.lock()

    def unlock(self):
        """The unlock() method will also unlock the WallConstructionSet, etc."""
        self._locked = False
        self._wall_set.unlock()
        self._floor_set.unlock()
        self._roof_ceiling_set.unlock()
        self._aperture_set.unlock()
        self._door_set.unlock()

    def _create_modifier_set(self, mod_type, unique_mods):
        """Create a modifier set from a dictionary of radiance modifiers."""
        # import the radiance dependency
        try:
            from honeybee_radiance.modifierset import ModifierSet
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        # create the modifier set object
        mod_set = ModifierSet(
            '{}_{}'.format(clean_rad_string(self.identifier), mod_type))
        mod_set.wall_set.exterior_modifier = \
            unique_mods[self.wall_set.exterior_construction.identifier]
        mod_set.wall_set.interior_modifier = \
            unique_mods[self.wall_set.interior_construction.identifier]
        mod_set.floor_set.exterior_modifier = \
            unique_mods[self.floor_set.exterior_construction.identifier]
        mod_set.floor_set.interior_modifier = \
            unique_mods[self.floor_set.interior_construction.identifier]
        mod_set.roof_ceiling_set.exterior_modifier = \
            unique_mods[self.roof_ceiling_set.exterior_construction.identifier]
        mod_set.roof_ceiling_set.interior_modifier = \
            unique_mods[self.roof_ceiling_set.interior_construction.identifier]
        mod_set.aperture_set.window_modifier = \
            unique_mods[self.aperture_set.window_construction.identifier]
        mod_set.aperture_set.interior_modifier = \
            unique_mods[self.aperture_set.interior_construction.identifier]
        mod_set.aperture_set.skylight_modifier = \
            unique_mods[self.aperture_set.skylight_construction.identifier]
        mod_set.aperture_set.operable_modifier = \
            unique_mods[self.aperture_set.operable_construction.identifier]
        mod_set.door_set.exterior_modifier = \
            unique_mods[self.door_set.exterior_construction.identifier]
        mod_set.door_set.interior_modifier = \
            unique_mods[self.door_set.interior_construction.identifier]
        mod_set.door_set.exterior_glass_modifier = \
            unique_mods[self.door_set.exterior_glass_construction.identifier]
        mod_set.door_set.interior_glass_modifier = \
            unique_mods[self.door_set.interior_glass_construction.identifier]
        mod_set.door_set.overhead_modifier = \
            unique_mods[self.door_set.overhead_construction.identifier]
        mod_set.shade_set.exterior_modifier = \
            unique_mods[self.shade_construction.identifier]
        mod_set.air_boundary_modifier = \
            unique_mods[self.air_boundary_construction.identifier]
        return mod_set

    def _get_constr_from_set(self, face_type_set, boundary_condition):
        """Get a specific construction from a face_type_set."""
        if boundary_condition == 'Outdoors':
            return face_type_set.exterior_construction
        elif boundary_condition == 'Surface' or boundary_condition == 'Adiabatic':
            return face_type_set.interior_construction
        else:
            return face_type_set.ground_construction

    @staticmethod
    def _get_subsets_from_abridged(data, constructions):
        """Get subset objects from and abridged dictionary."""
        wall_set = ConstructionSet._make_construction_subset(
            data, WallConstructionSet(), 'wall_set', constructions)
        floor_set = ConstructionSet._make_construction_subset(
            data, FloorConstructionSet(), 'floor_set', constructions)
        roof_ceiling_set = ConstructionSet._make_construction_subset(
            data, RoofCeilingConstructionSet(), 'roof_ceiling_set', constructions)
        aperture_set = ConstructionSet._make_aperture_subset(
            data, ApertureConstructionSet(), constructions)
        door_set = ConstructionSet._make_door_subset(
            data, DoorConstructionSet(), constructions)
        if 'shade_construction' in data and data['shade_construction'] is not None:
            shade = constructions[data['shade_construction']]
        else:
            shade = None
        if 'air_boundary_construction' in data and \
                data['air_boundary_construction'] is not None:
            air = constructions[data['air_boundary_construction']]
        else:
            air = None
        return wall_set, floor_set, roof_ceiling_set, aperture_set, door_set, shade, air

    @staticmethod
    def _make_construction_subset(data, sub_set, sub_set_id, constructions):
        """Make a wall set, floor set, or roof ceiling set from dictionary."""
        if sub_set_id in data:
            if 'exterior_construction' in data[sub_set_id] and \
                    data[sub_set_id]['exterior_construction'] is not None:
                sub_set.exterior_construction = \
                    constructions[data[sub_set_id]['exterior_construction']]
            if 'interior_construction' in data[sub_set_id] and \
                    data[sub_set_id]['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[data[sub_set_id]['interior_construction']]
            if 'ground_construction' in data[sub_set_id] and \
                    data[sub_set_id]['ground_construction'] is not None:
                sub_set.ground_construction = \
                    constructions[data[sub_set_id]['ground_construction']]
        return sub_set

    @staticmethod
    def _make_aperture_subset(data, sub_set, constructions):
        """Make an ApertureConstructionSet from a dictionary."""
        if 'aperture_set' in data:
            if 'window_construction' in data['aperture_set'] and \
                    data['aperture_set']['window_construction'] is not None:
                sub_set.window_construction = \
                    constructions[data['aperture_set']['window_construction']]
            if 'interior_construction' in data['aperture_set'] and \
                    data['aperture_set']['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[data['aperture_set']['interior_construction']]
            if 'skylight_construction' in data['aperture_set'] and \
                    data['aperture_set']['skylight_construction'] is not None:
                sub_set.skylight_construction = \
                    constructions[data['aperture_set']['skylight_construction']]
            if 'operable_construction' in data['aperture_set'] and \
                    data['aperture_set']['operable_construction'] is not None:
                sub_set.operable_construction = \
                    constructions[data['aperture_set']['operable_construction']]
        return sub_set

    @staticmethod
    def _make_door_subset(data, sub_set, constructions):
        """Make a DoorConstructionSet from dictionary."""
        if 'door_set' in data:
            if 'exterior_construction' in data['door_set'] and \
                    data['door_set']['exterior_construction'] is not None:
                sub_set.exterior_construction = \
                    constructions[data['door_set']['exterior_construction']]
            if 'interior_construction' in data['door_set'] and \
                    data['door_set']['interior_construction'] is not None:
                sub_set.interior_construction = \
                    constructions[data['door_set']['interior_construction']]
            if 'exterior_glass_construction' in data['door_set'] and \
                    data['door_set']['exterior_glass_construction'] is not None:
                sub_set.exterior_glass_construction = \
                    constructions[data['door_set']['exterior_glass_construction']]
            if 'interior_glass_construction' in data['door_set'] and \
                    data['door_set']['interior_glass_construction'] is not None:
                sub_set.interior_glass_construction = \
                    constructions[data['door_set']['interior_glass_construction']]
            if 'overhead_construction' in data['door_set'] and \
                    data['door_set']['overhead_construction'] is not None:
                sub_set.overhead_construction = \
                    constructions[data['door_set']['overhead_construction']]
        return sub_set

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        new_obj = ConstructionSet(self.identifier,
                                  self.wall_set.duplicate(),
                                  self.floor_set.duplicate(),
                                  self.roof_ceiling_set.duplicate(),
                                  self.aperture_set.duplicate(),
                                  self.door_set.duplicate(),
                                  self._shade_construction,
                                  self._air_boundary_construction)
        new_obj._display_name = self._display_name
        new_obj.user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier,) + tuple(hash(cnstr) for cnstr in self.constructions)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ConstructionSet) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Energy Construction Set: {}'.format(self.display_name)


@lockable
class _FaceSetBase(object):
    """Base class for the sets assigned to Faces.

    This includesWallConstructionSet, FloorConstructionSet, and the
    RoofCeilingConstructionSet.

    Args:
        exterior_construction: An OpaqueConstruction object for faces with an
            Outdoors boundary condition.
        interior_construction: An OpaqueConstruction object for faces with a
            Surface or Adiabatic boundary condition.
        ground_construction: : An OpaqueConstruction object for faces with a
            Ground boundary condition.
    """

    __slots__ = ('_exterior_construction', '_interior_construction',
                 '_ground_construction', '_locked')

    def __init__(self, exterior_construction=None, interior_construction=None,
                 ground_construction=None):
        """Initialize set."""
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

    @classmethod
    def from_dict(cls, data):
        """Create a SubSet from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: Dictionary describing the Set of the object.
        """
        assert data['type'] == cls.__name__, \
            'Expected {}. Got {}.'.format(cls.__name__, data['type'])
        extc = OpaqueConstruction.from_dict(data['exterior_construction']) \
            if 'exterior_construction' in data and data['exterior_construction'] \
            is not None else None
        intc = OpaqueConstruction.from_dict(data['interior_construction']) \
            if 'interior_construction' in data and data['interior_construction'] \
            is not None else None
        gndc = OpaqueConstruction.from_dict(data['ground_construction']) \
            if 'ground_construction' in data and data['ground_construction'] \
            is not None else None
        return cls(extc, intc, gndc)

    def to_dict(self, abridged=False, none_for_defaults=True):
        """Get the Set as a dictionary.

        Args:
            abridged: Boolean noting whether detailed materials and construction
                objects should be written into the ConstructionSet (False) or just
                an abridged version (True). Default: False.
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': self.__class__.__name__ + 'Abridged'} if abridged else \
            {'type': self.__class__.__name__}
        if none_for_defaults:
            if abridged:
                base['exterior_construction'] = self._exterior_construction.identifier \
                    if self._exterior_construction is not None else None
                base['interior_construction'] = self._interior_construction.identifier \
                    if self._interior_construction is not None else None
                base['ground_construction'] = self._ground_construction.identifier \
                    if self._ground_construction is not None else None
            else:
                base['exterior_construction'] = self._exterior_construction.to_dict() \
                    if self._exterior_construction is not None else None
                base['interior_construction'] = self._interior_construction.to_dict() \
                    if self._interior_construction is not None else None
                base['ground_construction'] = self._ground_construction.to_dict() \
                    if self._ground_construction is not None else None
        else:
            base['exterior_construction'] = self.exterior_construction.identifier \
                if abridged else self.exterior_construction.to_dict()
            base['interior_construction'] = self.interior_construction.identifier \
                if abridged else self.exterior_construction.to_dict()
            base['ground_construction'] = self.ground_construction.identifier \
                if abridged else self.exterior_construction.to_dict()
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
        new_obj =  self.__class__(
            self._exterior_construction, self._interior_construction,
            self._ground_construction)
        return(new_obj)

    def __repr__(self):
        return 'Base Face Set'


@lockable
class WallConstructionSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Walls.

    Properties:
        * exterior_construction
        * interior_construction
        * ground_construction
        * constructions
        * modified_constructions
        * is_modified
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
        return 'Wall Construction Set: [Exterior: {}] [Interior: {}]' \
            ' [Ground: {}]'.format(self.exterior_construction.display_name,
                                   self.interior_construction.display_name,
                                   self.ground_construction.display_name)


@lockable
class FloorConstructionSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Floors.

    Properties:
        * exterior_construction
        * interior_construction
        * ground_construction
        * constructions
        * modified_constructions
        * is_modified
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
        return 'Floor Construction Set: [Exterior: {}] [Interior: {}]' \
            ' [Ground: {}]'.format(self.exterior_construction.display_name,
                                   self.interior_construction.display_name,
                                   self.ground_construction.display_name)


@lockable
class RoofCeilingConstructionSet(_FaceSetBase):
    """Set containing all energy constructions needed to for an energy model's Roofs.

    Properties:
        * exterior_construction
        * interior_construction
        * ground_construction
        * constructions
        * modified_constructions
        * is_modified
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
        return 'RoofCeiling Construction Set: [Exterior: {}] [Interior: {}]' \
            ' [Ground: {}]'.format(self.exterior_construction.display_name,
                                   self.interior_construction.display_name,
                                   self.ground_construction.display_name)


@lockable
class ApertureConstructionSet(object):
    """Set containing all constructions needed to for an energy model's Apertures.

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

    Properties:
        * window_construction
        * interior_construction
        * skylight_construction
        * operable_construction
        * constructions
        * modified_constructions
        * is_modified
    """
    __slots__ = ('_window_construction', '_interior_construction',
                 '_skylight_construction', '_operable_construction', '_locked')

    def __init__(self, window_construction=None, interior_construction=None,
                 skylight_construction=None, operable_construction=None):
        """Initialize aperture set."""
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

    @classmethod
    def from_dict(cls, data):
        """Create a ApertureConstructionSet from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: Dictionary describing the Set of the object.
        """
        assert data['type'] == 'ApertureConstructionSet', \
            'Expected ApertureConstructionSet. Got {}.'.format(data['type'])
        winc = dict_to_construction(data['window_construction']) \
            if 'window_construction' in data and data['window_construction'] \
            is not None else None
        intc = dict_to_construction(data['interior_construction']) \
            if 'interior_construction' in data and data['interior_construction'] \
            is not None else None
        skyc = dict_to_construction(data['skylight_construction']) \
            if 'skylight_construction' in data and data['skylight_construction'] \
            is not None else None
        opc = dict_to_construction(data['operable_construction'])\
            if 'operable_construction' in data and data['operable_construction'] \
            is not None else None
        return cls(winc, intc, skyc, opc)

    def to_dict(self, abridged=False, none_for_defaults=True):
        """Get ApertureConstructionSet as a dictionary.

        Args:
            abridged: Boolean noting whether detailed materials and construction
                objects should be written into the ConstructionSet (False) or just
                an abridged version (True). Default: False.
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': 'ApertureConstructionSetAbridged'} if abridged \
            else {'type': 'ApertureConstructionSet'}
        if none_for_defaults:
            if abridged:
                base['window_construction'] = self._window_construction.identifier if \
                    self._window_construction is not None else None
                base['interior_construction'] = \
                    self._interior_construction.identifier if \
                    self._interior_construction is not None else None
                base['skylight_construction'] = \
                    self._skylight_construction.identifier if \
                    self._skylight_construction is not None else None
                base['operable_construction'] = \
                    self._operable_construction.identifier if \
                    self._operable_construction is not None else None
            else:
                base['window_construction'] = self._window_construction.to_dict() \
                    if self._window_construction is not None else None
                base['interior_construction'] = self._interior_construction.to_dict() \
                    if self._interior_construction is not None else None
                base['skylight_construction'] = self._skylight_construction.to_dict() \
                    if self._skylight_construction is not None else None
                base['operable_construction'] = \
                    self._operable_construction.to_dict() if \
                    self._operable_construction is not None else None
        else:
            base['window_construction'] = self.window_construction.identifier if \
                abridged else self.window_construction.to_dict()
            base['interior_construction'] = self.interior_construction.identifier if \
                abridged else self.interior_construction.to_dict()
            base['skylight_construction'] = self.skylight_construction.identifier if \
                abridged else self.skylight_construction.to_dict()
            base['operable_construction'] = self.operable_construction.identifier if \
                abridged else self.operable_construction.to_dict()
        return base

    def duplicate(self):
        """Get a copy of this set."""
        return self.__copy__()

    def _check_window_construction(self, value):
        """Check that a construction is valid before assigning it."""
        val_w = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)
        assert isinstance(value, val_w), \
            'Expected Window Construction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return 4

    def __iter__(self):
        return iter(self.constructions)

    def __copy__(self):
        new_obj =  self.__class__(
                        self._window_construction, self._interior_construction,
                        self._skylight_construction, self._operable_construction)
        return(new_obj)

    def __repr__(self):
        return 'Aperture Construction Set: [Window: {}] [Interior: {}]' \
            ' [Skylight: {}] [Operable: {}]'.format(
                self.window_construction.display_name,
                self.interior_construction.display_name,
                self.skylight_construction.display_name,
                self.operable_construction.display_name)


@lockable
class DoorConstructionSet(object):
    """Set containing all energy constructions needed to for an energy model's Roofs.

    Args:
        exterior_construction: An OpaqueConstruction object for opaque doors with an
            Outdoors boundary condition and a Wall face type for their parent face.
        interior_construction: An OpaqueConstruction object for all opaque doors
            with a Surface boundary condition.
        exterior_glass_construction: A WindowConstruction object for all glass
            doors with an Outdoors boundary condition.
        interior_glass_construction: A WindowConstruction object for all glass
            doors with a Surface boundary condition.
        overhead_construction: An OpaqueConstruction object for opaque doors with
            an Outdoors boundary condition and a RoofCeiling or Floor face type for
            their parent face.

    Properties:
        * exterior_construction
        * interior_construction
        * exterior_glass_construction
        * interior_glass_construction
        * overhead_construction
        * constructions
        * modified_constructions
        * is_modified
    """
    __slots__ = ('_exterior_construction', '_interior_construction',
                 '_exterior_glass_construction', '_interior_glass_construction',
                 '_overhead_construction', '_locked')

    def __init__(self, exterior_construction=None, interior_construction=None,
                 exterior_glass_construction=None, interior_glass_construction=None,
                 overhead_construction=None):
        """Initialize door set."""
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

    @classmethod
    def from_dict(cls, data):
        """Create a DoorConstructionSet from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: Dictionary describing the Set of the object.
        """
        assert data['type'] == 'DoorConstructionSet', \
            'Expected DoorConstructionSet. Got {}.'.format(data['type'])
        extc = OpaqueConstruction.from_dict(data['exterior_construction']) \
            if 'exterior_construction' in data and data['exterior_construction'] \
            is not None else None
        intc = OpaqueConstruction.from_dict(data['interior_construction']) \
            if 'interior_construction' in data and data['interior_construction'] \
            is not None else None
        egc = dict_to_construction(data['exterior_glass_construction']) \
            if 'exterior_glass_construction' in data and \
            data['exterior_glass_construction'] is not None else None
        igc = dict_to_construction(data['interior_glass_construction']) \
            if 'interior_glass_construction' in data and \
            data['interior_glass_construction'] is not None else None
        ohc = OpaqueConstruction.from_dict(data['overhead_construction']) \
            if 'overhead_construction' in data and data['overhead_construction'] \
            is not None else None
    
        return cls(extc, intc, egc, igc, ohc)

    def to_dict(self, abridged=False, none_for_defaults=True):
        """Get the DoorConstructionSet as a dictionary.

        Args:
            abridged: Boolean noting whether detailed materials and construction
                objects should be written into the ConstructionSet (False) or just
                an abridged version (True). Default: False.
            none_for_defaults: Boolean to note whether default constructions in the
                set should be included in detail (False) or should be None (True).
                Default: True.
        """
        base = {'type': 'DoorConstructionSetAbridged'} if abridged \
            else {'type': 'DoorConstructionSet'}
        if none_for_defaults:
            if abridged:
                base['exterior_construction'] = self._exterior_construction.identifier \
                    if self._exterior_construction is not None else None
                base['interior_construction'] = self._interior_construction.identifier \
                    if self._interior_construction is not None else None
                base['exterior_glass_construction'] = \
                    self._exterior_glass_construction.identifier if \
                    self._exterior_glass_construction is not None else None
                base['interior_glass_construction'] = \
                    self._interior_glass_construction.identifier if \
                    self._interior_glass_construction is not None else None
                base['overhead_construction'] = self._overhead_construction.identifier \
                    if self._overhead_construction is not None else None
            else:
                base['exterior_construction'] = self._exterior_construction.to_dict() \
                    if self._exterior_construction is not None else None
                base['interior_construction'] = self._interior_construction.to_dict() \
                    if self._interior_construction is not None else None
                base['exterior_glass_construction'] = \
                    self._exterior_glass_construction.to_dict() \
                    if self._exterior_glass_construction is not None else None
                base['interior_glass_construction'] = \
                    self._interior_glass_construction.to_dict() if \
                    self._interior_glass_construction is not None else None
                base['overhead_construction'] = self._overhead_construction.to_dict() \
                    if self._overhead_construction is not None else None
        else:
            base['exterior_construction'] = self.exterior_construction.identifier if \
                abridged else self.exterior_construction.to_dict()
            base['interior_construction'] = self.interior_construction.identifier if \
                abridged else self.interior_construction.to_dict()
            base['exterior_glass_construction'] = \
                self.exterior_glass_construction.identifier if \
                abridged else self.exterior_glass_construction.to_dict()
            base['interior_glass_construction'] = \
                self.interior_glass_construction.identifier if \
                abridged else self.interior_glass_construction.to_dict()
            base['overhead_construction'] = self.overhead_construction.identifier if \
                abridged else self.overhead_construction.to_dict()
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
        val_w = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)
        assert isinstance(value, val_w), \
            'Expected Window Construction. Got {}'.format(type(value))
        value.lock()   # lock editing in case construction has multiple references

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return 5

    def __iter__(self):
        return iter(self.constructions)

    def __copy__(self):
        new_obj = self.__class__(
            self._exterior_construction, self._interior_construction,
            self._exterior_glass_construction, self._interior_glass_construction,
            self._overhead_construction)
        return(new_obj)
        

    def __repr__(self):
        return 'Door Construction Set: [Exterior: {}] [Interior: {}]' \
            ' [Exterior Glass: {}] [Interior Glass: {}] [Overhead: {}]'.format(
                self.exterior_construction.display_name,
                self.interior_construction.display_name,
                self.exterior_glass_construction.display_name,
                self.interior_glass_construction.display_name,
                self.overhead_construction.display_name)
