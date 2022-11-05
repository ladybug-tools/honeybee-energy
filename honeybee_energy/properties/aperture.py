# coding=utf-8
"""Aperture Energy Properties."""
from honeybee.units import conversion_factor_to_meters
from honeybee.checkdup import is_equivalent

from ..construction.dictutil import dict_to_construction
from ..material.glazing import EnergyWindowMaterialSimpleGlazSys
from ..construction.window import WindowConstruction
from ..construction.windowshade import WindowConstructionShade
from ..construction.dynamic import WindowConstructionDynamic
from ..ventcool.opening import VentilationOpening
from ..lib.constructionsets import generic_construction_set


class ApertureEnergyProperties(object):
    """Energy Properties for Honeybee Aperture.

    Args:
        host: A honeybee_core Aperture object that hosts these properties.
        construction: An optional Honeybee WindowConstruction, WindowConstructionShade
            or WindowConstructionDynamic object for the aperture. If None, it will
            be set by the parent Room ConstructionSet or the the Honeybee default
            generic ConstructionSet.
        vent_opening: An optional VentilationOpening to specify the operable
            portion of the Aperture. (Default: None).

    Properties:
        * host
        * construction
        * vent_opening
        * is_construction_set_on_object
    """

    __slots__ = ('_host', '_construction', '_vent_opening')

    def __init__(self, host, construction=None, vent_opening=None):
        """Initialize Aperture energy properties."""
        self._host = host
        self.construction = construction
        self.vent_opening = vent_opening

    @property
    def host(self):
        """Get the Aperture object hosting these properties."""
        return self._host

    @property
    def construction(self):
        """Get or set Aperture Construction.

        If the Construction is not set on the aperture-level, then it will be assigned
        based on the ConstructionSet assigned to the parent Room.  If there is no
        parent Room or the parent Room's ConstructionSet has no construction for
        the aperture, it will be assigned using the honeybee default generic
        construction set.
        """
        if self._construction:  # set by user
            return self._construction
        elif self._host.has_parent and self._host.parent.has_parent:  # set by zone
            constr_set = self._host.parent.parent.properties.energy.construction_set
            return constr_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable,
                self._host.parent.type.name)
        elif self._host.has_parent:  # generic but influenced by parent face
            return generic_construction_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable,
                self._host.parent.type.name)
        else:
            return generic_construction_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable, 'Wall')

    @construction.setter
    def construction(self, value):
        if value is not None:
            vw = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)
            assert isinstance(value, vw), 'Expected WindowConstruction, ' \
                'WindowConstructionShade or WindowConstructionDynamic for aperture.' \
                ' Got {}'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def vent_opening(self):
        """Get or set a VentilationOpening object to specify the operable portion."""
        return self._vent_opening

    @vent_opening.setter
    def vent_opening(self, value):
        if value is not None:
            assert isinstance(value, VentilationOpening), 'Expected Ventilation' \
                'Opening for Aperture vent_opening. Got {}'.format(type(value))
            assert self.host.is_operable, 'Aperture must have a "True" is_operable ' \
                'property in order to assign vent_opening energy properties.'
            if value._parent is None:
                value._parent = self.host
            elif value._parent.identifier != self.host.identifier:
                raise ValueError(
                    '{0} objects can be assigned to only one parent.\n{0} cannot be '
                    'assigned to Aperture "{1}" since it is already assigned to "{2}".\n'
                    'Try duplicating the object and then assign it.'.format(
                        'VentilationOpening', self.host.identifier,
                        value._parent.identifier))
        self._vent_opening = value

    @property
    def is_construction_set_on_object(self):
        """Boolean noting if construction is assigned on the level of this Aperture.

        This is opposed to having the construction assigned by a ConstructionSet.
        """
        return self._construction is not None

    def r_factor(self, units='Meters'):
        """Get the Aperture R-factor [m2-K/W] (including resistances for air films).

        The air film resistances are computed using the orientation and height
        of the Aperture geometry. If the window construction has a frame, the
        geometry of the frame will also be accounted for.

        Args:
            units: Text for the units in which the Aperture geometry exists. These
                will be used to correctly interpret the dimensions of the
                geometry for heat flow calculation. (Default: Meters).
        """
        # compute the center-of-glass R-value
        u_conv = conversion_factor_to_meters(units)
        win_con = self._window_construction()
        height = (self.host.max.z - self.host.min.z) * u_conv
        height = 1 if height < 1 else height
        _, r_vals = win_con.temperature_profile(
            height=height, angle=abs(self.host.altitude - 90))
        if not win_con.has_frame:
            return sum(r_vals)
        # if there is a frame, account for it in the final R-value
        glass_u = (1 / sum(r_vals))
        glass_area = (self.host.area * (u_conv ** 2))
        if win_con.frame.edge_to_center_ratio != 1 and not \
                isinstance(win_con.materials[0], EnergyWindowMaterialSimpleGlazSys):
            edge_u = win_con.frame.edge_to_center_ratio * glass_u
            edge_area = self.host.perimeter * u_conv * 0.06
            cog_area = glass_area - edge_area
            cog_area = 0 if cog_area < 0 else cog_area
            total_area = cog_area + edge_area
            glass_u = ((glass_u * cog_area) + (edge_u * edge_area)) / total_area
        _, fr_r_vals = win_con.temperature_profile_frame(
            angle=abs(self.host.altitude - 90))
        frame_u = 1 / sum(fr_r_vals)
        frame_area = (self.host.perimeter * u_conv * win_con.frame.width) + \
            ((win_con.frame.width * u_conv) ** 2) * len(self.host.geometry)
        assembly_area = glass_area + frame_area
        total_u = ((glass_u * glass_area) + (frame_u * frame_area)) / assembly_area
        return 1 / total_u

    def u_factor(self, units='Meters'):
        """Get the Aperture U-factor [W/m2-K] (including resistances for air films).

        The air film resistances are computed using the orientation and height
        of the Aperture geometry. If the window construction has a frame, the
        geometry of the frame will also be accounted for.

        Args:
            units: Text for the units in which the Aperture geometry exists. These
                will be used to correctly interpret the dimensions of the
                geometry for heat flow calculation. (Default: Meters).
        """
        return 1 / self.r_factor(units)

    def shgc(self, units='Meters'):
        """Get the Aperture solar heat gain coefficient (SHGC).

        If this construction is not a simple glazing system, this value is computed
        by summing the transmitted and conducted portions of solar irradiance under
        the NFRC summer conditions. The air film resistances are computed using
        the orientation and height of the Aperture geometry. If the window
        construction has a frame, the geometry of the frame will also be accounted for.

        Args:
            units: Text for the units in which the Aperture geometry exists. These
                will be used to correctly interpret the dimensions of the
                geometry for heat flow calculation. (Default: Meters).
        """
        win_con = self._window_construction()
        if isinstance(win_con.materials[0], EnergyWindowMaterialSimpleGlazSys):
            if not win_con.has_frame:
                return win_con.materials[0].shgc
        # compute the temperature profile
        t_out, t_in, sol_irr = 32, 24, 783  # NFRC 2010 summer conditions
        u_conv = conversion_factor_to_meters(units)
        height = (self.host.max.z - self.host.min.z) * u_conv
        height = 1 if height < 1 else height
        _, r_vals = win_con.temperature_profile(
            t_out, t_in, height=height, angle=abs(self.host.altitude - 90),
            solar_irradiance=sol_irr)
        heat_gen, transmitted = win_con._heat_gen_from_solar(sol_irr)
        conducted = 0
        r_factor = sum(r_vals)
        for i, heat_g in enumerate(heat_gen):
            if heat_g != 0:
                conducted += heat_g * (1 - (sum(r_vals[i + 1:]) / r_factor))
        if not win_con.has_frame:
            return (transmitted + conducted) / sol_irr
        else:  # account for the frame conduction
            _, r_values = win_con.temperature_profile_frame(
                t_out, t_in, height=height, angle=abs(self.host.altitude - 90),
                solar_irradiance=sol_irr)
            heat_gen = [0, sol_irr * win_con.frame.solar_absorptance, 0]
            frame_conducted = 0
            r_factor = sum(r_values)
            for i, heat_g in enumerate(heat_gen):
                if heat_g != 0:
                    frame_conducted += heat_g * (1 - (sum(r_values[i + 1:]) / r_factor))
            glass_area = (self.host.area * (u_conv ** 2))
            frame_area = (self.host.perimeter * u_conv * win_con.frame.width) + \
                ((win_con.frame.width * u_conv) ** 2) * len(self.host.geometry)
            glass_trans = transmitted * glass_area
            glass_conduct = conducted * glass_area
            frame_conduct = frame_conducted * frame_area
            total_irr = sol_irr * (glass_area + frame_area)
            return (glass_trans + glass_conduct + frame_conduct) / total_irr

    def reset_to_default(self):
        """Reset a construction assigned at the level of this Aperture to the default.

        This means the Aperture's construction will be assigned by a ConstructionSet.
        """
        self._construction = None
        self._vent_opening = None

    @classmethod
    def from_dict(cls, data, host):
        """Create ApertureEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of ApertureEnergyProperties in the
                format below.
            host: A Aperture object that hosts these properties.

        .. code-block:: python

            {
            "type": 'ApertureEnergyProperties',
            "construction": {},  # Window Construction dictionary
            "vent_opening": {}  # VentilationOpening dict
            }
        """
        assert data['type'] == 'ApertureEnergyProperties', \
            'Expected ApertureEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction' in data and data['construction'] is not None:
            new_prop.construction = dict_to_construction(data['construction'])
        if 'vent_opening' in data and data['vent_opening'] is not None:
            new_prop.vent_opening = VentilationOpening.from_dict(data['vent_opening'])
        return new_prop

    def apply_properties_from_dict(self, abridged_data, constructions):
        """Apply properties from a ApertureEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A ApertureEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            constructions: A dictionary of constructions with constructions identifiers
                as keys, which will be used to re-assign constructions.
        """
        if 'construction' in abridged_data and abridged_data['construction'] is not None:
            try:
                self.construction = constructions[abridged_data['construction']]
            except KeyError:
                raise ValueError('Aperture construction "{}" was not found in '
                                 'constructions.'.format(abridged_data['construction']))
        if 'vent_opening' in abridged_data and abridged_data['vent_opening'] is not None:
            self.vent_opening = \
                VentilationOpening.from_dict(abridged_data['vent_opening'])

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'ApertureEnergyProperties' if not \
            abridged else 'ApertureEnergyPropertiesAbridged'
        if self._construction is not None:
            base['energy']['construction'] = \
                self._construction.identifier if abridged else \
                self._construction.to_dict()
        if self._vent_opening is not None:
            base['energy']['vent_opening'] = self._vent_opening.to_dict()
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Aperture object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        vo = self._vent_opening.duplicate() if self._vent_opening is not None else None
        return ApertureEnergyProperties(_host, self._construction, vo)

    def is_equivalent(self, other):
        """Check to see if these energy properties are equivalent to another object.
        
        This will only be True if all properties match (except for the host) and
        will otherwise be False.
        """
        if not is_equivalent(self._construction, other._construction):
            return False
        if not is_equivalent(self._vent_opening, other._vent_opening):
            return False
        return True

    def _window_construction(self):
        """Get the base window construction assigned to the aperture."""
        win_con = self.construction
        if isinstance(win_con, WindowConstructionShade):
            win_con = win_con.window_construction
        elif isinstance(win_con, WindowConstructionDynamic):
            win_con = win_con.constructions[0]
        return win_con

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Aperture Energy Properties: [host: {}]'.format(self.host.display_name)
