

###### (Automatically generated documentation)

# Thermal Bridging and Derating - TBD

## Description
Derates opaque constructions from major thermal bridges.

## Modeler Description
Check out rd2.github.io/tbd

## Measure Type
ModelMeasure

## Taxonomy


## Arguments


### Alter OpenStudio model (Apply Measures Now)
For EnergyPlus simulations, leave CHECKED. For iterative exploration with Apply Measures Now, UNCHECK to preserve original OpenStudio model.
**Name:** alter_model,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Proximity tolerance (m)
Proximity tolerance (e.g. 0.100 m) between subsurface edges, e.g. between near-adjacent window jambs.
**Name:** sub_tol,
**Type:** Double,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Load 'tbd.json'
Loads existing 'tbd.json' file (under '/files'), may override 'default thermal bridge' set.
**Name:** load_tbd_json,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Default thermal bridge set
e.g. 'poor', 'regular', 'efficient', 'code' (may be overridden by 'tbd.json' file).
**Name:** option,
**Type:** Choice,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Write 'tbd.out.json'
Write out 'tbd.out.json' file e.g., to customize for subsequent runs (edit, and place under '/files' as 'tbd.json').
**Name:** write_tbd_json,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Wall construction(s) to 'uprate'
Target 1x (or 'ALL') wall construction(s) to 'uprate', to achieve wall Ut target below.
**Name:** wall_option,
**Type:** Choice,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Roof construction(s) to 'uprate'
Target 1x (or 'ALL') roof construction(s) to 'uprate', to achieve roof Ut target below.
**Name:** roof_option,
**Type:** Choice,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Floor construction(s) to 'uprate'
Target 1x (or 'ALL') floor construction(s) to 'uprate', to achieve floor Ut target below.
**Name:** floor_option,
**Type:** Choice,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Wall Ut target (W/m2•K)
Overall Ut target to meet for wall construction(s). Ignored if previous wall 'uprate' option is set to 'NONE'.
**Name:** wall_ut,
**Type:** Double,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Roof Ut target (W/m2•K)
Overall Ut target to meet for roof construction(s). Ignored if previous roof 'uprate' option is set to 'NONE'.
**Name:** roof_ut,
**Type:** Double,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Floor Ut target (W/m2•K)
Overall Ut target to meet for floor construction(s). Ignored if previous floor 'uprate' option is set to 'NONE'.
**Name:** floor_ut,
**Type:** Double,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Generate UA' report
Compare ∑U•A + ∑PSI•L + ∑KHI•n : 'Design' vs UA' reference (see pull-down option below).
**Name:** gen_UA_report,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### UA' reference
e.g. 'poor', 'regular', 'efficient', 'code'.
**Name:** ua_reference,
**Type:** Choice,
**Units:** ,
**Required:** true,
**Model Dependent:** false

### Generate Kiva inputs
Generates Kiva settings & objects for surfaces with 'foundation' boundary conditions (not 'ground').
**Name:** gen_kiva,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false

### Force-generate Kiva inputs
Overwrites 'ground' boundary conditions as 'foundation' before generating Kiva inputs (recommended).
**Name:** gen_kiva_force,
**Type:** Boolean,
**Units:** ,
**Required:** false,
**Model Dependent:** false




