from Wave_eqn_functions import green_wave_fan, variable_shockwave, variable_dissipation_curve
import numpy as np
import matplotlib.pyplot as plt
#--------------------------------------------------------------------
# VARIABLES 
rho_initial = 0.52      # Density approaching Light 1 (0 to 1)
num_fan_segments = 1000 # Resolution of the traffic flow fan out of the first light

# Light 1 
pos_L1 = 0  # x-position of light
t_red_start_L1 = 0 # Start of first red cycle
t_red_dur_L1 = 5   # Duration of red
t_green_start_L1 = t_red_start_L1 + t_red_dur_L1 #when it turns green

# Light 2 
pos_L2 = 30  # x-position of light
t_red_start_L2 = 25  # When light 2 turns red
t_red_dur_L2 = 15  # How long Light 2 stays red
t_green_start_L2 = t_red_start_L2 + t_red_dur_L2 # when it turns green
#--------------------------------------------------------------------


#-------------------------------------------------------------------
#how to use the functions

#Generate the "Arrival Traffic" from Light 1
# This creates the fan of varying densities that will hit the next light.
fan1_data = green_wave_fan(
    rho_in = rho_initial, 
    t_start = t_green_start_L1, 
    D = pos_L1, 
    n = num_fan_segments
)
# a shockwave function also exist for use but this is all that is needed for the second light

# Input the fan data and Light 2's red timing.
# This returns the linear segments of the shockwave moving UPSTREAM.
shock_segments = variable_shockwave(
    rho_in = rho_initial, 
    fan_eqs = fan1_data, 
    D2 = pos_L2, 
    t_RL2 = t_red_start_L2, 
    d_RL2 = t_red_dur_L2
)
#this MUST come before the use of the next function

# Input the end of the red shock and the fan data again.
# This returns the curved dissipation line when the two green lights and shockwave interact
dissipation_points = variable_dissipation_curve(
    shock_segments = shock_segments, 
    fan1_equations = fan1_data, 
    D2 = pos_L2, 
    t_RL2 = t_red_start_L2, 
    d_RL2 = t_red_dur_L2
)
#function higherarchy:
#[green_wave_fan]  <- depends only on input variables/constants stated up top
#       |
#       +----> [variable_shockwave]  <- depends on fan1 data and the stuff uptop
#       |               |          
#       +---------------+----> [variable_dissipation_curve]  <- depends on the shockwave output and fan 1
#                                                               and the values stated uptop
#[shock_wave_linear] <- shock wave func for the simple case i.e. first light where it is just linear
#
#[combined_wave_front] <- like with the linear shockwave this is the simple constant density curve case
#--------------------------------------------------------------------------