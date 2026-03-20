from Wave_eqn_functions import green_wave_fan, shock_wave, combined_wave_front

#-----define variables-------------
'''maths uses dimensionless quantities so careful with units
velocity and density are defined as fractions of the total velocity and density'''

#universal variables: --------------
rho_initial = 0.3 # initial density entering the system, i.e. approaching the first set of lights

#traffic light set 1 variables: ---------------
position_of_1 = 4 # position of the first set of traffic lights
t_RL_interval_1 = 5 # time between when the red light hits
t_RL_length_1 = 1 # time that the light is red for
'''time when the green light occurs, is defined as the the time the redlight occurs at plus one interval of time
defines as the RL_length (redlight length)'''

#traffic light set 2: --------------
position_of_2 = 4 # position of the second set of traffic lights
t_RL_interval_2 = 5 # time between when the red light hits
t_RL_length_2 = 1 # time that the light is red for
'''time when the green light occurs, is defined as the the time the redlight occurs at plus one interval of time
defines as the RL_length (redlight length)'''

#----------------------------------


#-----function combination---------
#assuming we start from the beginning of the first light then the functions are plotted as such

#first traffic light:
red_light_start_times_1 = []
for i in range(0,6):
    red_light_start_times_1.append(0+i*(t_RL_interval_1+t_RL_length_1))#takes the position of the first light and iterates over it for multiples cycles to find the times of the red lights
    # the next redlight occurs after one red light length plus the red gap. 

#now, using the redlight start times the end times can then be found by simply adding one redlight length to each
red_light_end_times_1 = red_light_start_times_1 + t_RL_length_1

#we now have two lists, one of when each redlight begins, and when each redlight ends
#the linear shock function needs to be found between the first arm of the green light fan and the redlight start time. 
#to find this use the 


#second traffic light:
red_light_start_times_2 = []
for i in range(0,6):
    red_light_start_times_2.append(0+i*(t_RL_interval_2+t_RL_length_2))#takes the position of the first light and iterates over it for multiples cycles to find the times of the red lights
    # the next redlight occurs after one red light length plus the red gap. 

#now, using the redlight start times the end times can then be found by simply adding one redlight length to each
red_light_end_times_2 = red_light_start_times_1 + t_RL_length_2