"""Module for creating baseline buildings conforming to standards."""
import os

from ladybug.futil import csv_to_matrix
from honeybee.boundarycondition import Outdoors
from honeybee.facetype import Wall, RoofCeiling

from ..material.glazing import EnergyWindowMaterialSimpleGlazSys
from ..construction.window import WindowConstruction
from ..lib.constructionsets import construction_set_by_identifier
from ..lib.programtypes import program_type_by_identifier
from ..hvac._template import _TemplateSystem
from ..hvac.heatcool._base import _HeatCoolBase
from ..hvac.allair.vav import VAV
from ..hvac.allair.pvav import PVAV
from ..hvac.allair.psz import PSZ
from ..hvac.allair.ptac import PTAC
from ..hvac.allair.furnace import ForcedAirFurnace
from ..hvac.doas.fcu import FCUwithDOAS
from ..shw import SHWSystem


def model_to_baseline(model, climate_zone, building_type='NonResidential',
                      floor_area=None, story_count=None, lighting_by_building=False):
    """Convert a Model to be conformant with ASHRAE 90.1 appendix G.

    This includes running all other functions contained within this group to adjust
    the geometry, constructions, lighting, HVAC, SHW, and remove any clearly-defined
    energy conservation measures like daylight controls. Note that all schedules
    are essentially unchanged, meaning that additional post-processing of setpoints
    may be necessary to account for energy conservation strategies like expanded
    comfort ranges, ceiling fans, and personal thermal comfort devices. It may
    also be necessary to adjust electric equipment loads in cases where such
    equipment qualifies as an energy conservation strategy or hot water loads in
    cases where low-flow fixtures are implemented.

    Note that not all versions of ASHRAE 90.1 use this exact definition of a
    baseline model but version 2016 and onward conform to it. It is essentially
    an adjusted version of the 90.1-2004 methods.

    Args:
        model: A Honeybee Model that will be converted to conform to the ASHRAE 90.1
            appendix G baseline.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
        building_type: Text for the building type that the Model represents. This is
            used to determine the baseline window-to-wall ratio and HVAC system. If
            the type is not recognized or is "Unknown", it will be assumed that the
            building is a generic NonResidential. The following have specified
            meaning per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse

        floor_area: A number for the floor area of the building that the model is a part
            of in m2. If None, the model floor area will be used. (Default: None).
        story_count: An integer for the number of stories of the building that the
            model is a part of. If None, the model stories will be used. (Default: None).
        lighting_by_building: A boolean to note whether the building_type should
            be used to assign the baseline lighting power density (True), which will
            use the same value for all Rooms in the model, or a space-by-space method
            should be used (False). To use the space-by-space method, the model should
            either be built with the programs that ship with Ladybug Tools in
            honeybee-energy-standards or the baseline_watts_per_area should be correctly
            assigned for all Rooms. (Default: False).
    """
    model_geometry_to_baseline(model, building_type)
    model_constructions_to_baseline(model, climate_zone)
    if lighting_by_building:
        model_lighting_to_baseline_building(model, building_type)
    else:
        model_lighting_to_baseline(model)
    model_hvac_to_baseline(model, climate_zone, building_type, floor_area, story_count)
    model_shw_to_baseline(model, building_type)
    model_remove_ecms(model)


def model_geometry_to_baseline(model, building_type='NonResidential'):
    """Convert a Model's geometry to be conformant with ASHRAE 90.1 appendix G.

    This includes stripping out all attached shades (leaving detached shade as
    context), reducing the vertical glazing ratio to a level conformant to the
    building_type (or 40% if the building type is unknown and the model is above
    this value), and reducing the skylight ratio to 3% if it's above this value.

    Note that not all versions of ASHRAE 90.1 use this exact definition of
    baseline geometry but version 2016 and onward conform to it. It is
    essentially an adjusted version of the 90.1-2004 methods.

    Args:
        model: A Honeybee Model that will have its geometry adjusted to
            conform to the baseline.
        building_type: Text for the building type that the Model represents.
            This is used to set the maximum window ratio for the model. If the
            type is not recognized or is "Unknown", a maximum of 40% shall
            be used. The following have specified ratios per the standard.

            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant

    """
    # remove all non-context shade
    model.remove_assigned_shades()  # remove all of the child shades
    or_shades = [shd for shd in model.orphaned_shades if shd.is_detached]
    model.remove_shades()
    for shd in or_shades:
        model.add_shade(shd)

    # determine the maximum glazing ratio using the building type
    ratio_file = os.path.join(os.path.dirname(__file__), 'data', 'fen_ratios.csv')
    ratio_data = csv_to_matrix(ratio_file)
    max_ratio = 0.4
    for row in ratio_data:
        if row[0] == building_type:
            max_ratio = float(row[1])
            break

    # compute the window and skylight ratios
    w_area = model.exterior_wall_area
    r_area = model.exterior_roof_area
    wa_area = model.exterior_wall_aperture_area
    ra_area = model.exterior_skylight_aperture_area
    wr = wa_area / w_area if w_area != 0 else 0
    sr = ra_area / r_area if r_area != 0 else 0

    # if the window or skylight ratio is greater than max permitted, set it to max
    if wr > max_ratio:  # set all walls to have the maximum ratio
        adjust_factor = max_ratio / wr
        for room in model.rooms:
            for face in room.faces:
                if isinstance(face.boundary_condition, Outdoors) and \
                        isinstance(face.type, Wall):
                    new_ratio = face.aperture_ratio * adjust_factor
                    face.apertures_by_ratio(new_ratio, model.tolerance)
    if sr > 0.03:  # reduce all skylights by the amount needed for 5%
        red_fract = 0.03 / sr  # scale factor for all of the skylights
        for room in model.rooms:
            for face in room.faces:
                if isinstance(face.boundary_condition, Outdoors) and \
                        isinstance(face.type, RoofCeiling) and \
                        len(face._apertures) > 0:
                    new_ratio = face.aperture_ratio * red_fract
                    face.apertures_by_ratio(new_ratio)


def model_constructions_to_baseline(model, climate_zone):
    """Convert a Model's constructions to be conformant with ASHRAE 90.1 appendix G.

    This includes assigning a ConstructionSet that is compliant with Table G3.4
    to all rooms in the model, accounting for the fenestration ratios in the process.

    Note that not all versions of ASHRAE 90.1 use this exact definition of
    baseline constructions but version 2016 and onward conform to it. It is
    essentially an adjusted version of the 90.1-2004 methods.

    Args:
        model: A Honeybee Model that will have its constructions adjusted to
            conform to the baseline.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    # compute the fenestration ratios across the model
    w_area = model.exterior_wall_area
    r_area = model.exterior_roof_area
    wr = model.exterior_wall_aperture_area / w_area if w_area != 0 else 0
    sr = model.exterior_skylight_aperture_area / r_area if r_area != 0 else 0

    # get the base ConstructionSet from the standards library
    clean_cz = str(climate_zone)[0]
    constr_set_id = '2004::ClimateZone{}::SteelFramed'.format(clean_cz)
    base_set = construction_set_by_identifier(constr_set_id)

    # parse the CSV file with exceptions to the base construction set
    ex_file = os.path.join(os.path.dirname(__file__), 'data', 'constructions.csv')
    ex_data = csv_to_matrix(ex_file)
    ex_cz = clean_cz if climate_zone != '3C' else climate_zone
    ex_ratio = '100'
    for ratio in (40, 30, 20, 10):
        if wr < ratio / 100 + 0.001:
            ex_ratio = str(ratio)
    for row in ex_data:
        if row[0] == ex_cz and row[1] == ex_ratio:
            vert_except = [float(val) for val in row[2:]]
            break

    # change the constructions for fixed and operable windows
    si_ip_u = 5.678263337
    fixed_id = 'U {} SHGC {} Fixed Glz'.format(vert_except[0], vert_except[2])
    fixed_mat = EnergyWindowMaterialSimpleGlazSys(
        fixed_id, vert_except[0] * si_ip_u, vert_except[2])
    fixed_constr = WindowConstruction(fixed_id.replace('Glz', 'Window'), [fixed_mat])
    oper_id = 'U {} SHGC {} Operable Glz'.format(vert_except[1], vert_except[2])
    oper_mat = EnergyWindowMaterialSimpleGlazSys(
        oper_id, vert_except[1] * si_ip_u, vert_except[2])
    oper_constr = WindowConstruction(oper_id.replace('Glz', 'Window'), [oper_mat])
    base_set.aperture_set.window_construction = fixed_constr
    base_set.aperture_set.operable_construction = oper_constr

    # change the construction for skylights if the ratio is greater than 2%
    if sr > 0.021:
        for row in ex_data:
            if row[0] == ex_cz and row[1] == 'sky_5':
                sky_except = [float(row[2]), float(row[4])]
                break
        sky_id = 'U {} SHGC {} Skylight Glz'.format(sky_except[0], sky_except[1])
        sky_mat = EnergyWindowMaterialSimpleGlazSys(
            sky_id, sky_except[0] * si_ip_u, sky_except[1])
        sky_constr = WindowConstruction(sky_id.replace('Glz', 'Window'), [sky_mat])
        base_set.aperture_set.skylight_construction = sky_constr

    # remove child constructions ans assign the construction set to all rooms
    model.properties.energy.remove_child_constructions()
    for room in model.rooms:
        room.properties.energy.construction_set = base_set


def model_lighting_to_baseline(model):
    """Convert a Model's lighting to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes determining whether an ASHRAE 2004 equivalent exists for each
    program type in the model. If none is found, the baseline_watts_per_area on
    the room's program's lighting will be used, which will default to a typical
    office if none has been specified.

    Args:
        model: A Honeybee Model that will have its lighting power adjusted to
            conform to the baseline.
    """
    # loop through the rooms and try to find equivalent programs in 2004
    for room in model.rooms:
        if room.properties.energy.lighting is None or \
                room.properties.energy.lighting.watts_per_area == 0:
            continue
        prog_name = room.properties.energy.program_type.identifier.split('::')
        prog_2004 = None
        if len(prog_name) >= 3:
            new_prog_name = '2004::{}::{}'.format(prog_name[1], prog_name[2])
            try:
                prog_2004 = program_type_by_identifier(new_prog_name)
            except ValueError:  # no equivalent program in ASHRAE 2004
                pass
        # if program was found, use it to assign the LPD
        if prog_2004 is not None and prog_2004.lighting is not None:
            dup_light = room.properties.energy.lighting.duplicate()
            dup_light.watts_per_area = prog_2004.lighting.watts_per_area
        elif room.properties.energy.program_type.lighting is not None:
            dup_light = room.properties.energy.program_type.lighting.duplicate()
            dup_light.watts_per_area = dup_light.baseline_watts_per_area
        else:
            dup_light = room.properties.energy.lighting.duplicate()
            dup_light.watts_per_area = dup_light.baseline_watts_per_area
        dup_light.identifier = '{}_Lighting'.format(room.identifier)
        room.properties.energy.lighting = dup_light


def model_lighting_to_baseline_building(model, building_type='NonResidential'):
    """Convert a Model's lighting to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes looking up the building type's average lighting power density
    and assigning it to all Rooms in the model.

    Args:
        model: A Honeybee Model that will have its lighting power adjusted to
            conform to the baseline.
        building_type: Text for the building type that the Model represents. If
            the type is not recognized or is "Unknown", it will be assumed that the
            building is a generic NonResidential (aka. an office). The following
            have specified meaning per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse
    """
    # determine the lighting power density using the building type
    lpd_file = os.path.join(os.path.dirname(__file__), 'data', 'lpd_building.csv')
    lpd_data = csv_to_matrix(lpd_file)
    lpd = 1.0
    for row in lpd_data:
        if row[0] == building_type:
            lpd = float(row[1])
            break
    lpd = lpd * 10.7639  # convert to W/m2 from W/ft2

    # assign the lighting power density to all rooms in the model
    for room in model.rooms:
        if room.properties.energy.lighting is None or \
                room.properties.energy.lighting.watts_per_area == 0:
            continue
        dup_light = room.properties.energy.lighting.duplicate()
        dup_light.watts_per_area = lpd
        dup_light.identifier = '{}_Lighting'.format(room.identifier)
        room.properties.energy.lighting = dup_light


def model_hvac_to_baseline(model, climate_zone, building_type='NonResidential',
                           floor_area=None, story_count=None):
    """Convert a Model's HVAC to be conformant with ASHRAE 90.1 appendix G.

    This includes the selection of the correct Appendix G template HVAC based on
    the inputs and the application of this HVAC to all conditioned spaces in
    the model.

    Note that not all versions of ASHRAE 90.1 use this exact definition of
    baseline HVAC but version 2016 and onward conform to it. It is
    essentially an adjusted version of the 90.1-2004 methods.

    Args:
        model: A Honeybee Model that will have its HVAC adjusted to conform to
            the baseline.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
        building_type: Text for the building type that the Model represents. This is
            used to determine the baseline system. If the type is not recognized or
            is "Unknown", it will be assumed that the building is a generic
            NonResidential. The following have specified systems per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory

        floor_area: A number for the floor area of the building that the model is a part
            of in m2. If None, the model floor area will be used. (Default: None).
        story_count: An integer for the number of stories of the building that the
            model is a part of. If None, the model stories will be used. (Default: None).
    """
    # set the standard to be used and the climate zone
    std = 'ASHRAE_2004'
    if len(climate_zone) == 1:
        climate_zone = '{}A'.format(climate_zone)

    # determine whether the system uses fuel or electricity from the climate zone
    fuel = climate_zone not in ('0A', '0B', '1A', '1B', '2A', '2B', '3A')

    # determine whether the building type is residential or it's heated-only storage
    res_types = ('Residential', 'MidriseApartment', 'HighriseApartment'
                 'SmallHotel', 'LargeHotel')
    residential = building_type in res_types
    heat_only = False
    if building_type == 'Warehouse':
        for hvac in model.properties.energy.hvacs:
            if isinstance(hvac, _HeatCoolBase) and \
                    hvac.equipment_type in hvac.HEAT_ONLY_TYPES:
                heat_only = True
                break
            elif isinstance(hvac, ForcedAirFurnace):
                heat_only = True
                break

    # determine the HVAC template from the input criteria
    if residential:
        hvac_id = 'Baseline PT Residential HVAC'
        hvac_sys = PTAC(hvac_id, std, 'PTAC_BoilerBaseboard') \
            if fuel else PTAC(hvac_id, std, 'PTHP')
    elif heat_only:
        hvac_id = 'Baseline Warm Air Furnace HVAC'
        hvac_sys = ForcedAirFurnace(hvac_id, std, 'Furnace') \
            if fuel else ForcedAirFurnace(hvac_id, std, 'Furnace_Electric')
    else:
        # determine the floor area if it is not input
        if floor_area == 0 or floor_area is None:
            floor_area = model.floor_area
            floor_area = floor_area if model.units == 'Meters' else \
                floor_area * model.conversion_factor_to_meters(model.units)
        # determine the number of stories if it is not input
        if story_count == 0 or story_count is None:
            story_count = len(model.stories)
        # determine the HVAC from the floor area and stories
        hvac_temp = 'Baseline {} HVAC'
        if building_type in ('Retail, StripMall') and story_count <= 2:
            hvac_id = hvac_temp.format('PSZ')
            hvac_sys = PSZ(hvac_id, std, 'PSZAC_Boiler') \
                if fuel else PSZ(hvac_id, std, 'PSZHP')
        elif story_count > 5 or floor_area > 13935.5:  # more than 150,000 ft2
            hvac_id = hvac_temp.format('VAV')
            hvac_sys = VAV(hvac_id, std, 'VAV_Chiller_Boiler') \
                if fuel else VAV(hvac_id, std, 'VAV_Chiller_PFP')
        elif story_count > 3 or floor_area > 2322.6:  # more than 25,000 ft2
            hvac_id = hvac_temp.format('PVAV')
            hvac_sys = PVAV(hvac_id, std, 'PVAV_Boiler') \
                if fuel else PVAV(hvac_id, std, 'PVAV_PFP')
        elif building_type in ('Hospital', 'Laboratory'):
            hvac_id = hvac_temp.format('PVAV')
            hvac_sys = PVAV(hvac_id, std, 'PVAV_Boiler') \
                if fuel else PVAV(hvac_id, std, 'PVAV_PFP')
        else:
            hvac_id = hvac_temp.format('PSZ')
            hvac_sys = PSZ(hvac_id, std, 'PSZAC_Boiler') \
                if fuel else PSZ(hvac_id, std, 'PSZHP')
        if climate_zone not in ('0A', '0B', '1A', '1B', '2A', '3A', '4A'):
            hvac_sys.economizer_type = 'DifferentialDryBulb'

    # apply the HVAC template to all conditioned rooms in the model
    dhw_only, dch_only, dhw_dcw = [], [], []
    for room in model.rooms:
        r_hvac = room.properties.energy.hvac
        if r_hvac is not None:
            if isinstance(r_hvac, _TemplateSystem):
                if not r_hvac.has_district_heating and not r_hvac.has_district_cooling:
                    room.properties.energy.hvac = hvac_sys
                elif r_hvac.has_district_heating and r_hvac.has_district_cooling:
                    dhw_dcw.append(room)
                elif r_hvac.has_district_heating:
                    dhw_only.append(room)
                else:
                    dch_only.append(room)
            else:
                room.properties.energy.hvac = hvac_sys

    # if there were any rooms with district heating or cooling, substitute the system
    if len(dhw_dcw) != 0:
        if isinstance(hvac_sys, (VAV, PVAV)):
            hvac_id = hvac_temp.format('VAV') + ' DHW DCW'
            new_hvac_sys = VAV(hvac_id, std, 'VAV_DCW_DHW')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PSZ):
            hvac_id = hvac_temp.format('PSZ') + ' DHW DCW'
            new_hvac_sys = PSZ(hvac_id, std, 'PSZAC_DCW_DHW')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PTAC):
            hvac_id = 'Baseline FCU Residential HVAC DHW DCW'
            new_hvac_sys = FCUwithDOAS(hvac_id, std, 'DOAS_FCU_DCW_DHW')
        else:
            new_hvac_sys = hvac_sys
        for room in dhw_dcw:
            room.properties.energy.hvac = new_hvac_sys
    if len(dch_only) != 0:
        if isinstance(hvac_sys, (VAV, PVAV)):
            hvac_id = hvac_temp.format('VAV') + ' DCW'
            new_hvac_sys = VAV(hvac_id, std, 'VAV_DCW_Boiler') \
                if fuel else PVAV(hvac_id, std, 'VAV_DCW_PFP')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PSZ):
            hvac_id = hvac_temp.format('PSZ') + ' DCW'
            new_hvac_sys = PSZ(hvac_id, std, 'PSZAC_DCW_Boiler')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PTAC):
            hvac_id = 'Baseline FCU Residential HVAC DCW'
            new_hvac_sys = FCUwithDOAS(hvac_id, std, 'DOAS_FCU_DCW_Boiler')
        else:
            new_hvac_sys = hvac_sys
        for room in dch_only:
            room.properties.energy.hvac = new_hvac_sys
    if len(dhw_only) != 0:
        if isinstance(hvac_sys, VAV):
            hvac_id = hvac_temp.format('VAV') + ' DHW'
            new_hvac_sys = VAV(hvac_id, std, 'VAV_Chiller_DHW')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PVAV):
            hvac_id = hvac_temp.format('PVAV') + ' DHW'
            new_hvac_sys = PVAV(hvac_id, std, 'PVAV_DHW')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PSZ):
            hvac_id = hvac_temp.format('PSZ') + ' DHW'
            new_hvac_sys = PSZ(hvac_id, std, 'PSZAC_DHW')
            new_hvac_sys.economizer_type = hvac_sys.economizer_type
        elif isinstance(hvac_sys, PTAC):
            hvac_id = 'Baseline PT Residential HVAC DHW'
            hvac_sys = PTAC(hvac_id, std, 'PTAC_DHW')
        else:
            new_hvac_sys = hvac_sys
        for room in dhw_only:
            room.properties.energy.hvac = new_hvac_sys


def model_shw_to_baseline(model, building_type='NonResidential'):
    """Convert a Model's SHW systems to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes looking up the building type's baseline heating method and
    assigning it to all Rooms with a SHW system in the model.

    Args:
        model: A Honeybee Model that will have its Service Hot Water (SHW) systems
            adjusted to conform to the baseline.
        building_type: Text for the building type that the Model represents. If
            the type is not recognized or is "Unknown", it will be assumed that
            the building is a generic NonResidential (aka. an office). The following
            have specified meaning per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse
    """
    # determine the service hot water system using the building type
    shw_file = os.path.join(os.path.dirname(__file__), 'data', 'shw.csv')
    shw_data = csv_to_matrix(shw_file)
    shw_t = 'Gas'
    for row in shw_data:
        if row[0] == building_type:
            shw_t = row[1]
            break
    shw_sys = SHWSystem('Baseline Gas SHW System', 'Gas_WaterHeater') if shw_t == 'Gas' \
        else SHWSystem('Baseline Electric Resistance SHW System', 'Electric_WaterHeater')

    # assign the SHW system to all relevant rooms in the model
    for room in model.rooms:
        if room.properties.energy.shw is None:
            continue
        room.properties.energy.shw = shw_sys


def model_remove_ecms(model):
    """Remove energy conservation strategies (ECMs) not associated with baseline models.

    This includes removing the opening behavior of all operable windows, daylight
    controls, etc.

    Args:
        model: A Honeybee Model that will have its lighting power adjusted to
            conform to the baseline.
    """
    # loop through the rooms and remove daylight controls
    for room in model.rooms:
        room.properties.energy.daylighting_control = None
    # loop through the rooms and remove operable windows
    for room in model.rooms:
        room.properties.energy.window_vent_control = None
        room.properties.energy.remove_ventilation_opening()
        for face in room.faces:
            for ap in face.apertures:
                ap.is_operable = False
