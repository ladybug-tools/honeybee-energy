"""Energy Face Outside Boundary Condition."""


class _BoundaryCondition(object):

    __slots__ = (
        '_sun_exposure', '_wind_exposure', '_boundary_condition_object', '_view_factor'
    )

    def __init__(self):
        self.sun_exposure = False
        self.wind_exposure = False
        self.boundary_condition_object = None
        self.view_factor = 'autocalculate'

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def sun_exposure(self):
        return self._sun_exposure

    @sun_exposure.setter
    def sun_exposure(self, value):
        assert isinstance(value, bool), \
            'Input value must be a Boolean not {}.'.format(type(value))
        self._sun_exposure = value

    @property
    def wind_exposure(self):
        return self._wind_exposure

    @wind_exposure.setter
    def wind_exposure(self, value):
        assert isinstance(value, bool), \
            'Input value must be a Boolean not {}.'.format(type(value))
        self._wind_exposure = value

    @property
    def boundary_condition_object(self):
        return self._boundary_condition_object

    @boundary_condition_object.setter
    def boundary_condition_object(self, bco):
        self._boundary_condition_object = bco

    @property
    def view_factor(self):
        return self._view_factor

    @view_factor.setter
    def view_factor(self, vf):
        if vf == 'autocalculate':
            self._view_factor = vf
        else:
            self._view_factor = float(vf)

    @property
    def sun_exposure_idf(self):
        return 'NoSun' if not self.wind_exposure else 'SunExposed'

    @property
    def wind_exposure_idf(self):
        return 'NoWind' if not self.wind_exposure else 'WindExposed'

    @property
    def boundary_condition_object_idf(self):
        return '' if not self.boundary_condition_object else \
            self.boundary_condition_object.name

    @property
    def to_dict(self):
        """Boundary condition."""
        return {
            'boundary_condition': self.name,
            'boundary_condition_object': self.boundary_condition_object_idf,
            'sun_exposure': self.sun_exposure_idf,
            'wind_exposure': self.wind_exposure_idf,
            'view_factor': self.view_factor
        }

    def __repr__(self):
        return 'BC: %s' % self.name


class Surface(_BoundaryCondition):

    __slots__ = ()

    def __init__(self, other_object=None):
        _BoundaryCondition.__init__(self)
        self.boundary_condition_object = other_object


class Zone(Surface):
    __slots__ = ()
    pass


class Adiabatic(_BoundaryCondition):
    __slots__ = ()
    pass


class Outdoors(_BoundaryCondition):

    __slots__ = ()

    def __init__(self):
        _BoundaryCondition.__init__(self)
        self.wind_exposure = True
        self.sun_exposure = True


class Ground(_BoundaryCondition):
    __slots__ = ()
    pass


class _BoundaryConditions(object):
    """Boundary conditions."""

    def __init__(self):
        self._outdoors = Outdoors()
        self._adiabatic = Adiabatic()
        self._ground = Ground()

    @property
    def outdoors(self):
        return self._outdoors

    @property
    def adiabatic(self):
        return self._adiabatic

    @property
    def ground(self):
        return self._ground

    def surface(self, other_object):
        return Surface(other_object)

    def zone(self, other_object):
        return Zone(other_object)

    def __contains__(self, value):
        return isinstance(value, _BoundaryCondition)


boundary_conditions = _BoundaryConditions()
