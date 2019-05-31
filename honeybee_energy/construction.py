"""Energy construction."""


class Construction(object):

    def __init__(self, name, materials):
        """Energy construction.
        
        args:
            name: Construction name.
            materials: List of energy materials from outside to inside.
        """
        self.name = name
        self.materials = materials

    def to_dict(self):
        """Construction dictionary representation."""
        return {
            'type': 'EnergyConstruction',
            'name': self.name,
            'materials': [m.to_dict for m in self.materials]
        }

    def to_idf(self):
        """idf representation of construction object."""
        idf_string = 'Construction,\n\t%s,\n\t%s;' % (
            self.name,
            ',\n'.join(m.name for m in self.materials)
        )
        return idf_string

    def __repr__(self):
        return 'EnergyConstruction:%s' % self.name
