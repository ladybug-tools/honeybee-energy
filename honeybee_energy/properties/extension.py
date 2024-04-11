# coding: utf-8
"""Extension properties for Honeybee-Energy objects like constructions and schedules.

These properties classes can be used to extend the honeybee-energy for
other purposes. For example, extending the capabilities of constructions for
embodied carbon or extending schedules and loads for creation of compliance
reports for certain standards (eg. passive house).
"""


class _EnergyProperties(object):
    """Base class for all Honeybee-Energy Properties classes.

    Args:
        host: A honeybee-energy object that hosts these properties
            (ie. ScheduleRuleset, OpaqueConstruction, WindowConstruction).
    """
    _exclude = {'host', 'to_dict', 'ToString'}

    def __init__(self, host):
        """Initialize properties."""
        self._host = host

    @property
    def host(self):
        """Get the object hosting these properties."""
        return self._host

    @property
    def _extension_attributes(self):
        return (atr for atr in dir(self) if not atr.startswith('_')
                and atr not in self._exclude)

    def to_dict(self):
        """Convert properties to dictionary.

        Will be None if no extension attributes exist.
        """
        base = {'type': self.__class__.__name__}
        for atr in self._extension_attributes:
            var = getattr(self, atr)
            if not hasattr(var, 'to_dict'):
                continue
            try:
                base.update(var.to_dict())
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception('Failed to convert {} to a dict: {}'.format(var, e))
        return base if len(base) != 1 else None

    def _load_extension_attr_from_dict(self, property_dict):
        """Get attributes for extensions from a dictionary of the properties.

        This method should be called within the from_dict method of each
        honeybee-energy object. Specifically, this method should be called on
        the host object after it has been created from a dictionary but lacks
        any of the extension attributes in the dictionary.

        Args:
            property_dict: A dictionary of properties for the object (ie.
                ScheduleRulesetProperties, OpaqueConstructionProperties).
                These will be used to load attributes from the dictionary and
                assign them to the object on which this method is called.
        """
        for atr in self._extension_attributes:
            var = getattr(self, atr)
            if not hasattr(var, 'from_dict'):
                continue
            
            atr_prop_dict = property_dict.get(atr, None)
            if not atr_prop_dict:
                # the property_dict possesses no properties for that extension
                continue 
            setattr(self, '_' + atr, var.__class__.from_dict(atr_prop_dict, self.host)) 

    def _duplicate_extension_attr(self, original_properties):
        """Duplicate the attributes added by extensions.

        This method should be called within the duplicate or __copy__ methods of
        each honeybee-energy object after the host object has been duplicated.
        This method only needs to be called on the new (duplicated) host object and
        the extension properties of the original host object should be passed to
        this method as the original_properties.

        Args:
            original_properties: The properties object of the original host
                object from which the duplicate was derived.
        """
        for atr in self._extension_attributes:
            var = getattr(original_properties, atr)
            if not hasattr(var, 'duplicate'):
                continue
            try:
                setattr(self, '_' + atr, var.duplicate(self.host))
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception('Failed to duplicate {}: {}'.format(var, e))

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Properties representation."""
        return '{}: {}'.format(self.__class__.__name__, self.host.display_name)
    
    def move(self, move_vec):
        """Move the property's extensions along a vector.

        Args:
            moving_vec: A ladybug_geometry Vector3D with the direction and distance
                to move the object.
        """
        for extension_name in self._extension_attributes:
            extension = getattr(self, extension_name)
            if not hasattr(extension, "move"):
                continue
            try:
                extension.move(move_vec)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception("Failed to move {}: {}".format(extension, e))

    def rotate(self, angle, origin):
        """Rotate the .properties by a certain angle around an axis and origin.

        Args:
            angle: An angle for rotation in degrees.
            axis: Rotation axis as a Vector3D.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        for extension_name in self._extension_attributes:
            extension = getattr(self, extension_name)
            if not hasattr(extension, "rotate"):
                continue
            try:
                extension.rotate(angle, origin)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception("Failed to rotate {}: {}".format(extension, e))
    
    def rotate_xy(self, angle, origin):
        """Rotate the .properties counterclockwise in the world XY plane by a certain angle.

        Args:
            angle: An angle in degrees.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        for extension_name in self._extension_attributes:
            extension = getattr(self, extension_name)
            if not hasattr(extension, "rotate_xy"):
                continue
            try:
                extension.rotate_xy(angle, origin)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception("Failed to rotate {}: {}".format(extension, e))

    def reflect(self, plane):
        """Reflect the .properties across a plane.

        Args:
            plane: A ladybug_geometry Plane across which the object will
                be reflected.
        """
        for extension_name in self._extension_attributes:
            extension = getattr(self, extension_name)
            if not hasattr(extension, "reflect"):
                continue
            try:
                extension.reflect(plane)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception("Failed to reflect {}: {}".format(extension, e))

    def scale(self, factor, origin=None):
        """Scale the .properties by a factor from an origin point.

        Args:
            factor: A number representing how much the object should be scaled.
            origin: A ladybug_geometry Point3D representing the origin from which
                to scale. If None, it will be scaled from the World origin (0, 0, 0).
        """
        for extension_name in self._extension_attributes:
            extension = getattr(self, extension_name)
            if not hasattr(extension, "scale"):
                continue
            try:
                extension.scale(factor, origin)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception("Failed to scale {}: {}".format(extension, e))


class ScheduleRulesetProperties(_EnergyProperties):
    """ScheduleRuleset properties to be extended by extensions."""


class ScheduleFixedIntervalProperties(_EnergyProperties):
    """ScheduleFixedInterval properties to be extended by extensions."""


class OpaqueConstructionProperties(_EnergyProperties):
    """OpaqueConstruction properties to be extended by extensions."""


class ShadeConstructionProperties(_EnergyProperties):
    """ShadeConstruction properties to be extended by extensions."""


class WindowConstructionProperties(_EnergyProperties):
    """WindowConstruction properties to be extended by extensions."""


class WindowConstructionShadeProperties(_EnergyProperties):
    """WindowConstructionShade properties to be extended by extensions."""


class ElectricEquipmentProperties(_EnergyProperties):
    """ElectricEquipment properties to be extended by extensions."""


class GasEquipmentProperties(_EnergyProperties):
    """GasEquipment properties to be extended by extensions."""


class ServiceHotWaterProperties(_EnergyProperties):
    """ServiceHotWater properties to be extended by extensions."""


class SHWSystemProperties(_EnergyProperties):
    """SHWSystem (Equipment) properties to be extended by extensions."""


class InfiltrationProperties(_EnergyProperties):
    """Infiltration properties to be extended by extensions."""


class LightingProperties(_EnergyProperties):
    """Lighting properties to be extended by extensions."""


class PeopleProperties(_EnergyProperties):
    """People properties to be extended by extensions."""


class ProcessProperties(_EnergyProperties):
    """Process properties to be extended by extensions."""


class SetpointProperties(_EnergyProperties):
    """Setpoint properties to be extended by extensions."""


class VentilationProperties(_EnergyProperties):
    """Ventilation properties to be extended by extensions."""


class IdealAirSystemProperties(_EnergyProperties):
    """IdealAirSystem properties to be extended by extensions."""


class AllAirSystemProperties(_EnergyProperties):
    """AllAirSystem HVAC properties to be extended by extensions."""


class DOASSystemProperties(_EnergyProperties):
    """DOASSystem HVAC properties to be extended by extensions."""


class HeatCoolSystemProperties(_EnergyProperties):
    """HeatCoolSystem HVAC properties to be extended by extensions."""


class EnergyMaterialProperties(_EnergyProperties):
    """EnergyMaterial properties to be extended by extensions."""


class EnergyMaterialNoMassProperties(_EnergyProperties):
    """EnergyMaterialNoMass properties to be extended by extensions."""


class EnergyMaterialVegetationProperties(_EnergyProperties):
    """EnergyMaterialVegetation properties to be extended by extensions."""