"""Face writer to idf."""


def face_to_idf(face):
    """generate face idf representation."""
    #     TODO(): Check face.geo_type first. This only works for a Face. Fails for
    #     PolyFace, etc
    en_prop = face.properties.energy

    idf_string = 'BuildingSurface:Detailed,' \
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
            face.properties.face_type.name,
            en_prop.construction.name if en_prop.construction else '',
            face.parent.name if face.parent else 'unknown',
            face.boundary_condition.name,
            face.boundary_condition.boundary_condition_object_idf,
            face.boundary_condition.sun_exposure_idf,
            face.boundary_condition.wind_exposure_idf,
            face.boundary_condition.view_factor,
            len(face.vertices),
            ',\n\t'.join('%f, %f, %f' % (v[0], v[1], v[2]) for v in face.vertices)
        )
    return idf_string
