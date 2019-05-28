"""Energy zone."""
import re
from .lib.constructionset import generic


class Zone(object):

    def __init__(self, name, origin=None, constructionset=None):
        self.name = name
        self.origin = origin
        self.constructionset = constructionset or generic
        self._faces = []

    @classmethod
    def from_room(self, room, constructionset=None):
        raise NotImplementedError()

    @property
    def name(self):
        """Zone name."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = re.sub(r'[^.A-Za-z0-9_-]', '', value)
        self._name_original = value

    @property
    def name_original(self):
        """Original input name by user.

        If there is no illegal characters in name then name and name_original will be the
        same. Legal characters are ., A-Z, a-z, 0-9, _ and -. Invalid characters are
        removed from the original name for compatability with simulation engines.
        """
        return self._name_original

    @property
    def faces(self):
        """List of zone faces."""
        return self._faces

    @property
    def constructionset(self):
        return self._constructionset

    @constructionset.setter
    def constructionset(self, value):
        self._constructionset = value
        # update construction set for each face if not already set by user
        for face in self._faces:
            if face.property.energy.is_construction_set_by_user:
                continue
            face._constructionset = self._constructionset

    def add_face(self, face):
        self._faces.append(face)
        # similar to face <> aperture this is two-way association and weakref might be
        # the correct way of doing it. TODO: try using weakref instead!
        face.parent = self
        if not face.property.energy.is_construction_set_by_user:
            face._constructionset = self._constructionset
