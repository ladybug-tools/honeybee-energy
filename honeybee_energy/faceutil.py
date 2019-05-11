@property
def face_to_idf(self):
    """generate face idf representation."""
    # BuildingSurface:Detailed,
    #     Zn001:Wall001,           !- Name
    #     Wall,                    !- Surface Type
    #     R13WALL,                 !- Construction Name
    #     Main Zone,               !- Zone Name
    #     Outdoors,                !- Outside Boundary Condition
    #     ,                        !- Outside Boundary Condition Object
    #     SunExposed,              !- Sun Exposure
    #     WindExposed,             !- Wind Exposure
    #     0.5000000,               !- View Factor to Ground
    #     4,                       !- Number of Vertices
    #     0,0,4.572000,  !- X,Y,Z ==> Vertex 1 {m}
    #     0,0,0,  !- X,Y,Z ==> Vertex 2 {m}
    #     15.24000,0,0,  !- X,Y,Z ==> Vertex 3 {m}
    #     15.24000,0,4.572000;  !- X,Y,Z ==> Vertex 4 {m}
    return 'BuildingSurface:Detailed,\n\t%s,\n\t%s,\n\t%s;' % (
        self.name,
        self.properties.face_type,
        self.properties.energy.construction.name,
        # self.parent.name
        )
