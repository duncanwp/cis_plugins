__author__ = 'watson-parris'
from cis.data_io.products.HadGEM import HadGEM_PP


class HadGEM_UKCA(HadGEM_PP):

    def __init__(self):
        from iris.fileformats.um_cf_map import STASH_TO_CF, CFName
        super(HadGEM_UKCA, self).__init__()
    
        # Section 0: Horizontal winds (assume non-rotated grid)
        STASH_TO_CF["m01s00i002"] = CFName("eastward_wind", None, "m s-1")
        STASH_TO_CF["m01s00i003"] = CFName("northward_wind", None, "m s-1")

        # Section 0: Emissions
        STASH_TO_CF["m01s00i121"] = CFName(None, 'tendency_of_atmosphere_mass_content_of_sulfur_dioxide_due_to_volcanic_emission_expressed_as_sulfur', 'kg m-2 s-1') # IRIS 1.7.2 has wrong units (kg/kg) for this
        STASH_TO_CF["m01s00i309"] = CFName("tendency_of_atmosphere_mass_content_of_isoprene_due_to_emission", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i310"] = CFName("tendency_of_atmosphere_mass_content_of_black_carbon_dry_aerosol_due_to_emission_from_fossil_fuel_burning", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i311"] = CFName("tendency_of_atmosphere_mass_content_of_black_carbon_dry_aerosol_due_to_emission_from_biofuel_burning", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i312"] = CFName("tendency_of_atmosphere_mass_content_of_particulate_organic_matter_dry_aerosol_due_to_emission_from_fossil_fuel_burning", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i313"] = CFName("tendency_of_atmosphere_mass_content_of_particulate_organic_matter_dry_aerosol_due_to_emission_from_biofuel_burning", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i314"] = CFName("tendency_of_atmosphere_mass_content_of_monoterpenes_due_to_emission", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i316"] = CFName("tendency_of_atmosphere_mass_content_of_black_carbon_dry_aerosol_due_to_emission_from_wildfires", None, "kg m-2 s-1")
        STASH_TO_CF["m01s00i317"] = CFName("tendency_of_atmosphere_mass_content_of_particulate_organic_matter_dry_aerosol_due_to_emission_from_wildfires", None, "kg m-2 s-1")

        # Section 2: extinction and absorption profiles
        STASH_TO_CF["m01s02i114"] = CFName("optical_thickness_of_atmosphere_layer_due_to_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i115"] = CFName("absorption_optical_thickness_of_atmosphere_layer_due_to_ambient_aerosol", None, "1")

        # Section 2: AAOD
        STASH_TO_CF["m01s02i240"] = CFName("atmosphere_absorption_optical_thickness_due_to_soluble_aitken_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i241"] = CFName("atmosphere_absorption_optical_thickness_due_to_soluble_accumulation_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i242"] = CFName("atmosphere_absorption_optical_thickness_due_to_soluble_coarse_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i243"] = CFName("atmosphere_absorption_optical_thickness_due_to_insoluble_aitken_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i247"] = CFName("atmosphere_absorption_optical_thickness_due_to_dust_ambient_aerosol", None, "1")

        # Section 2: AOD
        STASH_TO_CF["m01s02i285"] = CFName("atmosphere_optical_thickness_due_to_dust_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i300"] = CFName("atmosphere_optical_thickness_due_to_soluble_aitken_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i301"] = CFName("atmosphere_optical_thickness_due_to_soluble_accumulation_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i302"] = CFName("atmosphere_optical_thickness_due_to_soluble_coarse_mode_ambient_aerosol", None, "1")
        STASH_TO_CF["m01s02i303"] = CFName("atmosphere_optical_thickness_due_to_insoluble_aitken_mode_ambient_aerosol", None, "1")

        # Section 3: Near-surface winds (assume non-rotated grid)
        STASH_TO_CF["m01s03i209"] = CFName("eastward_wind", None, "m s-1")
        STASH_TO_CF["m01s03i210"] = CFName("northward_wind", None, "m s-1")
        STASH_TO_CF["m01s00i225"] = CFName("eastward_wind", None, "m s-1")
        STASH_TO_CF["m01s00i226"] = CFName("northward_wind", None, "m s-1")


        # Section 15: Dynamics
        STASH_TO_CF["m01s15i271"] = CFName("air_density", None, "kg m-3")

        # Section 34: UKCA Tracers
        STASH_TO_CF["m01s34i101"] = CFName("number_fraction_of_soluble_nucleation_mode_dry_aerosol_in_air", None, "1")
        STASH_TO_CF["m01s34i102"] = CFName("mass_fraction_of_sulfate_soluble_nucleation_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i103"] = CFName("number_fraction_of_soluble_aitken_mode_dry_aerosol_in_air", None, "1")
        STASH_TO_CF["m01s34i104"] = CFName("mass_fraction_of_sulfate_soluble_aitken_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i105"] = CFName("mass_fraction_of_black_carbon_soluble_aitken_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i106"] = CFName("mass_fraction_of_particulate_organic_matter_soluble_aitken_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i107"] = CFName("number_fraction_of_soluble_accumulation_mode_dry_aerosol_in_air", None, "1")
        STASH_TO_CF["m01s34i108"] = CFName("mass_fraction_of_sulfate_soluble_accumulation_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i109"] = CFName("mass_fraction_of_black_carbon_soluble_accumulation_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i110"] = CFName("mass_fraction_of_particulate_organic_matter_soluble_accumulation_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i111"] = CFName("mass_fraction_of_seasalt_soluble_accumulation_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i113"] = CFName("number_fraction_of_soluble_coarse_mode_dry_aerosol_in_air", None, "1")
        STASH_TO_CF["m01s34i114"] = CFName("mass_fraction_of_sulfate_soluble_coarse_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i115"] = CFName("mass_fraction_of_black_carbon_soluble_coarse_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i116"] = CFName("mass_fraction_of_particulate_organic_matter_soluble_coarse_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i117"] = CFName("mass_fraction_of_seasalt_soluble_coarse_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i119"] = CFName("number_fraction_of_insoluble_aitken_mode_dry_aerosol_in_air", None, "1")
        STASH_TO_CF["m01s34i120"] = CFName("mass_fraction_of_black_carbon_insoluble_aitken_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i121"] = CFName("mass_fraction_of_particulate_organic_matter_insoluble_aitken_mode_dry_aerosol_in_air", None, "kg kg-1")
        STASH_TO_CF["m01s34i126"] = CFName("mass_fraction_of_particulate_organic_matter_soluble_nucleation_mode_dry_aerosol_in_air", None, "kg kg-1")

        # Section 17: Interactive CLASSIC emissions
        STASH_TO_CF["m01s17i205"] = CFName("tendency_of_atmosphere_mass_content_of_dimethyl_sulfide_due_to_emission_expressed_as_sulfur", None, "kg m-2 s-1")

        # Section 34: UKCA chemistry deposition
        STASH_TO_CF["m01s34i454"] = CFName("tendency_of_moles_of_sulfur_dioxide_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s34i455"] = CFName("tendency_of_moles_of_sulfur_dioxide_due_to_wet_deposition", None, "mol s-1")

        # Section 38: UKCA aerosol primary emissions
        STASH_TO_CF["m01s38i201"] = CFName("tendency_of_moles_of_sulfate_soluble_aitken_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i202"] = CFName("tendency_of_moles_of_sulfate_soluble_accumulation_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i203"] = CFName("tendency_of_moles_of_sulfate_soluble_coarse_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i204"] = CFName("tendency_of_moles_of_seasalt_soluble_accumulation_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i205"] = CFName("tendency_of_moles_of_seasalt_soluble_coarse_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i207"] = CFName("tendency_of_moles_of_black_carbon_insoluble_aitken_mode_dry_aerosol_due_to_emission", None, "mol s-1")
        STASH_TO_CF["m01s38i209"] = CFName("tendency_of_moles_of_particulate_organic_matter_insoluble_aitken_mode_dry_aerosol_due_to_emission", None, "mol s-1")

        # Section 38: UKCA aerosol dry deposition
        STASH_TO_CF["m01s38i214"] = CFName("tendency_of_moles_of_sulfate_soluble_nucleation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i215"] = CFName("tendency_of_moles_of_sulfate_soluble_aitken_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i216"] = CFName("tendency_of_moles_of_sulfate_soluble_accumulation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i217"] = CFName("tendency_of_moles_of_sulfate_soluble_coarse_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i218"] = CFName("tendency_of_moles_of_seasalt_soluble_accumulation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i219"] = CFName("tendency_of_moles_of_seasalt_soluble_coarse_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i220"] = CFName("tendency_of_moles_of_black_carbon_soluble_aitken_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i221"] = CFName("tendency_of_moles_of_black_carbon_soluble_accumulation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i222"] = CFName("tendency_of_moles_of_black_carbon_soluble_coarse_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i223"] = CFName("tendency_of_moles_of_black_carbon_insoluble_aitken_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i224"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_nucleation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i225"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_aitken_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i226"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_accumulation_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i227"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_coarse_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")
        STASH_TO_CF["m01s38i228"] = CFName("tendency_of_moles_of_particulate_organic_matter_insoluble_aitken_mode_dry_aerosol_due_to_dry_deposition", None, "mol s-1")

        # Section 38: UKCA aerosol in-cloud wet deposition
        STASH_TO_CF["m01s38i237"] = CFName("tendency_of_moles_of_sulfate_soluble_nucleation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i238"] = CFName("tendency_of_moles_of_sulfate_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i239"] = CFName("tendency_of_moles_of_sulfate_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i240"] = CFName("tendency_of_moles_of_sulfate_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i241"] = CFName("tendency_of_moles_of_seasalt_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i242"] = CFName("tendency_of_moles_of_seasalt_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i243"] = CFName("tendency_of_moles_of_black_carbon_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i244"] = CFName("tendency_of_moles_of_black_carbon_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i245"] = CFName("tendency_of_moles_of_black_carbon_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i246"] = CFName("tendency_of_moles_of_black_carbon_insoluble_aitken_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i247"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_nucleation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i248"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i249"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i250"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i251"] = CFName("tendency_of_moles_of_particulate_organic_matter_insoluble_aitken_mode_dry_aerosol_due_to_wet_deposition_in_cloud", None, "mol s-1")

        # Section 38: UKCA aerosol below-cloud wet deposition
        STASH_TO_CF["m01s38i261"] = CFName("tendency_of_moles_of_sulfate_soluble_nucleation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i262"] = CFName("tendency_of_moles_of_sulfate_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i263"] = CFName("tendency_of_moles_of_sulfate_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i264"] = CFName("tendency_of_moles_of_sulfate_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i265"] = CFName("tendency_of_moles_of_seasalt_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i266"] = CFName("tendency_of_moles_of_seasalt_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i267"] = CFName("tendency_of_moles_of_black_carbon_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i268"] = CFName("tendency_of_moles_of_black_carbon_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i269"] = CFName("tendency_of_moles_of_black_carbon_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i270"] = CFName("tendency_of_moles_of_black_carbon_insoluble_aitken_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i271"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_nucleation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i272"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_aitken_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i273"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_accumulation_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i274"] = CFName("tendency_of_moles_of_particulate_organic_matter_soluble_coarse_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")
        STASH_TO_CF["m01s38i275"] = CFName("tendency_of_moles_of_particulate_organic_matter_insoluble_aitken_mode_dry_aerosol_due_to_wet_deposition_below_cloud", None, "mol s-1")

        # Section 38: UKCA CCN concentrations
        STASH_TO_CF["m01s38i437"] = CFName(None, "condensation_nuclei_number_concentration", "cm-3")
        STASH_TO_CF["m01s38i438"] = CFName(None, "cloud_condensation_nuclei_number_concentration_accumulation_plus_coarse_modes", "cm-3")
        STASH_TO_CF["m01s38i439"] = CFName(None, "cloud_condensation_nuclei_number_concentration_accumulation_plus_coarse_plus_aitken_gt_25r_modes", "cm-3")
        STASH_TO_CF["m01s38i440"] = CFName(None, "cloud_condensation_nuclei_number_concentration_accumulation_plus_coarse_plus_aitken_gt_35r_modes", "cm-3")
        STASH_TO_CF["m01s38i441"] = CFName(None, "cloud_droplet_numer_number_concentration", "cm-3")

        STASH_TO_CF["m01s38i484"] = CFName(None, "cloud_condensation_nuclei_number_concentration_at_fixed_supersaturation", "m-3")
        # This looks 3D but the vertical dimension actually represents different levels of supersaturation.
        # Model saturation levels, lowest model level will be lowest supersaturation:
        saturation_levels = [0.02, 0.04, 0.06, 0.08,
                             0.1,  0.16, 0.2,  0.23,
                             0.3,  0.33, 0.38, 0.4,
                             0.5,  0.6,  0.75, 0.8,
                             0.85, 1.0, 1.2]

        # Section 38: UKCA Partial volume conctrations
        STASH_TO_CF["m01s38i446"] = CFName(None, "partial_volume_concentration_of_sulfate_soluble_aitken_mode", "1")

        # Section 50: UKCA standard diagnostic. Probably Kg, but I've not double checked.
        # These are mostly used in non-hydrostatic cases. An alternative is to use density of air, either directly or
        # as calculated by pressure and temperature. I'd also need to check if these are dry or wet air...
        STASH_TO_CF["m01s50i061"] = CFName(None, "tropospheric_mass_of_air", "kg")
        STASH_TO_CF["m01s50i063"] = CFName(None, "mass_of_air", "kg")

