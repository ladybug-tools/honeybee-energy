# MIT License
#
# Copyright (c) 2020-2023 Denis Bourgeois & Dan Macumber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

require_relative "resources/tbd"

class TBDMeasure < OpenStudio::Measure::ModelMeasure
  def name
    return "Thermal Bridging and Derating - TBD"
  end

  def description
    return "Derates opaque constructions from major thermal bridges."
  end

  def modeler_description
    return "Check out rd2.github.io/tbd"
  end

  def arguments(model = nil)
    args = OpenStudio::Measure::OSArgumentVector.new

    arg = "alter_model"
    dsc = "For EnergyPlus simulations, leave CHECKED. For iterative "          \
          "exploration with Apply Measures Now, UNCHECK to preserve "          \
          "original OpenStudio model."
    alter = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    alter.setDisplayName("Alter OpenStudio model (Apply Measures Now)")
    alter.setDescription(dsc)
    alter.setDefaultValue(true)
    args << alter

    arg = "sub_tol"
    dsc = "Proximity tolerance (e.g. 0.100 m) between subsurface edges, e.g. " \
          "between near-adjacent window jambs."
    sub_tol = OpenStudio::Measure::OSArgument.makeDoubleArgument(arg, false)
    sub_tol.setDisplayName("Proximity tolerance (m)")
    sub_tol.setDescription(dsc)
    sub_tol.setDefaultValue(TBD::TOL)
    args << sub_tol

    arg = "load_tbd_json"
    dsc = "Loads existing 'tbd.json' file (under '/files'), may override "     \
          "'default thermal bridge' set."
    load_tbd = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    load_tbd.setDisplayName("Load 'tbd.json'")
    load_tbd.setDescription(dsc)
    load_tbd.setDefaultValue(false)
    args << load_tbd

    chs = OpenStudio::StringVector.new
    psi = TBD::PSI.new
    psi.set.keys.each { |k| chs << k.to_s }

    arg = "option"
    dsc = "e.g. 'poor', 'regular', 'efficient', 'code' (may be overridden by " \
          "'tbd.json' file)."
    option = OpenStudio::Measure::OSArgument.makeChoiceArgument(arg, chs, false)
    option.setDisplayName("Default thermal bridge set")
    option.setDescription(dsc)
    option.setDefaultValue("poor (BETBG)")
    args << option

    arg = "write_tbd_json"
    dsc = "Write out 'tbd.out.json' file e.g., to customize for subsequent "   \
          "runs (edit, and place under '/files' as 'tbd.json')."
    write_tbd = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    write_tbd.setDisplayName("Write 'tbd.out.json'")
    write_tbd.setDescription(dsc)
    write_tbd.setDefaultValue(false)
    args << write_tbd

    none = "NONE"
    all_walls = "ALL wall constructions"
    all_roofs = "ALL roof constructions"
    all_flors = "ALL floor constructions"
    walls = {c: {}}
    roofs = {c: {}}
    flors = {c: {}}
    walls[:c][none] = {a: 0}
    roofs[:c][none] = {a: 0}
    flors[:c][none] = {a: 0}
    walls[:c][all_walls] = {a: 100000000000000}
    roofs[:c][all_roofs] = {a: 100000000000000}
    flors[:c][all_flors] = {a: 100000000000000}
    walls[:chx] = OpenStudio::StringVector.new
    roofs[:chx] = OpenStudio::StringVector.new
    flors[:chx] = OpenStudio::StringVector.new

    if model
      model.getSurfaces.each do |s|
        type = s.surfaceType.downcase
        next unless type == "wall" || type == "roofceiling" || type == "floor"
        next unless s.outsideBoundaryCondition.downcase == "outdoors"
        next if s.construction.empty?
        next if s.construction.get.to_LayeredConstruction.empty?
        lc = s.construction.get.to_LayeredConstruction.get
        next if walls[:c].key?(lc.nameString)
        next if roofs[:c].key?(lc.nameString)
        next if flors[:c].key?(lc.nameString)
        walls[:c][lc.nameString] = {a: lc.getNetArea} if type == "wall"
        roofs[:c][lc.nameString] = {a: lc.getNetArea} if type == "roofceiling"
        flors[:c][lc.nameString] = {a: lc.getNetArea} if type == "floor"
      end

      walls[:c] = walls[:c].sort_by{ |k,v| v[:a] }.reverse!.to_h
      walls[:c][all_walls][:a] = 0
      walls[:c].keys.each { |id| walls[:chx] << id }

      roofs[:c] = roofs[:c].sort_by{ |k,v| v[:a] }.reverse!.to_h
      roofs[:c][all_roofs][:a] = 0
      roofs[:c].keys.each { |id| roofs[:chx] << id }

      flors[:c] = flors[:c].sort_by{ |k,v| v[:a] }.reverse!.to_h
      flors[:c][all_flors][:a] = 0
      flors[:c].keys.each { |id| flors[:chx] << id }
    end

    arg = "wall_option"
    dsc = "Target 1x (or 'ALL') wall construction(s) to 'uprate', to achieve " \
          "wall Ut target below."
    chx = walls[:chx]
    wall = OpenStudio::Measure::OSArgument.makeChoiceArgument(arg, chx, false)
    wall.setDisplayName("Wall construction(s) to 'uprate'")
    wall.setDescription(dsc)
    wall.setDefaultValue(chx.to_a.last)
    args << wall

    arg = "roof_option"
    dsc = "Target 1x (or 'ALL') roof construction(s) to 'uprate', to achieve " \
          "roof Ut target below."
    chx = roofs[:chx]
    roof = OpenStudio::Measure::OSArgument.makeChoiceArgument(arg, chx, false)
    roof.setDisplayName("Roof construction(s) to 'uprate'")
    roof.setDescription(dsc)
    roof.setDefaultValue(chx.to_a.last)
    args << roof

    arg = "floor_option"
    dsc = "Target 1x (or 'ALL') floor construction(s) to 'uprate', to achieve "\
          "floor Ut target below."
    chx = flors[:chx]
    floor = OpenStudio::Measure::OSArgument.makeChoiceArgument(arg, chx, false)
    floor.setDisplayName("Floor construction(s) to 'uprate'")
    floor.setDescription(dsc)
    floor.setDefaultValue(chx.to_a.last)
    args << floor

    arg = "wall_ut"
    dsc = "Overall Ut target to meet for wall construction(s). Ignored if "    \
          "previous wall 'uprate' option is set to 'NONE'."
    wall_ut = OpenStudio::Measure::OSArgument.makeDoubleArgument(arg, false)
    wall_ut.setDisplayName("Wall Ut target (W/m2•K)")
    wall_ut.setDescription(dsc)
    wall_ut.setDefaultValue(0.210) # (NECB 2017, climate zone 7)
    args << wall_ut

    arg = "roof_ut"
    dsc = "Overall Ut target to meet for roof construction(s). Ignored if "    \
          "previous roof 'uprate' option is set to 'NONE'."
    roof_ut = OpenStudio::Measure::OSArgument.makeDoubleArgument(arg, false)
    roof_ut.setDisplayName("Roof Ut target (W/m2•K)")
    roof_ut.setDescription(dsc)
    roof_ut.setDefaultValue(0.138) # (NECB 2017, climate zone 7)
    args << roof_ut

    arg = "floor_ut"
    dsc = "Overall Ut target to meet for floor construction(s). Ignored if "   \
          "previous floor 'uprate' option is set to 'NONE'."
    floor_ut = OpenStudio::Measure::OSArgument.makeDoubleArgument(arg, false)
    floor_ut.setDisplayName("Floor Ut target (W/m2•K)")
    floor_ut.setDescription(dsc)
    floor_ut.setDefaultValue(0.162) # (NECB 2017, climate zone 7)
    args << floor_ut

    arg = "gen_UA_report"
    dsc = "Compare ∑U•A + ∑PSI•L + ∑KHI•n : 'Design' vs UA' reference (see "   \
          "pull-down option below)."
    gen_ua_report = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    gen_ua_report.setDisplayName("Generate UA' report")
    gen_ua_report.setDescription(dsc)
    gen_ua_report.setDefaultValue(false)
    args << gen_ua_report

    arg = "ua_reference"
    dsc = "e.g. 'poor', 'regular', 'efficient', 'code'."
    ua_ref = OpenStudio::Measure::OSArgument.makeChoiceArgument(arg, chs, true)
    ua_ref.setDisplayName("UA' reference")
    ua_ref.setDescription(dsc)
    ua_ref.setDefaultValue("code (Quebec)")
    args << ua_ref

    arg = "gen_kiva"
    dsc = "Generates Kiva settings & objects for surfaces with 'foundation' "  \
          "boundary conditions (not 'ground')."
    gen_kiva = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    gen_kiva.setDisplayName("Generate Kiva inputs")
    gen_kiva.setDescription(dsc)
    gen_kiva.setDefaultValue(false)
    args << gen_kiva

    arg = "gen_kiva_force"
    dsc = "Overwrites 'ground' boundary conditions as 'foundation' before "    \
          "generating Kiva inputs (recommended)."
    kiva_force = OpenStudio::Measure::OSArgument.makeBoolArgument(arg, false)
    kiva_force.setDisplayName("Force-generate Kiva inputs")
    kiva_force.setDescription(dsc)
    kiva_force.setDefaultValue(false)
    args << kiva_force

    return args
  end

  def run(mdl, runner, args)
    super(mdl, runner, args)

    argh                 = {}
    argh[:alter        ] = runner.getBoolArgumentValue("alter_model",      args)
    argh[:sub_tol      ] = runner.getDoubleArgumentValue("sub_tol",        args)
    argh[:load_tbd     ] = runner.getBoolArgumentValue("load_tbd_json",    args)
    argh[:option       ] = runner.getStringArgumentValue("option",         args)
    argh[:write_tbd    ] = runner.getBoolArgumentValue("write_tbd_json",   args)
    argh[:wall_ut      ] = runner.getDoubleArgumentValue("wall_ut",        args)
    argh[:roof_ut      ] = runner.getDoubleArgumentValue("roof_ut",        args)
    argh[:floor_ut     ] = runner.getDoubleArgumentValue("floor_ut",       args)
    argh[:wall_option  ] = runner.getStringArgumentValue("wall_option",    args)
    argh[:roof_option  ] = runner.getStringArgumentValue("roof_option",    args)
    argh[:floor_option ] = runner.getStringArgumentValue("floor_option",   args)
    argh[:gen_ua       ] = runner.getBoolArgumentValue("gen_UA_report",    args)
    argh[:ua_ref       ] = runner.getStringArgumentValue("ua_reference",   args)
    argh[:gen_kiva     ] = runner.getBoolArgumentValue("gen_kiva",         args)
    argh[:kiva_force   ] = runner.getBoolArgumentValue("gen_kiva_force",   args)

    argh[:uprate_walls ] = argh[:wall_option ] != "NONE"
    argh[:uprate_roofs ] = argh[:roof_option ] != "NONE"
    argh[:uprate_floors] = argh[:floor_option] != "NONE"

    return false unless runner.validateUserArguments(arguments(mdl), args)

    if argh[:wall_ut] < TBD::TOL
      runner.registerError("Wall Ut must be greater than 0 W/m2•K - Halting")
      return false
    elsif argh[:wall_ut] > 5.678 - TBD::TOL
      runner.registerError("Wall Ut must be lower than 5.678 W/m2•K - Halting")
      return false
    end

    if argh[:roof_ut] < TBD::TOL
      runner.registerError("Roof Ut must be greater than 0 W/m2•K - Halting")
      return false
    elsif argh[:roof_ut] > 5.678 - TBD::TOL
      runner.registerError("Roof Ut must be lower than 5.678 W/m2•K - Halting")
      return false
    end

    if argh[:floor_ut] < TBD::TOL
      runner.registerError("Floor Ut must be greater than 0 W/m2•K - Halting")
      return false
    elsif argh[:floor_ut] > 5.678 - TBD::TOL
      runner.registerError("Floor Ut must be lower than 5.678 W/m2•K - Halting")
      return false
    end

    TBD.clean!
    argh[:schema_path] = nil
    argh[:io_path    ] = nil

    if argh[:load_tbd]
      argh[:io_path] = runner.workflow.findFile('tbd.json')

      if argh[:io_path].empty?
        TBD.log(TBD::FTL, "Can't find 'tbd.json' - simulation halted")
        return TBD.exit(runner, argh)
      else
        argh[:io_path] = argh[:io_path].get.to_s
        # TBD.log(TBD::INF, "Using inputs from #{argh[:io_path]}")  # debugging
        # runner.registerInfo("Using inputs from #{argh[:io_path]}") # debugging
      end
    end

    # Pre-validate ground-facing constructions for KIVA.
    if argh[:kiva_force] || argh[:gen_kiva]
      kva = true

      mdl.getSurfaces.each do |s|
        id = s.nameString
        construction = s.construction
        next unless s.isGroundSurface

        if construction.empty?
          runner.registerError("Invalid construction for KIVA (#{id})")
          kva = false if kva
        else
          construction = construction.get.to_LayeredConstruction

          if construction.empty?
            runner.registerError("KIVA requires layered constructions (#{id})")
            kva = false if kva
          else
            construction = construction.get

            unless TBD.standardOpaqueLayers?(construction)
              runner.registerError("KIVA requires standard materials (#{id})")
              kva = false if kva
            end
          end
        end
      end

      return false unless kva
    end

    # Process all ground-facing surfaces as foundation-facing.
    if argh[:kiva_force]
      argh[:gen_kiva] = true

      mdl.getSurfaces.each do |s|
        next unless s.isGroundSurface
        construction = s.construction.get
        s.setOutsideBoundaryCondition("Foundation")
        s.setConstruction(construction)
      end
    end

    str = "temp_measure_manager.osm"
    seed = runner.workflow.seedFile
    seed = File.basename(seed.get.to_s) unless seed.empty?
    seed = "OpenStudio model" if seed.empty? || seed == str
    argh[:seed] = seed

    if argh[:alter]
      model = mdl
    else
      model = OpenStudio::Model::Model.new
      model.addObjects(mdl.toIdfFile.objects)
    end

    argh[:version ]  = model.getVersion.versionIdentifier
    tbd              = TBD.process(model, argh)
    argh[:io      ]  = tbd[:io      ]
    argh[:surfaces]  = tbd[:surfaces]
    setpoints        = TBD.heatingTemperatureSetpoints?(model)
    setpoints        = TBD.coolingTemperatureSetpoints?(model) || setpoints
    argh[:setpoints] = setpoints

    return TBD.exit(runner, argh)
  end
end

# register the measure to be used by the application
TBDMeasure.new.registerWithApplication
