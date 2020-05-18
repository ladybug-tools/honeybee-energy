# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class EditFractionRadiantOfLightingAndEquipment < OpenStudio::Ruleset::ModelUserScript

  # human readable name
  def name
    return "Edit Fraction Radiant of Lighting and Equipment"
  end

  # human readable description
  def description
    return "This measure replaces the 'Fraction Radiant' of all lights and equipment in the model with values that you specify. This is useful for thermal comfort studies where the percentage of heat transferred to the air is important."
  end

  # human readable description of modeling approach
  def modeler_description
    return "This measure replaces the 'Fraction Radiant' of all lights and equipment in the model with values that you specify."
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    #Fraction Radiant of Lights
	lightFract = OpenStudio::Ruleset::OSArgument::makeDoubleArgument("lightsFractRad",false)
	lightFract.setDisplayName("Lights Fraction Radiant")
	lightFract.setDefaultValue(0.0)
	args << lightFract
	
	#Fraction Radiant of Equipment
	equipFract = OpenStudio::Ruleset::OSArgument::makeDoubleArgument("equipFractRad",false)
	equipFract.setDisplayName("Equipment Fraction Radiant")
	equipFract.setDefaultValue(0.0)
	args << equipFract

    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # assign the user inputs to variables
    lightFract = runner.getStringArgumentValue("lightsFractRad", user_arguments).to_f
	equipFract = runner.getStringArgumentValue("equipFractRad", user_arguments).to_f

    # check the inputs for reasonableness
    if lightFract < 0 or lightFract > 1
      runner.registerError("Lights Fraction Radiant must be between 0 and 1.")
      return false
    end
	if equipFract < 0 or equipFract > 1
      runner.registerError("Equipment Fraction Radiant must be between 0 and 1.")
      return false
    end

    # change the fraction radiant of all light and equipment objects in the model.
	lightCount = 0
	equipCount = 0
	space_types = model.getSpaceTypes
	space_types.each do |space_type|
		lights = space_type.lights
		lights.each do |light|
			ldef = model.getLights(light.handle).get
			finalDef = model.getLightsDefinition(ldef.lightsDefinition.handle).get
			finalDef.setFractionRadiant(lightFract)
			lightCount += 1
		end
		equips = space_type.electricEquipment
		equips.each do |equip|
			edef = model.getElectricEquipment(equip.handle).get
			finalDef = model.getElectricEquipmentDefinition(edef.electricEquipmentDefinition.handle).get
			finalDef.setFractionRadiant(equipFract)
			equipCount += 1
		end
	end

    # report final condition of model
    runner.registerFinalCondition("The building finished with #{lightCount} light definitions with their fraction radiant set to #{lightFract}.")
	runner.registerFinalCondition("The building finished with #{equipCount} equipment definitions with their fraction radiant set to #{equipFract}.")

    return true

  end
  
end

# register the measure to be used by the application
EditFractionRadiantOfLightingAndEquipment.new.registerWithApplication
