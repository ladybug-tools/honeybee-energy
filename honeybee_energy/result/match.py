# coding=utf-8
"""Utilities for matching Model geometry with energy simulation results."""
from honeybee.door import Door
from honeybee.aperture import Aperture
from honeybee.face import Face


def match_rooms_to_data(data_collections, rooms):
    """Match honeybee Rooms to the Zone-level data collections from SQLiteResult.

    Args:
        data_collections: An array of data collections that will matched to
            simulation results. Data collections can be of any class (eg.
            MonthlyCollection, DailyCollection) but they should all have headers
            with metadata dictionaries with 'Zone' or 'System' keys. These keys
            will be used to match the data in the collections to the input rooms.
        rooms: An array of honeybee Rooms, which will be matched to the data_collections.
            The length of these Rooms does not have to match the data_collections.

    Returns:
        An array of tuples that contain matched rooms and data collections. All
        tuples have a length of 3 with the following:

        -   room -- A honeybee Room object.

        -   data_collection -- A data collection that matches the honeybee Room.

        -   multiplier -- An integer for the Room multiplier, which may be useful
            for calcuating total results.
    """
    matched_tuples = []  # list of matched rooms and data collections

    # extract the zone identifier from each of the data collections
    zone_ids = []
    use_mult = False
    for data in data_collections:
        if 'Zone' in data.header.metadata:
            zone_ids.append(data.header.metadata['Zone'])
        else:  # it's HVAC system data and we need to see if it's matchable
            hvac_id = data.header.metadata['System']
            use_mult = True
            if '_IDEALAIR' in hvac_id:
                zone_ids.append(hvac_id.split('_IDEALAIR')[0])
            elif ' IDEAL LOADS AIR SYSTEM' in hvac_id:
                zone_ids.append(hvac_id.split(' IDEAL LOADS AIR SYSTEM')[0])
            else:
                zone_ids.append(hvac_id)

    # loop through the rooms and match the data to them
    for room in rooms:
        rm_id = room.identifier.upper()
        for i, data_id in enumerate(zone_ids):
            if data_id == rm_id:
                mult = 1 if not use_mult else room.multiplier
                matched_tuples.append((room, data_collections[i], mult))
                break
    return matched_tuples


def match_faces_to_data(data_collections, faces):
    """Match honeybee faces/sub-faces to data collections from SQLiteResult.

    Args:
        data_collections: An array of data collections that will be mathed to
            the input faces Data collections can be of any class (eg.
            MonthlyCollection, DailyCollection) but they should all have headers
            with metadata dictionaries with 'Surface' keys. These keys will be
            used to match the data in the collections to the input faces.
        faces: An array of honeybee Faces, Apertures, and/or Doors which will be
            matched to the data_collections. Note that a given input Face should
            NOT have its child Apertures or Doors as a separate item

    Returns:
        An array of tuples that contain matched faces/sub-faces and data collections.
        All tuples have a length of 2 with the following:

        -   face -- A honeybee Face, Aperture, or Door object.

        -   data_collection -- A data collection that matches the Face,
            Aperture, or Door.
    """
    matched_tuples = []  # list of matched faces and data collections

    flat_f = []  # flatten the list of nested apertures and doors in the faces
    for face in faces:
        if isinstance(face, Face):
            flat_f.append(face)
            for ap in face.apertures:
                flat_f.append(ap)
            for dr in face.doors:
                flat_f.append(dr)
        elif isinstance(face, (Aperture, Door)):
            flat_f.append(face)
        else:
            raise ValueError('Expected honeybee Face, Aperture, Door or Shade '
                             'for match_faces_to_data. Got {}.'.format(type(face)))

    # extract the surface id from each of the data collections
    srf_ids = []
    for data in data_collections:
        if 'Surface' in data.header.metadata:
            srf_ids.append(data.header.metadata['Surface'])

    # loop through the faces and match the data to them
    for face in flat_f:
        f_id = face.identifier.upper()
        for i, data_id in enumerate(srf_ids):
            if data_id == f_id:
                matched_tuples.append((face, data_collections[i]))
                break
    return matched_tuples
