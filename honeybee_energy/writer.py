"""Face writer to idf."""
from honeybee.boundarycondition import Surface


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
