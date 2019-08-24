"""Methods to write to idf."""
from honeybee.boundarycondition import Surface


def generate_idf_string(object_type, values, comments=None):
    """Get an IDF string representation of an EnergyPlus object.

    Args:
        object_type: Text representing the expected start of the IDF object.
            (ie. WindowMaterial:Glazing).
        values: A list of values associated with the EnergyPlus object in the
            order that they are supposed to be written to IDF format.
        comments: A list of text comments with the same length as the values.
            If None, no comments will be written into the object.

    Returns:
        ep_str: Am EnergyPlus IDF string representing a single object.
    """
    if comments is not None:
        space_count = tuple((25 - len(str(n))) for n in values)
        spaces = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
        ep_str = object_type + ',\n ' + '\n '.join(
            '{},{}!- {}'.format(val, space, com) for val, space, com in
            zip(values[:-1], spaces[:-1], comments[:-1]))
        ep_str = ep_str + '\n {};{}!- {}'.format(
            values[-1], spaces[-1], comments[-1])
    else:
        ep_str = object_type + ',\n ' + '\n '.join(
            '{},'.format(val) for val in values[:-1])
        ep_str = ep_str + '\n {};'.format(values[-1])
    return ep_str


def face_to_idf(face):
    """Generate an IDF string representation of a Face.

    Args:
        face: A honeyee Face for which an IDF representation will be returned.
    """

    return 'BuildingSurface:Detailed,' \
        '\n\t%s,\t!- Name' \
        '\n\t%s,\t!- Surface Type' \
        '\n\t%s,\t!- Construction Name' \
        '\n\t%s,\t!- Zone Name' \
        '\n\t%s,\t!- Outside Boundary Condition' \
        '\n\t%s,\t!- Outside Boundary Condition Object' \
        '\n\t%s,\t!- Sun Exposure' \
        '\n\t%s,\t!- Wind Exposure' \
        '\n\t%s,\t!- View Factor to Ground' \
        '\n\t%d,\t!- Number of Vertices' \
        '\n\t%s;' % (
            face.name,
            face.type.name,
            face.properties.energy.construction.name,
            face.parent.name if face.parent else 'unknown',
            face.boundary_condition.name,
            face.boundary_condition.boundary_condition_object if
            isinstance(face.boundary_condition, Surface) else '',
            face.boundary_condition.sun_exposure_idf,
            face.boundary_condition.wind_exposure_idf,
            face.boundary_condition.view_factor,
            len(face.vertices),
            ',\n\t'.join('%f, %f, %f' % (v[0], v[1], v[2]) for v in face.upper_left_vertices)
        )
