@property
def face_to_idf(self):
    """generate face idf representation."""
    #     TODO(): Check self.geo_type first. This only works for a Face. Fails for
    #     PolyFace, etc
    ep = self.properties.energy

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
            self.name,
            self.properties.face_type.name,
            ep.construction.name,
            self.parent.name if self.parent else 'unknown',
            ep.boundary_condition.name,
            ep.boundary_condition.boundary_condition_object_idf,
            ep.boundary_condition.sun_exposure_idf,
            ep.boundary_condition.wind_exposure_idf,
            ep.boundary_condition.view_factor,
            len(self.vertices),
            ',\n\t'.join('%f, %f, %f' % (v[0], v[1], v[2]) for v in self.vertices)
        )
    return idf_string
