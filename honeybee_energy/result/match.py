# coding=utf-8
"""Utilities for matching Model geometry with energy simulation results."""
from __future__ import division

import re

from honeybee.typing import clean_ep_string
from honeybee.door import Door
from honeybee.aperture import Aperture
from honeybee.face import Face


def match_rooms_to_data(
        data_collections, rooms, invert_multiplier=False, space_based=False,
        zone_correct_mult=True):
    """Match honeybee Rooms to the Zone-level data collections from SQLiteResult.

    This method ensures that Room multipliers are correctly output for a given
    EnergyPlus output.

    Args:
        data_collections: An array of data collections that will matched to
            simulation results. Data collections can be of any class (eg.
            MonthlyCollection, DailyCollection) but they should all have headers
            with metadata dictionaries with 'Zone' or 'System' keys. These keys
            will be used to match the data in the collections to the input rooms.
        rooms: An array of honeybee Rooms, which will be matched to the data_collections.
            The length of these Rooms does not have to match the data_collections.
        invert_multiplier: Boolean to note whether the output room multiplier should be
            included when the data type values already account for the multiplier
            (False) or when they do not (True). (Default: False).
        space_based: Boolean to note whether the result is reported on the EnergyPlus
            Space level instead of the Zone level. In this case, the matching to
            the Room will account for the fact that the Space name is the Room
            name with _Space added to it. (Default: False).
        zone_correct_mult: Boolean to note whether the multiplier in the returned result
            should be divided by the number of Rooms within each zone when
            space_based is False. This is useful for ensuring that, overall,
            values reported on the zone level and matched to Rooms are not counted
            more than once for zones with multiple Rooms. Essentially, multiplying
            each Room data collection by the multiplier before summing results
            together ensures that the final summed result is accurate. Setting
            this to False will make the multiplier in the result equal to the
            Room.multiplier property, which may be useful for certain visualizations
            where rooms are to be colored with the total result for their parent
            zone. (Default: True).

    Returns:
        An array of tuples that contain matched rooms and data collections. All
        tuples have a length of 3 with the following:

        -   room -- A honeybee Room object.

        -   data_collection -- A data collection that matches the honeybee Room.

        -   multiplier -- An integer for the Room multiplier, which may be useful
            for calculating total results.
    """
    # extract the zone identifier from each of the data collections
    zone_ids = []
    use_mult = False
    for data in data_collections:
        if 'Zone' in data.header.metadata:
            zone_ids.append(data.header.metadata['Zone'])
        else:  # it's HVAC system data and we need to see if it's matchable
            hvac_id = data.header.metadata['System']
            use_mult = True
            if ' IDEAL LOADS AIR SYSTEM' in hvac_id:  # convention of E+ HVAC Templates
                zone_ids.append(hvac_id.split(' IDEAL LOADS AIR SYSTEM')[0])
            elif '..' in hvac_id:  # convention used for service hot water
                zone_ids.append(hvac_id.split('..')[-1])
                use_mult = False if 'Gain' in data.header.metadata['type'] else True
            else:
                use_mult = False
                zone_ids.append(hvac_id)
    if invert_multiplier:
        use_mult = not use_mult
    if space_based:
        zone_ids = [zid.replace('_SPACE', '') for zid in zone_ids]

    # count the number of rooms in each zone to zone-correct the multiplier
    if not space_based and zone_correct_mult:
        zone_counter = {}
        for room in rooms:
            z_id = clean_ep_string(room.zone)
            try:
                zone_counter[z_id] += 1
            except KeyError:  # first room found in the zone
                zone_counter[z_id] = 1

    # loop through the rooms and match the data to them
    matched_tuples = []  # list of matched rooms and data collections
    for room in rooms:
        if space_based:
            rm_id, zc = room.identifier.upper(), 1
        else:
            z_id = clean_ep_string(room.zone)
            rm_id = z_id.upper()
            zc = zone_counter[z_id] if zone_correct_mult else 1
        for i, data_id in enumerate(zone_ids):
            if data_id == rm_id:
                mult = 1 if not use_mult else room.multiplier
                matched_tuples.append((room, data_collections[i], mult / zc))
                break

    return matched_tuples


def match_faces_to_data(data_collections, faces):
    """Match honeybee faces/sub-faces to data collections from SQLiteResult.

    This method will correctly match triangulated apertures and doors with a
    merged version of the relevant data_collections.

    Args:
        data_collections: An array of data collections that will be matched to
            the input faces Data collections can be of any class (eg.
            MonthlyCollection, DailyCollection) but they should all have headers
            with metadata dictionaries with 'Surface' keys. These keys will be
            used to match the data in the collections to the input faces.
        faces: An array of honeybee Faces, Apertures, and/or Doors which will be
            matched to the data_collections. Note that a given input Face should
            NOT have its child Apertures or Doors as a separate item.

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
    tri_srf_ids = {}  # track data collections from triangulated apertures/doors
    tri_pattern = re.compile(r".*\.\.\d")
    for data in data_collections:
        if 'Surface' in data.header.metadata:
            srf_ids.append(data.header.metadata['Surface'])
            if tri_pattern.match(data.header.metadata['Surface']) is not None:
                base_name = re.sub(r'(\.\.\d*)', '', data.header.metadata['Surface'])
                try:
                    tri_srf_ids[base_name].append(data)
                except KeyError:  # first triangulated piece found
                    tri_srf_ids[base_name] = [data]

    # loop through the faces and match the data to them
    for face in flat_f:
        f_id = face.identifier.upper()
        for i, data_id in enumerate(srf_ids):
            if data_id == f_id:
                matched_tuples.append((face, data_collections[i]))
                break
        else:  # check to see if it's a triangulated sub-face
            try:
                data_colls = tri_srf_ids[f_id]
                matched_tuples.append(
                    (face, _merge_collections(data_colls, f_id)))
            except KeyError:
                pass  # the face could not be matched with any data
    return matched_tuples


def _merge_collections(data_collections, surface_id):
    """Combine several data collections for a triangulated surface into one.

    This method will automatically decide to either sum the collection data or
    average it depending on whether the data collection data_type is cumulative.

    Args:
        data_collections: A list of data collections to be merged.
        surface_id: The identifier of the combined surface, encompassing
            all triangulated pieces.
    """
    # total all of the values in the data collections
    merged_data = data_collections[0]
    for data in data_collections[1:]:
        merged_data = merged_data + data
    # divide by the number of collections if the data type is not cumulative
    if not data_collections[0].header.data_type.cumulative:
        merged_data = merged_data / len(data_collections)
    # create the final data collection
    merged_data = merged_data.duplicate()  # duplicate to avoid editing the header
    merged_data.header.metadata['Surface'] = surface_id
    return merged_data
