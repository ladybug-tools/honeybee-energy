# coding=utf-8
"""Window frame materials.

The materials here can only be applied as frames to window constructions.
"""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_in_range_excl_incl, float_positive

from ._base import _EnergyMaterialBase
from ..reader import parse_idf_string
from ..writer import generate_idf_string


@lockable
class EnergyWindowFrame(_EnergyMaterialBase):
    """A window frame assigned to a Window Construction.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        width: Number for the width of frame in plane of window [m]. The frame
            width is assumed to be the same on all sides of window.
        conductance: Number for the thermal conductance of the frame material measured
            from inside to outside of the frame surface (no air films) and taking 2D
            conduction effects into account [W/m2-K]. Values for typical frame
            materials are as follows.

            * Aluminum with Thermal Break - 56.4 W/m2-K
            * Aluminum One-Sided (Flush) - 10.7 W/m2-K
            * Wood - 3.5 W/m2-K
            * Vinyl - 2.3 W/m2-K

        edge_to_center_ratio: Number between 0 and 4 for the ratio of the glass
            conductance near the frame (excluding air films) divided by the glass
            conductance at the center of the glazing (excluding air films).
            This is used only for multi-pane glazing constructions. This ratio should
            usually be greater than 1.0 since the spacer material that separates
            the glass panes is usually more conductive than the gap between panes.
            A value of 1 effectively indicates no spacer. Values should usually be
            obtained from the LBNL WINDOW program so that the unique characteristics
            of the window construction can be accounted for. (Default: 1).
        outside_projection: Number for the distance that the frame projects outward
            from the outside face of the glazing [m]. This is used to calculate shadowing
            of frame onto glass, solar absorbed by the frame, IR emitted and
            absorbed by the frame, and convection from frame. (Default: 0).
        inside_projection: Number for the distance that the frame projects inward
            from the inside face of the glazing [m]. This is used to calculate solar
            absorbed by the frame, IR emitted and absorbed by the frame, and
            convection from frame. (Default: 0).
        thermal_absorptance: A number between 0 and 1 for the fraction of incident long
            wavelength radiation that is absorbed by the material. (Default: 0.9).
        solar_absorptance: A number between 0 and 1 for the fraction of incident
            solar radiation absorbed by the material. (Default: 0.7).
        visible_absorptance: A number between 0 and 1 for the fraction of incident
            visible wavelength radiation absorbed by the material.
            Default is None, which will yield the same value as solar_absorptance.

    Properties:
        * identifier
        * display_name
        * width
        * conductance
        * edge_to_center_ratio
        * outside_projection
        * inside_projection
        * thermal_absorptance
        * solar_absorptance
        * visible_absorptance
        * solar_reflectance
        * visible_reflectance
        * u_value
        * r_value
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_width', '_conductance',
                 '_edge_to_center_ratio', '_outside_projection', '_inside_projection',
                 '_thermal_absorptance', '_solar_absorptance', '_visible_absorptance')

    def __init__(self, identifier, width, conductance, edge_to_center_ratio=1,
                 outside_projection=0, inside_projection=0, thermal_absorptance=0.9,
                 solar_absorptance=0.7, visible_absorptance=None):
        """Initialize energy material."""
        _EnergyMaterialBase.__init__(self, identifier)
        self.width = width
        self.conductance = conductance
        self.edge_to_center_ratio = edge_to_center_ratio
        self.outside_projection = outside_projection
        self.inside_projection = inside_projection
        self.thermal_absorptance = thermal_absorptance
        self.solar_absorptance = solar_absorptance
        self.visible_absorptance = visible_absorptance
        self._locked = False

    @property
    def width(self):
        """Get or set the width of frame in plane of window [m]."""
        return self._width

    @width.setter
    def width(self, value):
        self._width = float_in_range_excl_incl(value, 0.0, 1.0, 'window frame width')

    @property
    def conductance(self):
        """Get or set the conductance of the frame material [W/m2-K]."""
        return self._conductance

    @conductance.setter
    def conductance(self, cond):
        self._conductance = float_positive(cond, 'window frame conductance')

    @property
    def edge_to_center_ratio(self):
        """Get or set the ratio between the edge and center glass conductances."""
        return self._edge_to_center_ratio

    @edge_to_center_ratio.setter
    def edge_to_center_ratio(self, value):
        self._edge_to_center_ratio = float_in_range_excl_incl(
            value, 0.0, 4.0, 'window frame edge-to-center ratio')

    @property
    def outside_projection(self):
        """Get or set the distance the frame projects from the outside [m]."""
        return self._outside_projection

    @outside_projection.setter
    def outside_projection(self, value):
        self._outside_projection = float_in_range(
            value, 0.0, 0.5, 'window frame outside projection')

    @property
    def inside_projection(self):
        """Get or set the distance the frame projects from the inside [m]."""
        return self._inside_projection

    @inside_projection.setter
    def inside_projection(self, value):
        self._inside_projection = float_in_range(
            value, 0.0, 0.5, 'window frame inside projection')

    @property
    def thermal_absorptance(self):
        """Get or set the thermal absorptance of the frame material."""
        return self._thermal_absorptance

    @thermal_absorptance.setter
    def thermal_absorptance(self, t_abs):
        self._thermal_absorptance = float_in_range(
            t_abs, 0.0, 1.0, 'window frame thermal absorptance')

    @property
    def solar_absorptance(self):
        """Get or set the solar absorptance of the frame material."""
        return self._solar_absorptance

    @solar_absorptance.setter
    def solar_absorptance(self, s_abs):
        self._solar_absorptance = float_in_range(
            s_abs, 0.0, 1.0, 'window frame solar absorptance')

    @property
    def visible_absorptance(self):
        """Get or set the visible absorptance of the frame material."""
        return self._visible_absorptance if self._visible_absorptance is not None \
            else self._solar_absorptance

    @visible_absorptance.setter
    def visible_absorptance(self, v_abs):
        self._visible_absorptance = float_in_range(
            v_abs, 0.0, 1.0, 'window frame visible absorptance') if v_abs is not None \
            else None

    @property
    def solar_reflectance(self):
        """Get or set the front solar reflectance of the frame material."""
        return 1 - self.solar_absorptance

    @solar_reflectance.setter
    def solar_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'window frame solar reflectance')
        self.solar_absorptance = 1 - v_ref

    @property
    def visible_reflectance(self):
        """Get or set the front visible reflectance of the frame material."""
        return 1 - self.visible_absorptance

    @visible_reflectance.setter
    def visible_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'window frame visible reflectance')
        self.visible_absorptance = 1 - v_ref

    @property
    def r_value(self):
        """Get or set the R-value of the frame material in [m2-K/W] (excluding films).
        """
        return 1 / self.conductance

    @r_value.setter
    def r_value(self, r_val):
        _new_conductance = 1 / float_positive(r_val, 'window frame r-value')
        self._conductance = _new_conductance

    @property
    def u_value(self):
        """Get or set the U-value of the frame material [W/m2-K] (excluding films).
        """
        return self.conductance

    @u_value.setter
    def u_value(self, u_val):
        self.conductance = u_val

    @classmethod
    def from_idf(cls, idf_string):
        """Create an EnergyWindowFrame from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'WindowProperty:FrameAndDivider,')
        idf_defaults = ('unnamed', 0, 0, 0, 0, 1, 0.7, 0.7, 0.9)
        for i, d_val in enumerate(idf_defaults):  # fill in any default values
            try:
                if ep_strs[i] == '':
                    ep_strs[i] = d_val
            except IndexError:
                ep_strs.append(d_val)
        if float(ep_strs[1]) == 0 or float(ep_strs[4]) == 0:
            return None  # no frame definition within WindowProperty:FrameAndDivider
        return cls(
            ep_strs[0], ep_strs[1], ep_strs[4], ep_strs[5], ep_strs[2], ep_strs[3],
            ep_strs[6], ep_strs[7], ep_strs[8])

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowFrame from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowFrame',
            "identifier": 'Wood_Frame_050_032',
            "display_name": 'Pine Wooden Frame',
            "width": 0.05,
            "conductance": 3.2,
            "edge_to_center_ratio": 2.6,
            "outside_projection": 0.05,
            "inside_projection": 0.1,
            "thermal_absorptance": 0.9,
            "solar_absorptance": 0.7,
            "visible_absorptance": 0.7
            }
        """
        assert data['type'] == 'EnergyWindowFrame', \
            'Expected EnergyWindowFrame. Got {}.'.format(data['type'])

        ratio = data['edge_to_center_ratio'] if 'edge_to_center_ratio' in data and \
            data['edge_to_center_ratio'] is not None else 1
        out_pro = data['outside_projection'] if 'outside_projection' in data and \
            data['outside_projection'] is not None else 0
        in_pro = data['inside_projection'] if 'inside_projection' in data and \
            data['inside_projection'] is not None else 0
        t_abs = data['thermal_absorptance'] if 'thermal_absorptance' in data and \
            data['thermal_absorptance'] is not None else 0.9
        s_abs = data['solar_absorptance'] if 'solar_absorptance' in data and \
            data['solar_absorptance'] is not None else 0.7
        v_abs = data['visible_absorptance'] if 'visible_absorptance' in data else None

        new_mat = cls(data['identifier'], data['width'], data['conductance'],
                      ratio, out_pro, in_pro, t_abs, s_abs, v_abs)
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']

        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the window frame."""
        values = (
            self.identifier, self.width, self.outside_projection, self.inside_projection,
            self.conductance, self.edge_to_center_ratio, self.solar_absorptance,
            self.visible_absorptance, self.thermal_absorptance)
        comments = (
            'name', 'width {m}', 'outside projection {m}', 'inside projection {m}',
            'conductance {W/m2-K}', 'edge-to-center-of-glass conductance ratio',
            'solar absorptance', 'visible absorptance', 'thermal absorptance')
        return generate_idf_string('WindowProperty:FrameAndDivider', values, comments)

    def to_dict(self):
        """EnergyWindowFrame dictionary representation."""
        base = {
            'type': 'EnergyWindowFrame',
            'identifier': self.identifier,
            'width': self.width,
            'conductance': self.conductance,
            'edge_to_center_ratio': self.edge_to_center_ratio,
            'outside_projection': self.outside_projection,
            'inside_projection': self.inside_projection,
            'thermal_absorptance': self.thermal_absorptance,
            'solar_absorptance': self.solar_absorptance,
            'visible_absorptance': self.visible_absorptance
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (
            self.identifier, self.width, self.conductance, self.edge_to_center_ratio,
            self.outside_projection, self.inside_projection,
            self.thermal_absorptance, self.solar_absorptance, self.visible_absorptance)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowFrame) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = self.__class__(
            self.identifier, self.width, self.conductance, self.edge_to_center_ratio,
            self.outside_projection, self.inside_projection, self.thermal_absorptance,
            self.solar_absorptance, self._visible_absorptance)
        new_material._display_name = self._display_name
        new_material._user_data = None if self._user_data is None \
            else self._user_data.copy()
        return new_material
