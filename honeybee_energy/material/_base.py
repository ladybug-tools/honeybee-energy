# coding=utf-8
"""Base energy material."""
from __future__ import division
import xml.etree.ElementTree as ET

from ladybug.datatype.distance import Distance
from ladybug.datatype.conductivity import Conductivity
from ladybug.datatype.density import Density
from ladybug.datatype.specificheatcapacity import SpecificHeatCapacity
from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, clean_string


@lockable
class _EnergyMaterialBase(object):
    """Base energy material.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.

    Properties:
        * identifier
        * display_name
        * user_data
        * properties
    """
    __slots__ = ('_identifier', '_display_name', '_locked', '_user_data', '_properties')

    def __init__(self, identifier):
        """Initialize energy material base."""
        self._locked = False
        self.identifier = identifier
        self._display_name = None
        self._user_data = None
        self._properties = None

    @property
    def identifier(self):
        """Get or set the text string for material identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'material identifier')

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
        if value is not None:
            try:
                value = str(value)
            except UnicodeEncodeError:  # Python 2 machine lacking the character set
                pass  # keep it as unicode
        self._display_name = value

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

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def _compare_thickness_conductivity(self):
        """Compare the thickness and conductivity to avoid CTF errors from EnergyPlus.

        These CTF errors were common in EnergyPlus 9.5 and below but they have
        been completely eliminated in more recent versions.
        """
        try:
            assert self._conductivity / self._thickness <= 200000, \
                'Material layer "{}" does not have sufficient thermal resistance.\n'\
                'Either increase the thickness or remove it from the ' \
                'construction.'.format(self.identifier)
        except ZeroDivisionError:
            raise ValueError(
                'Material layer "{}" cannot have zero thickness.'.format(self.identifier)
            )
        except AttributeError:
            pass  # conductivity or thickness has not yet been set

    def __copy__(self):
        new_obj = self.__class__(self.identifier)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Base Energy Material:\n{}'.format(self.display_name)


@lockable
class _EnergyMaterialOpaqueBase(_EnergyMaterialBase):
    """Base energy material for all opaque material types."""
    ROUGHTYPES = ('VeryRough', 'Rough', 'MediumRough',
                  'MediumSmooth', 'Smooth', 'VerySmooth')
    RADIANCEROUGHTYPES = {'VeryRough': 0.2, 'Rough': 0.2, 'MediumRough': 0.15,
                          'MediumSmooth': 0.1, 'Smooth': 0.05, 'VerySmooth': 0}
    __slots__ = ()

    @property
    def is_window_material(self):
        """Boolean to note whether the material can be used for window surfaces."""
        return False

    def to_gbxml_element(self, ip_units=False, parent_element=None):
        """Get a gbXML Material Element representation of this object.

        Args:
            ip_units: A boolean to note whether the properties should be reported
                in IP units (True) or SI units (False). (Default: False).
            parent_element: An optional XML Element for the gbXML root to which the
                material element will be added. If None, a new XML Element
                will be generated. (Default: None).
        """
        # create the Material element
        con_id = clean_string(self.identifier)
        if parent_element is not None:
            xml_mat = ET.SubElement(parent_element, 'Material', id=con_id)
        else:
            xml_mat = ET.Element('Material', id=con_id)
        # set the units of properties
        if ip_units:
            thick_units, cond_units, dens_units, sh_units = \
                'Feet', 'BtuPerHourFtF', 'LbsPerCubicFt', 'BTUPerLbF'
            thick = round(Distance().to_ip([self.thickness], 'm')[0][0], 4)
            cond = round(Conductivity().to_ip([self.conductivity], 'W/m-K')[0][0], 3)
            dens = round(Density().to_ip([self.density], 'kg/m3')[0][0], 3)
            sh = round(SpecificHeatCapacity().to_ip([self.specific_heat], 'J/kg-K')[0][0], 3)
        else:
            thick_units, cond_units, dens_units, sh_units = \
                'Meters', 'WPerMeterK', 'KgPerCubicM', 'JPerKgK'
            thick = round(self.thickness, 4)
            cond = round(self.conductivity, 3)
            dens = round(self.density, 2)
            sh = round(self.specific_heat, 2)
        # add the name and the required properties
        xml_name = ET.SubElement(xml_mat, 'Name')
        xml_name.text = str(self.display_name)
        xml_rough = ET.SubElement(xml_mat, 'Roughness')
        xml_rough.text = str(self.roughness)
        xml_thick = ET.SubElement(xml_mat, 'Thickness', unit=thick_units)
        xml_thick.text = str(thick)
        xml_cond = ET.SubElement(xml_mat, 'Conductivity', unit=cond_units)
        xml_cond.text = str(cond)
        xml_dens = ET.SubElement(xml_mat, 'Density', unit=dens_units)
        xml_dens.text = str(dens)
        xml_sh = ET.SubElement(xml_mat, 'SpecificHeat', unit=sh_units)
        xml_sh.text = str(sh)
        # add the reflectance and absorptance
        self._add_gbxml_reflectance(xml_mat)
        return xml_mat

    def to_gbxml(self, ip_units=False):
        """Generate an gbXML string representation of this object.

        Args:
            ip_units: A boolean to note whether the U-value should be reported
                in IP units (True) or SI units (False). (Default: False).
        """
        xml_root = self.to_gbxml_element(ip_units)
        try:  # try to indent the XML to make it read-able
            ET.indent(xml_root)
            return ET.tostring(xml_root, encoding='unicode')
        except AttributeError:  # we are in Python 2 and no indent is available
            return ET.tostring(xml_root)

    def _add_gbxml_reflectance(self, xml_mat):
        """Add the reflectance and absorptance to a gbXML element of the material."""
        # add the reflectance
        xml_rf_sol = ET.SubElement(xml_mat, 'Reflectance', type='ExtSolar')
        xml_rf_sol.text = str(round(self.solar_reflectance, 3))
        xml_rb_sol = ET.SubElement(xml_mat, 'Reflectance', type='IntSolar')
        xml_rb_sol.text = str(round(self.solar_reflectance, 3))
        xml_rf_vis = ET.SubElement(xml_mat, 'Reflectance', type='ExtVisible')
        xml_rf_vis.text = str(round(self.visible_reflectance, 3))
        xml_rb_vis = ET.SubElement(xml_mat, 'Reflectance', type='IntVisible')
        xml_rb_vis.text = str(round(self.visible_reflectance, 3))
        therm_ref = 1 - self.thermal_absorptance
        xml_rf_th = ET.SubElement(xml_mat, 'Reflectance', type='ExtIR')
        xml_rf_th.text = str(round(therm_ref, 3))
        xml_rb_th = ET.SubElement(xml_mat, 'Reflectance', type='IntIR')
        xml_rb_th.text = str(round(therm_ref, 3))
        all_r = (xml_rf_sol, xml_rb_sol, xml_rf_vis, xml_rb_vis, xml_rf_th, xml_rb_th)
        for xml_ref in all_r:
            xml_ref.set('unit', 'Fraction')
            xml_ref.set('surfaceType', 'Both')
        # add the absorptance
        xml_af_sol = ET.SubElement(xml_mat, 'Absorptance', type='ExtSolar')
        xml_af_sol.text = str(round(self.solar_absorptance, 3))
        xml_ab_sol = ET.SubElement(xml_mat, 'Absorptance', type='IntSolar')
        xml_ab_sol.text = str(round(self.solar_absorptance, 3))
        xml_af_vis = ET.SubElement(xml_mat, 'Absorptance', type='ExtVisible')
        xml_af_vis.text = str(round(self.visible_absorptance, 3))
        xml_ab_vis = ET.SubElement(xml_mat, 'Absorptance', type='IntVisible')
        xml_ab_vis.text = str(round(self.visible_absorptance, 3))
        xml_af_th = ET.SubElement(xml_mat, 'Absorptance', type='ExtIR')
        xml_af_th.text = str(round(self.thermal_absorptance, 3))
        xml_ab_th = ET.SubElement(xml_mat, 'Absorptance', type='IntIR')
        xml_ab_th.text = str(round(self.thermal_absorptance, 3))
        all_a = (xml_af_sol, xml_ab_sol, xml_af_vis, xml_ab_vis, xml_af_th, xml_ab_th)
        for xml_abs in all_a:
            xml_ref.set('unit', 'Fraction')

    def __repr__(self):
        return 'Base Opaque Energy Material:\n{}'.format(self.display_name)


@lockable
class _EnergyMaterialWindowBase(_EnergyMaterialBase):
    """Base energy material for all window material types."""
    __slots__ = ()

    @property
    def is_window_material(self):
        """Boolean to note whether the material can be used for window surfaces."""
        return True

    @property
    def is_glazing_material(self):
        """Boolean to note whether the material is a glazing layer."""
        return False

    @property
    def is_gas_material(self):
        """Boolean to note whether the material is a gas gap layer."""
        return False

    @property
    def is_shade_material(self):
        """Boolean to note whether the material is a shade layer."""
        return False

    def __repr__(self):
        return 'Base Window Energy Material:\n{}'.format(self.display_name)
