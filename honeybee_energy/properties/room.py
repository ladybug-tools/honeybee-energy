# coding=utf-8
"""Room Energy Properties."""
# import the main types of assignable objects
from ..programtype import ProgramType
from ..constructionset import ConstructionSet
from ..load.people import People
from ..load.lighting import Lighting
from ..load.equipment import ElectricEquipment, GasEquipment
from ..load.infiltration import Infiltration
from ..load.ventilation import Ventilation
from ..load.setpoint import Setpoint
from ..ventcool.control import VentilationControl
from ..ventcool.crack import AFNCrack
from ..ventcool.opening import VentilationOpening

# import Honeybee-core modules
from honeybee.boundarycondition import Outdoors, Surface
from honeybee.facetype import Wall, RoofCeiling, Floor
from honeybee.aperture import Aperture

# import all hvac modules to ensure they are all re-serialize-able in Room.from_dict
from ..hvac import HVAC_TYPES_DICT
from ..hvac._base import _HVACSystem
from ..hvac.idealair import IdealAirSystem

# import the libraries of constructionsets and programs
from ..lib.constructionsets import generic_construction_set
from ..lib.programtypes import plenum_program


class RoomEnergyProperties(object):
    """Energy Properties for Honeybee Room.

    Args:
        host: A honeybee_core Room object that hosts these properties.
        program_type: A honeybee ProgramType object to specify all default
            schedules and loads for the Room. If None, the Room will have a Plenum
            program (with no loads or setpoints). Default: None.
        construction_set: A honeybee ConstructionSet object to specify all
            default constructions for the Faces of the Room. If None, the Room
            will use the honeybee default construction set, which is not
            representative of a particular building code or climate zone.
            Default: None.
        hvac: A honeybee HVAC object (such as an IdealAirSystem) that specifies
            how the Room is conditioned. If None, it will be assumed that the
            Room is not conditioned. Default: None.

    Properties:
        * host
        * program_type
        * construction_set
        * hvac
        * people
        * lighting
        * electric_equipment
        * gas_equipment
        * infiltration
        * ventilation
        * setpoint
        * window_vent_control
        * is_conditioned
    """

    __slots__ = ('_host', '_program_type', '_construction_set', '_hvac',
                 '_people', '_lighting', '_electric_equipment', '_gas_equipment',
                 '_infiltration', '_ventilation', '_setpoint', '_window_vent_control')

    def __init__(self, host, program_type=None, construction_set=None, hvac=None):
        """Initialize Room energy properties."""
        # set the main properties of the Room
        self._host = host
        self.program_type = program_type
        self.construction_set = construction_set
        self.hvac = hvac

        # set the Room's specific properties that override the program_type to None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None
        self._window_vent_control = None

    @property
    def host(self):
        """Get the Room object hosting these properties."""
        return self._host

    @property
    def program_type(self):
        """Get or set the ProgramType object for the Room.

        If not set, it will default to a plenum ProgramType (with no loads assigned).
        """
        if self._program_type is not None:  # set by the user
            return self._program_type
        else:
            return plenum_program

    @program_type.setter
    def program_type(self, value):
        if value is not None:
            assert isinstance(value, ProgramType), \
                'Expected ProgramType for Room program_type. Got {}'.format(type(value))
            value.lock()   # lock in case program type has multiple references
        self._program_type = value

    @property
    def construction_set(self):
        """Get or set the Room ConstructionSet object.

        If not set, it will be the Honeybee default generic ConstructionSet.
        """
        if self._construction_set is not None:  # set by the user
            return self._construction_set
        else:
            return generic_construction_set

    @construction_set.setter
    def construction_set(self, value):
        if value is not None:
            assert isinstance(value, ConstructionSet), \
                'Expected ConstructionSet. Got {}'.format(type(value))
            value.lock()   # lock in case construction set has multiple references
        self._construction_set = value

    @property
    def hvac(self):
        """Get or set the HVAC object for the Room.

        If None, it will be assumed that the Room is not conditioned.
        """
        return self._hvac

    @hvac.setter
    def hvac(self, value):
        if value is not None:
            assert isinstance(value, _HVACSystem), \
                'Expected HVACSystem for Room hvac. Got {}'.format(type(value))
            if value.is_single_room:
                if value._parent is None:
                    value._parent = self.host
                elif value._parent.identifier != self.host.identifier:
                    raise ValueError(
                        '{0} objects can be assigned to a only one Room.\n'
                        '{0} "{1}" cannot be assigned to Room "{2}" since it is '
                        'already assigned to "{3}".\nTry duplicating the {0}, '
                        'and then assigning it to this Room.'.format(
                            value.__class__.__name__, value.identifier,
                            self.host.identifier, value._parent.identifier))
            value.lock()   # lock in case hvac has multiple references
        self._hvac = value

    @property
    def people(self):
        """Get or set a People object to describe the occupancy of the Room."""
        if self._people is not None:  # set by the user
            return self._people
        else:
            return self.program_type.people

    @people.setter
    def people(self, value):
        if value is not None:
            assert isinstance(value, People), \
                'Expected People for Room people. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._people = value

    @property
    def lighting(self):
        """Get or set a Lighting object to describe the lighting usage of the Room."""
        if self._lighting is not None:  # set by the user
            return self._lighting
        else:
            return self.program_type.lighting

    @lighting.setter
    def lighting(self, value):
        if value is not None:
            assert isinstance(value, Lighting), \
                'Expected Lighting for Room lighting. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._lighting = value

    @property
    def electric_equipment(self):
        """Get or set an ElectricEquipment object to describe the equipment usage."""
        if self._electric_equipment is not None:  # set by the user
            return self._electric_equipment
        else:
            return self.program_type.electric_equipment

    @electric_equipment.setter
    def electric_equipment(self, value):
        if value is not None:
            assert isinstance(value, ElectricEquipment), 'Expected ElectricEquipment ' \
                'for Room electric_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._electric_equipment = value

    @property
    def gas_equipment(self):
        """Get or set a GasEquipment object to describe the equipment usage."""
        if self._gas_equipment is not None:  # set by the user
            return self._gas_equipment
        else:
            return self.program_type.gas_equipment

    @gas_equipment.setter
    def gas_equipment(self, value):
        if value is not None:
            assert isinstance(value, GasEquipment), 'Expected GasEquipment ' \
                'for Room gas_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._gas_equipment = value

    @property
    def infiltration(self):
        """Get or set a Infiltration object to to describe the outdoor air leakage."""
        if self._infiltration is not None:  # set by the user
            return self._infiltration
        else:
            return self.program_type.infiltration

    @infiltration.setter
    def infiltration(self, value):
        if value is not None:
            assert isinstance(value, Infiltration), 'Expected Infiltration ' \
                'for Room infiltration. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._infiltration = value

    @property
    def ventilation(self):
        """Get or set a Ventilation object for the minimum outdoor air requirement."""
        if self._ventilation is not None:  # set by the user
            return self._ventilation
        else:
            return self.program_type.ventilation

    @ventilation.setter
    def ventilation(self, value):
        if value is not None:
            assert isinstance(value, Ventilation), 'Expected Ventilation ' \
                'for Room ventilation. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._ventilation = value

    @property
    def setpoint(self):
        """Get or set a Setpoint object for the temperature setpoints of the Room."""
        if self._setpoint is not None:  # set by the user
            return self._setpoint
        else:
            return self.program_type.setpoint

    @setpoint.setter
    def setpoint(self, value):
        if value is not None:
            assert isinstance(value, Setpoint), 'Expected Setpoint ' \
                'for Room setpoint. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._setpoint = value

    @property
    def window_vent_control(self):
        """Get or set a VentilationControl object to dictate the opening of windows.

        If None, the windows will never open.
        """
        return self._window_vent_control

    @window_vent_control.setter
    def window_vent_control(self, value):
        if value is not None:
            assert isinstance(value, VentilationControl), 'Expected VentilationControl ' \
                'object for Room window_vent_control. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._window_vent_control = value

    @property
    def is_conditioned(self):
        """Boolean to note whether the Room is conditioned."""
        return self._hvac is not None

    def envelope_components_by_type(self):
        """Group the room envelope by boundary condition and type for the AirflowNetwork.

        The surface groups created by this function correspond to the structure of the
        crack template data used to generate the AirflowNetwork.

        Return:
            A tuple with five groups of exterior envelope types

            -   ext_walls - A list of exterior Wall type Face objects.

            -   ext_roofs - A list of exterior RoofCeiling type Face objects.

            -   ext_floors - A list of exterior Floor type Face objects, like you
                would find in a cantilevered Room.

            -   ext_apertures - A list of exterior Aperture Face objects.

            -   ext_doors - A list of exterior Door Face objects.

            A tuple with four groups of interior faces types

            - int_walls: List of interior Wall type Face objects.

            - int_floorceilings: List of interior RoofCeiling and Floor type Face
              objects.

            - int_apertures: List of interior Aperture Face objects.

            - int_doors: List of interior Door Face objects.
        """
        ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors = [], [], [], [], []
        int_walls, int_floorceilings, int_apertures, int_doors = [], [], [], []

        for face in self.host.faces:
            if isinstance(face.boundary_condition, Outdoors):
                if isinstance(face.type, Wall):
                    ext_walls.append(face)
                    ext_apertures.extend(face.apertures)
                    ext_doors.extend(face.doors)
                elif isinstance(face.type, RoofCeiling):
                    ext_roofs.append(face)
                    ext_apertures.extend(face.apertures)  # exterior skylights
                elif isinstance(face.type, Floor):
                    ext_floors.append(face)
            elif isinstance(face.boundary_condition, Surface):
                if isinstance(face.type, Wall):
                    int_walls.append(face)
                    int_apertures.extend(face.apertures)
                    int_doors.extend(face.doors)
                elif isinstance(face.type, RoofCeiling) or isinstance(face.type, Floor):
                    int_floorceilings.append(face)
                    int_apertures.extend(face.apertures)  # interior skylights

        ext_faces = (ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors)
        int_faces = (int_walls, int_floorceilings, int_apertures, int_doors)

        return ext_faces, int_faces

    @staticmethod
    def solve_norm_area_flow_coefficient(flow_per_exterior_area, flow_exponent=0.65,
                                         air_density=1.2041, delta_pressure=4):
        """Mass flow coefficient in kg/(m2 s P^n) for exposed surface area from infiltration.

        Note that this coefficient is normalized per unit area. The EnergyPlus
        AirflowNetwork requires an unnormalized value, and thus this value needs to be
        multiplied by its corresponding exposed surface area. The normalized area air
        mass flow coefficient is derived from a zone's infiltration flow rate using the
        following formula::

            Qva * d = Cqa * dP^n

            where:
                Cqa: Air mass flow coefficient per unit meter at 1 Pa [kg/m2/s/P^n]
                Qva: Volumetric air flow rate per area [m3/s/m2]
                d: Air density [kg/m3]
                dP: Change in pressure across building envelope [Pa]
                n: Air mass flow exponent [-]

        Rearranged to solve for ``Cqa`` ::

            Cqa = Qv * d / dP^n

        Args:
            flow_per_exterior_area: A numerical value for the intensity of infiltration
                in m3/s per square meter of exterior surface area.
            air_density: Air density in kg/m3. (Default: 1.2041 represents
                air density at a temperature of 20 C and 101325 Pa).
            flow_exponent: A numerical value for the air mass flow exponent.
                (Default: 0.65).
            delta_pressure: Reference building air pressure in Pascals. (Default: 4).
                represents typical building pressures.

        Returns:
            Air mass flow coefficient per unit meter at 1 Pa [kg/m2/s/P^n]
        """
        qva = flow_per_exterior_area
        n = flow_exponent
        d = air_density
        dp = delta_pressure

        return qva * d / (dp ** n)

    @staticmethod
    def solve_norm_perimeter_flow_coefficient(norm_area_flow_coefficient, face_area,
                                              face_perimeter):

        """Mass flow coefficient in kg/(s m P^n) for exposed opening edges from infiltration.

        This parameter is used to derive air flow for the four cracks around the
        perimeter of a closed window or door: one along the bottom, one along the top,
        and one on each side. Since this value is derived from the infiltration flow
        rate per exterior area, which represents an average over many types of air
        leakage rates, this value is not intended to be representative of actual opening
        edges flow coefficients. Note that, unlike the surface area flow_coefficient,
        this coefficient is normalized per unit length, which is the required input unit
        the EnergyPlus AirflowNetwork, whereas the flow coefficient for surface cracks is
        not normalized. The normalized perimeter air mass flow coefficient is derived
        from its infiltration flow rate using the following formula::

            Qv * d * A = Cql * L * dP^n

            where:
                Cql: Air mass flow coefficient per unit length at 1 Pa [kg/m/s/P^n]
                Qv: Volumetric air flow rate per length [m3/s/m]
                d: Air density [kg/m3]
                A: Surface area of opening [m2]
                L: Surface perimeter of opening [m]
                dP: Change in pressure across building envelope [Pa]
                n: Air mass flow exponent [-]

        Since ``Qv * d / dP^n`` equals ``Cqa`` the normalized area flow coefficient,
        this can be simplified and rearranged to solve for ``Cql`` with the following
        formula::

            Cql = Cqa * A / L

        Args:
            norm_area_flow_coefficient: Air mass flow coefficient per unit meter at
                1 Pa [kg/m2/s/P^n]
            face_area: A numerical value for the total exterior area in m2.
            face_perimeter: A numerical value for the total exterior perimeter in meters.

        Returns:
            Air mass flow coefficient per unit length at 1 Pa [kg/m/s/P^n]
        """
        cqa = norm_area_flow_coefficient
        a = face_area
        ln = face_perimeter

        return cqa * a / ln

    def exterior_afn_from_infiltration_load(self, exterior_face_groups,
                                            air_density=1.2041):
        """Calculate exterior AirflowNetwork parameters from the room infiltration rate.

        This will compute air leakage parameters for exterior cracks and opening edges
        that produce a total air flow rate equivalent to the room infiltration rate, at
        an envelope pressure difference of 4 Pa. However, the individual flow air
        leakage parameters are not meant to be representative of real values, since the
        infiltration flow rate is an average of the actual, variable surface flow
        dynamics.

        VentilationOpening objects will be added to Aperture and Door objects if not
        already defined, with the fraction_area_operable set to 0. If already defined,
        only the parameters defining leakage when the openings are closed will be
        overwritten. AFNCrack objects will be added to all external and internal Face
        objects, and any existing AFNCrack objects will be overwritten.

        Args:
            exterior_face_groups: A tuple with five types of the exterior room envelope

                -   ext_walls - A list of exterior Wall type Face objects.

                -   ext_roofs - A list of exterior RoofCeiling type Face objects.

                -   ext_floors - A list of exterior Floor type Face objects, like you
                    would find in a cantilevered Room.

                -   ext_apertures - A list of exterior Aperture Face objects.

                -   ext_doors - A list of exterior Door Face objects.

            air_density: Air density in kg/m3. (Default: 1.2041 represents
                air density at a temperature of 20 C and 101325 Pa).
        """

        # simplify parameters
        ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors = exterior_face_groups
        ext_faces = ext_walls + ext_roofs + ext_floors
        ext_openings = ext_apertures + ext_doors
        infil_flow = self.infiltration.flow_per_exterior_area

        # derive normalized flow coefficient
        flow_cof_area = self.solve_norm_area_flow_coefficient(
            infil_flow, air_density=air_density)

        # add exterior crack leakage components
        for ext_face in ext_faces:
            opening_area = sum([aper.area for aper in ext_face.apertures])
            opening_area += sum([door.area for door in ext_face.doors])
            flow_cof = flow_cof_area * (ext_face.area - opening_area)
            ext_face.properties.energy.vent_crack = AFNCrack(flow_cof)

        # add exterior opening leakage components
        for ext_opening in ext_openings:
            if ext_opening.properties.energy.vent_opening is None:
                if isinstance(ext_opening, Aperture):
                    ext_opening.is_operable = True
                ext_opening.properties.energy.vent_opening = \
                    VentilationOpening(fraction_area_operable=0)
            vent_opening = ext_opening.properties.energy.vent_opening
            ext_flow_cof_perimeter = self.solve_norm_perimeter_flow_coefficient(
                flow_cof_area, ext_opening.area, ext_opening.perimeter)
            vent_opening.flow_coefficient_closed = ext_flow_cof_perimeter

    def add_default_ideal_air(self):
        """Add a default IdealAirSystem to this Room.

        The identifier of this system will be derived from the room identifier.
        """
        self.hvac = IdealAirSystem('{}_IdealAir'.format(self.host.identifier))

    def assign_ventilation_opening(self, vent_opening):
        """Assign a VentilationOpening object to all operable Apertures on this Room.

        This method will handle the duplication of the VentilationOpening object to
        ensure that each aperture gets a unique object that can export the correct
        area and height properties of its parent.

        Args:
            vent_opening: A VentilationOpening object to be duplicated and assigned
                to all of the operable apertures of the Room.

        Returns:
            A list of Apertures for which ventilation opening properties were set.
            This can be used to perform additional operations on the apertures, such
            as changing their construction.
        """
        operable_aps = []
        for face in self.host.faces:
            for ap in face.apertures:
                if ap.is_operable:
                    ap.properties.energy.vent_opening = vent_opening.duplicate()
                    operable_aps.append(ap)
        return operable_aps

    def add_prefix(self, prefix):
        """Change the identifier attributes unique to this object by adding a prefix.

        Notably, this method only adds the prefix to extension attributes that must
        be unique to the Room (eg. single-room HVAC systems) and does not add the
        prefix to attributes that are shared across several Rooms (eg. ConstructionSets).

        Args:
            prefix: Text that will be inserted at the start of extension
                attribute identifiers.
        """
        if self._hvac is not None and self._hvac.is_single_room:
            new_hvac = self._hvac.duplicate()
            new_hvac.identifier = '{}_{}'.format(prefix, self._hvac.identifier)
            self.hvac = new_hvac

    def reset_to_default(self):
        """Reset all of the properties assigned at the level of this Room to the default.
        """
        self._program_type = None
        self._construction_set = None
        self._hvac = None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None
        self._window_vent_control = None

    @classmethod
    def from_dict(cls, data, host):
        """Create RoomEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of RoomEnergyProperties with the
                format below.
            host: A Room object that hosts these properties.

        .. code-block:: python

            {
            "type": 'RoomEnergyProperties',
            "construction_set": {},  # A ConstructionSet dictionary
            "program_type": {},  # A ProgramType dictionary
            "hvac": {}, # A HVACSystem dictionary
            "people":{},  # A People dictionary
            "lighting": {},  # A Lighting dictionary
            "electric_equipment": {},  # A ElectricEquipment dictionary
            "gas_equipment": {},  # A GasEquipment dictionary
            "infiltration": {},  # A Infiltration dictionary
            "ventilation": {},  # A Ventilation dictionary
            "setpoint": {}  # A Setpoint dictionary
            "window_vent_control": {}  # A VentilationControl dictionary
            }
        """
        assert data['type'] == 'RoomEnergyProperties', \
            'Expected RoomEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction_set' in data and data['construction_set'] is not None:
            new_prop.construction_set = \
                ConstructionSet.from_dict(data['construction_set'])
        if 'program_type' in data and data['program_type'] is not None:
            new_prop.program_type = ProgramType.from_dict(data['program_type'])
        if 'hvac' in data and data['hvac'] is not None:
            hvac_class = HVAC_TYPES_DICT[data['hvac']['type']]
            new_prop.hvac = hvac_class.from_dict(data['hvac'])

        if 'people' in data and data['people'] is not None:
            new_prop.people = People.from_dict(data['people'])
        if 'lighting' in data and data['lighting'] is not None:
            new_prop.lighting = Lighting.from_dict(data['lighting'])
        if 'electric_equipment' in data and data['electric_equipment'] is not None:
            new_prop.electric_equipment = \
                ElectricEquipment.from_dict(data['electric_equipment'])
        if 'gas_equipment' in data and data['gas_equipment'] is not None:
            new_prop.gas_equipment = GasEquipment.from_dict(data['gas_equipment'])
        if 'infiltration' in data and data['infiltration'] is not None:
            new_prop.infiltration = Infiltration.from_dict(data['infiltration'])
        if 'ventilation' in data and data['ventilation'] is not None:
            new_prop.ventilation = Ventilation.from_dict(data['ventilation'])
        if 'setpoint' in data and data['setpoint'] is not None:
            new_prop.setpoint = Setpoint.from_dict(data['setpoint'])
        if 'window_vent_control' in data and data['window_vent_control'] is not None:
            new_prop.window_vent_control = \
                VentilationControl.from_dict(data['window_vent_control'])

        return new_prop

    def apply_properties_from_dict(self, abridged_data, construction_sets,
                                   program_types, hvacs, schedules):
        """Apply properties from a RoomEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A RoomEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            construction_sets: A dictionary of ConstructionSets with identifiers
                of the sets as keys, which will be used to re-assign construction_sets.
            program_types: A dictionary of ProgramTypes with identifiers of the types as
                keys, which will be used to re-assign program_types.
            hvacs: A dictionary of HVACSystems with the identifiers of the systems as
                keys, which will be used to re-assign hvac to the Room.
            schedules: A dictionary of Schedules with identifiers of the schedules ask
                keys, which will be used to re-assign schedules.
        """
        if 'construction_set' in abridged_data and \
                abridged_data['construction_set'] is not None:
            self.construction_set = construction_sets[abridged_data['construction_set']]
        if 'program_type' in abridged_data and abridged_data['program_type'] is not None:
            self.program_type = program_types[abridged_data['program_type']]
        if 'hvac' in abridged_data and abridged_data['hvac'] is not None:
            self.hvac = hvacs[abridged_data['hvac']]

        if 'people' in abridged_data and abridged_data['people'] is not None:
            self.people = People.from_dict_abridged(
                abridged_data['people'], schedules)
        if 'lighting' in abridged_data and abridged_data['lighting'] is not None:
            self.lighting = Lighting.from_dict_abridged(
                abridged_data['lighting'], schedules)
        if 'electric_equipment' in abridged_data and \
                abridged_data['electric_equipment'] is not None:
            self.electric_equipment = ElectricEquipment.from_dict_abridged(
                abridged_data['electric_equipment'], schedules)
        if 'gas_equipment' in abridged_data and \
                abridged_data['gas_equipment'] is not None:
            self.gas_equipment = GasEquipment.from_dict_abridged(
                abridged_data['gas_equipment'], schedules)
        if 'infiltration' in abridged_data and abridged_data['infiltration'] is not None:
            self.infiltration = Infiltration.from_dict_abridged(
                abridged_data['infiltration'], schedules)
        if 'ventilation' in abridged_data and abridged_data['ventilation'] is not None:
            self.ventilation = Ventilation.from_dict_abridged(
                abridged_data['ventilation'], schedules)
        if 'setpoint' in abridged_data and abridged_data['setpoint'] is not None:
            self.setpoint = Setpoint.from_dict_abridged(
                abridged_data['setpoint'], schedules)
        if 'window_vent_control' in abridged_data and \
                abridged_data['window_vent_control'] is not None:
            self.window_vent_control = VentilationControl.from_dict_abridged(
                abridged_data['window_vent_control'], schedules)

    def to_dict(self, abridged=False):
        """Return Room energy properties as a dictionary.

        Args:
            abridged: Boolean for whether the full dictionary of the Room should
                be written (False) or just the identifier of the the individual
                properties (True). Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'RoomEnergyProperties' if not \
            abridged else 'RoomEnergyPropertiesAbridged'

        # write the ProgramType into the dictionary
        if self._program_type is not None:
            base['energy']['program_type'] = \
                self._program_type.identifier if abridged else \
                self._program_type.to_dict()

        # write the ConstructionSet into the dictionary
        if self._construction_set is not None:
            base['energy']['construction_set'] = \
                self._construction_set.identifier if abridged else \
                self._construction_set.to_dict()

        # write the hvac into the dictionary
        if self._hvac is not None:
            base['energy']['hvac'] = \
                self._hvac.identifier if abridged else self._hvac.to_dict()

        # write any room-specific overriding properties into the dictionary
        if self._people is not None:
            base['energy']['people'] = self._people.to_dict(abridged)
        if self._lighting is not None:
            base['energy']['lighting'] = self._lighting.to_dict(abridged)
        if self._electric_equipment is not None:
            base['energy']['electric_equipment'] = \
                self._electric_equipment.to_dict(abridged)
        if self._gas_equipment is not None:
            base['energy']['gas_equipment'] = self._gas_equipment.to_dict(abridged)
        if self._infiltration is not None:
            base['energy']['infiltration'] = self._infiltration.to_dict(abridged)
        if self._ventilation is not None:
            base['energy']['ventilation'] = self._ventilation.to_dict(abridged)
        if self._setpoint is not None:
            base['energy']['setpoint'] = self._setpoint.to_dict(abridged)
        if self._window_vent_control is not None:
            base['energy']['window_vent_control'] = \
                self._window_vent_control.to_dict(abridged)

        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Room object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        new_room = RoomEnergyProperties(
            _host, self._program_type, self._construction_set, self._hvac)
        if self._hvac is not None and self._hvac.is_single_room:
            new_room.hvac = self.hvac.duplicate()  # reassign parent to new host
        new_room._people = self._people
        new_room._lighting = self._lighting
        new_room._electric_equipment = self._electric_equipment
        new_room._gas_equipment = self._gas_equipment
        new_room._infiltration = self._infiltration
        new_room._ventilation = self._ventilation
        new_room._setpoint = self._setpoint
        new_room._window_vent_control = self._window_vent_control
        return new_room

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Room Energy Properties:\n host: {}'.format(self.host.identifier)
