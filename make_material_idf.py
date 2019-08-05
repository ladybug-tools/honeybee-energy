from honeybee_energy.lib.default.face import brick, concrete_lw, concrete_hw, \
    insulation, insulation_thin, gypsum, acoustic_tile, metal_surface, \
    roof_membrane, wood, wall_gap, ceiling_gap, air

from honeybee_energy.lib.default.face import clear_glass, lowe_glass, air_gap, argon_gap

from honeybee_energy.lib.default.face import generic_exterior_wall, generic_interior_wall, \
    generic_underground_wall, generic_exposed_floor, generic_interior_floor, \
    generic_ground_slab, generic_roof, generic_interior_ceiling, \
    generic_underground_roof, generic_double_pane, generic_single_pane, \
    generic_exterior_door, generic_interior_door, air_wall


all_opaque_materials = [brick, concrete_lw, concrete_hw, insulation,
                        insulation_thin, gypsum, acoustic_tile, metal_surface,
                        roof_membrane, wood, wall_gap, ceiling_gap, air]
all_window_materials = [clear_glass, lowe_glass, air_gap, argon_gap]

all_opaque_constr = [generic_exterior_wall, generic_interior_wall,
                     generic_underground_wall, generic_exposed_floor,
                     generic_interior_floor, generic_ground_slab, generic_roof,
                     generic_interior_ceiling, generic_underground_roof,
                     generic_exterior_door, generic_interior_door, air_wall]
all_window_constr = [generic_double_pane, generic_single_pane]

m = '!- These constructions are loaded into the honeybee_energy library as defaults.\n' \
 '!- Editing these materials and/or constructions will edit the defaults used across\n' \
 '!- all of honeybee_energy as long as the names of the constructions are kept.\n\n' \
 '!- Note that these constructions are not in accordance with any particular building\n' \
 '!- code or climate zone. They are just meant to represent "typical" constructions\n' \
 '!- that are plausible for a building constructed in the last few decades. While they\n' \
 '!- provide a decent starting point, it is recommended that at least the outdoor\n' \
 '!- constructions be changed to suit a given project building code and climate.\n\n\n'


dest_file = 'C:/Users/chris/Documents/GitHub/honeybee-energy/honeybee_energy/' \
    'lib/idf/constructions/default.idf'

with open(dest_file, 'w') as fp:
    fp.write('!-   =========  DEFAULT HONEYBEE CONSTRUCTIONS =========\n')
    fp.write(m)
    fp.write('!-   ================  OPAQUE MATERIALS ================\n\n')
    for mat in all_opaque_materials:
        fp.write(mat.to_idf() + '\n\n')
    fp.write('\n!-   ================  WINDOW MATERIALS ================\n\n')
    for mat in all_window_materials:
        fp.write(mat.to_idf() + '\n\n')
    fp.write('\n!-   ==============  OPAQUE CONSTRUCTIONS ==============\n\n')
    for cnstr in all_opaque_constr:
        fp.write(cnstr.to_idf()[0] + '\n\n')
    fp.write('\n!-   ==============  WINDOW CONSTRUCTIONS ==============\n\n')
    for cnstr in all_window_constr:
        fp.write(cnstr.to_idf()[0] + '\n\n')
