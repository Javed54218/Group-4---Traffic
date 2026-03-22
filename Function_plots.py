import numpy as np
import matplotlib.pyplot as plt
from Wave_eqn_functions import green_wave_fan, shock_wave_linear, combined_wave_front, variable_shockwave


#-----define variables-------------
'''maths uses dimensionless quantities so careful with units
velocity and density are defined as fractions of the total velocity and density'''

#universal variables: --------------
rho_initial = 0.3 # initial density entering the system, i.e. approaching the first set of lights
no_cycles = 3 #number of cycles we graph/consider

#traffic light set 1 variables: ---------------
position_of_1 = 40 # position of the first set of traffic lights
t_RL_interval_1 = 20 # time between when the red light hits
t_RL_length_1 = 20 # time that the light is red for
'''time when the green light occurs, is defined as the the time the redlight occurs at plus one interval of time
defines as the RL_length (redlight length)'''

#traffic light set 2: --------------
position_of_2 = position_of_1 + 25 # position of the second set of traffic lights
# added 225 as the real distance in metres measured on google maps, can change. REVERTED
#VARIABLE SHOCKWAVE DOES NOT WORK WITH LARGE DISTANCES
t_RL_interval_2 = 20 # time between when the red light hits
t_RL_length_2 = 20 # time that the light is red for
t_offset_2 = 10 #time offset between the first light red and second light red
'''time when the green light occurs, is defined as the the time the redlight occurs at plus one interval of time
defines as the RL_length (redlight length)'''


#----------------------------------


#-----function combination---------
#assuming we start from the beginning of the first light then the functions are plotted as such

red_light_start_times_1 = []
for i in range(0, no_cycles):
    red_light_start_times_1.append(0+i*(t_RL_interval_1+t_RL_length_1))#takes the position of the first light and iterates over it for multiples cycles to find the times of the red lights
    # the next redlight occurs after one red light length plus the red gap.

red_light_start_times_1 = np.array(red_light_start_times_1)#converting to numpy array to use change if needed
#now, using the redlight start times the end times can then be found by simply adding one redlight length to each
red_light_end_times_1 = red_light_start_times_1 + t_RL_length_1

#we now have two lists, one of when each redlight begins, and when each redlight ends
#the linear shock function needs to be found between the first arm of the green light fan and the redlight start time.
#to find this use the


#second traffic light:
red_light_start_times_2 = []
for i in range(0,no_cycles):
    red_light_start_times_2.append(t_offset_2+i*(t_RL_interval_2+t_RL_length_2))#takes the position of the first light and iterates over it for multiples cycles to find the times of the red lights
    # the next redlight occurs after one red light length plus the red gap.

#now, using the redlight start times the end times can then be found by simply adding one redlight length to each
red_light_start_times_2 = np.array(red_light_start_times_2) # converting to numpy array
red_light_end_times_2 = red_light_start_times_2 + t_RL_length_2


#----------plotting----------------

def plot_linear(position, start_red, end_red, rho_initial,
                shock_function, ax):
    '''
    This function just plots the red light, green light and linear wave sections
    over the time of a red light.
    Input variables:
    shock_function - this is the shock function being plotted, could work with other
                     equations with some adapting perhaps.
    Input constants:
    position - position in space of light
    start_red - time the light turns red
    end_red - time the stops being red
    rho_initial - density goinng into the function
    '''

    # iterates over each cycle
    for i in range(len(start_red)):
        ax.vlines(position, start_red[i], end_red[i], colors='red') # red line for red light
        time = np.linspace(start_red[i], end_red[i], 50) # creates a time array over red
        linear_wave = shock_function(time, rho_initial, position, start_red[i])
        ax.plot(linear_wave, time, color='blue') # blue linear shock

    ax.axvline(position, color='green', alpha=0.3) # faint green line when green
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Time (s)')


def plot_fan(position, end_red, rho_initial,
                shock_function, ax):
    '''
    This function plots the green wave fan for one green light

    Input variables:
    shock_function - just the green wave fan from wave_eqn-functions
    rho_initial - density goinng into the function

    Input constants:
    position - position in space of light
    end_red - time the stops being red
    '''

    no_arms = 100 # this is just the number of fan arms, can be altered
    time = np.linspace(end_red, (end_red + 30)) # creates a time array over green
    #unsure when it should end, use 30 sec after for now
    fan = shock_function(rho_initial,
                         end_red,
                         position,
                         no_arms
                         )
    # iterates over each arm
    for i in range(len(fan)):
        gradient = fan[i][0]
        intercept = fan[i][1]

        # x = (t - intercept) / gradient
        #rearrange because green fan gives gradient for flipped axis
        fan_line = (time - intercept) / gradient
        #plot the arms as faint grey lines
        ax.plot(fan_line, time, color="gray", alpha = 0.3)

    return fan

fig, ax = plt.subplots() #creating the axis to use plot on

#plotting liner for the first set of lights
plot_linear(position_of_1,
            red_light_start_times_1,
            red_light_end_times_1,
            rho_initial,
            shock_wave_linear,
            ax)


#first fan after first green light at first light
plot_fan(position_of_1,
         red_light_end_times_1[0],
         rho_initial,
         green_wave_fan,
         ax)

plt.show()

#--------function output sanity check----------
#ignore this i just use it to check the functions
#will delete when everything works

fan1_data = green_wave_fan(
    rho_initial,
    red_light_start_times_1[0] ,
    position_of_1,
    15
)

shock_segments = variable_shockwave(
    rho_initial = rho_initial,
    fan1_equations = fan1_data,
    D2 = position_of_2,
    t_RL2 = red_light_start_times_2[0] ,
    d_RL2 = t_RL_interval_2
)

plt.show()
print(fan1_data)
print(shock_segments)

t = np.linspace(red_light_end_times_1[0], red_light_start_times_1[1], 50)


#print(fan1_data)
combined_wave_front(t, rho_initial, position_of_1, red_light_start_times_1[0], red_light_end_times_1[0])

#original how to use, get apostrophes for clarity
#variable names are different in the guide, i may change them in the original code

'''
#-------------------------------------------------------------------
#how to use the functions

#Generate the "Arrival Traffic" from Light 1
# This creates the fan of varying densities that will hit the next light.
fan1_data = green_wave_fan(
    rho_in = rho_initial,
    t_G1 = t_green_start_L1,
    D = pos_L1,
    number_of_segements_of_fan = num_fan_segments
)
# a shockwave function also exist for use but this is all that is needed for the second light

# Input the fan data and Light 2's red timing.
# This returns the linear segments of the shockwave moving UPSTREAM.
shock_segments = variable_shockwave(
    rho_initial = rho_initial,
    fan1_equations = fan1_data,
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
'''

