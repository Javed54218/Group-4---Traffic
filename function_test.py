import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll
from Wave_eqn_functions import green_wave_fan, shock_wave_linear, variable_shockwave
from Wave_eqn_functions import variable_dissipation_curve, L1_shock_curves

# --- 1. USER INPUTS (REAL WORLD UNITS) ---
V_MAX_REAL = 15.0       # Speed limit in meters per second (m/s)
RHO_JAM_REAL = 0.12     # Jam density in vehicles per meter (veh/m)
FLUX_IN = 0.15          # Arrival rate in vehicles per second (veh/s)

# Universal variables (Keeping your names)
no_cycles = 3 

# Traffic Light Set 1
position_of_1 = 40.0     # Position in METERS
t_RL_interval_1 = 40.0   # Time between the start of one red light and the next (SEC)
t_RL_length_1 = 20.0     # Duration the light stays red (SEC)

# Traffic Light Set 2
position_of_2 = position_of_1 + 250 
t_RL_interval_2 = 40.0   
t_RL_length_2 = 20.0     
t_offset_2 = 10.0        # Time delay between L1 red and L2 red (SEC)

# --- 2. THE CONVERSION CALCULATIONS ---

def get_rho_from_flux(q, v_max, r_max):
    """Solves the Greenshields quadratic for density."""
    q_max = 0.25 * v_max * r_max
    if q > q_max: q = q_max
    # Standard quadratic solution for rho (uncongested root)
    disc = v_max**2 - (4 * v_max * q / r_max)
    return ((v_max - np.sqrt(disc)) / (2 * v_max / r_max)) / r_max

# Derived Model Density (Dimensionless fraction 0.0 to 1.0)
rho_initial = get_rho_from_flux(FLUX_IN, V_MAX_REAL, RHO_JAM_REAL)

# Scaled Positions (Math requires x_model = meters / V_MAX)
# This ensures the "Free Flow" speed in your math equals 1.0
D1 = position_of_1 / V_MAX_REAL
D2 = position_of_2 / V_MAX_REAL

# Timing Lists (Seconds are fine as the base unit)
# start_list = when light turns RED
# end_list = when light turns GREEN (start + red_duration)
start_list_1 = [i * t_RL_interval_1 for i in range(no_cycles)]
end_list_1 = [t + t_RL_length_1 for t in start_list_1]

start_list_2 = [t + t_offset_2 for t in [i * t_RL_interval_2 for i in range(no_cycles)]]
end_list_2 = [t + t_RL_length_2 for t in start_list_2]
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

#second traffic light:
red_light_start_times_2 = []
for i in range(0,no_cycles):
    red_light_start_times_2.append(t_offset_2+i*(t_RL_interval_2+t_RL_length_2))#takes the position of the first light and iterates over it for multiples cycles to find the times of the red lights
    # the next redlight occurs after one red light length plus the red gap.

#now, using the redlight start times the end times can then be found by simply adding one redlight length to each
red_light_start_times_2 = np.array(red_light_start_times_2) # converting to numpy array
red_light_end_times_2 = red_light_start_times_2 + t_RL_length_2

# --- PRE-CALCULATION FOR PHYSICS ---
# We need to generate the L1 fan data first so the variable_shockwave can "see" it

light_1_shock_wave_front = L1_shock_curves(rho_initial,position_of_1,red_light_start_times_1,red_light_end_times_1)

fan1_data_list = green_wave_fan( red_light_end_times_1, position_of_1, 50)

# Calculate the complex shockwave buildup at Light 2
shock_segments = variable_shockwave(rho_initial, fan1_data_list, position_of_2, 
                                    red_light_start_times_2, t_RL_length_2, 
                                    position_of_1, red_light_start_times_1)

# Generate the smooth dissipation curves (trajectories)
curves_2 = variable_dissipation_curve(shock_segments, fan1_data_list, position_of_2, 
                                    red_light_start_times_2, t_RL_length_2, rho_initial)

#----------plotting----------------

def plot_L1_full(l1_curves,position, ax):
    '''
    This function just plots the red light, green light and linear wave sections
    over the time of a red light. It now also plots the dissipating curve after the linear shockwave phase
    Input variables:
    shock_function - this is the shock function being plotted, could work with other
                     equations with some adapting perhaps.
    Input constants:
    curves_list- Output from L1_shock_curves
    start_list- red_light_start_times_1
    end_list - red_light_end_times_1
    D1 - position of the first light
    '''
    import matplotlib.collections as mcoll

    for p in l1_curves:
        # 1. Calculate Velocity for coloring (dx/dt)
        dx = np.diff(p[:, 0])
        dt = np.diff(p[:, 1])
        # Avoid division by zero for the vertical 'red light' parts
        velocities = np.where(dt > 1e-9, dx/dt, 0)
        
        # Creates segments using the 'stack' method to avoid the (4,) shape error
        segments = np.stack([p[:-1], p[1:]], axis=1)

        # Creates and add the collection
        lc = mcoll.LineCollection(segments, cmap='RdYlGn', linewidths=2.5, zorder=4)
        lc.set_array(velocities)
        lc.set_clim(vmin=0, vmax=1.0)
        
        ax.add_collection(lc)

    

    ax.axvline(position, color='green', alpha=0.3) # faint green line when green
    ax.set_xlabel('Position (m)')
    ax.set_ylabel('Time (s)')


def plot_fan(position,end_times, rho_initial, fan_data_list, ax, target_pos):
    '''
    This function plots the green wave fan for all green lights now using the edited
    beckend function which uses a list.

    Input variables:
    shock_function - just the green wave fan from wave_eqn-functions
    rho_initial - density goinng into the function

    Input constants:
    position - position in space of light
    end_red - time the light stops being red
    '''

    no_arms = 30 # this is just the number of fan arms, can be altered
    #unsure when it should end, use 30 sec after for now
    for end_red, fan in zip(end_times,fan_data_list):
        # iterates over each arm
        for arm in fan:
            gradient = arm[0] # m which is dt/dx
            intercept = arm[1] # c

            # x = (t - intercept) / gradient
            #rearrange because green fan gives gradient for flipped axis
            t_arrival = gradient * target_pos + intercept #edited so it stops the fan at the second light
            #plot the arms as faint grey lines
            if t_arrival >= end_red:#only want arms moving forwards in time
                ax.plot([position, target_pos], [end_red, t_arrival], 
                        color="gray", alpha=0.1, lw=0.5)
            #edited the limits so that it plots the fan between the lights

    return fan

def plot_variable_shock(red_light_start_2, red_light_end_2, position_of_2, shock_segments_f):
        # Plot Light 2 Red Bars and the Variable Shockwaves
    for i in range(len(red_light_start_2)):
        ax.vlines(position_of_2, red_light_start_2[i], red_light_end_2[i], colors='red', lw=3)
        # Plotting each segment of the variable shockwave calculated earlier
        for seg in shock_segments_f[i]:#gets the shock segments for plotting
            m_s, t_s, t_e, x_s, x_e = seg
            ax.plot([x_s, x_e], [t_s, t_e], color='red', lw=2)
            ax.scatter(x_e, t_e, color='black', s=12, zorder=5) # Show intersection points


def plot_variable_dissipation_curve(diss_curves, ax):
    import matplotlib.collections as mcoll
    '''
    Takes the list of dissipation boundary values and plots them.
    '''
    for curve in diss_curves:
        if len(curve)< 2:#checks if curve has less than 2 points
            continue
        p = np.asanyarray(curve)#converts to a numpy array
        xs, ts = p[:,0], p[:,1]# extraxcts the x and t coordinates as lists
        dx = np.diff(xs)
        dt = np.diff(ts)#finds differences in x and t between the points for a velocity calculation
        velocities = np.where(dt>1e-9,dx/dt,0)
        segments = np.stack([p[:-1], p[1:]],axis =1)

        lc = mcoll.LineCollection(segments, cmap='RdYlGn', linewidths=2.5, zorder=4)
        #uses mulcticolored to create segments.

        lc.set_array(velocities)#sets colour based off of velocities
        lc.set_clim(vmin=0, vmax=1.0) #sets velocity limits as max and min of 0 and 1
        
        ax.add_collection(lc)#adds the segments to the plot

        #plots black dots to show some points every 40th change
        ax.scatter(xs[::40], ts[::40], color='black', s=4, zorder=5)

#-----main plotting code------------------
fig, ax = plt.subplots(figsize=(11, 8))

# Plot Light 1 full wave and red,light periods
plot_L1_full(light_1_shock_wave_front,position_of_1, ax)

# Plot fans from L1 to L2 for all cycles
plot_fan(position_of_1,red_light_end_times_1, rho_initial, fan1_data_list, ax, position_of_2)

#plots variable shock waves for second light
plot_variable_shock(red_light_start_times_2, red_light_end_times_2, position_of_2, shock_segments)

#plots the variable dissipation for the second light
plot_variable_dissipation_curve(curves_2,ax)

# Final Formatting
ax.axvline(position_of_1, color='green', alpha=0.3) 
ax.set_xlabel('Position (x)')
ax.set_ylabel('Time (t)')#no units yet as waiting on dimensional work 
ax.set_title(f'Integrated Traffic Flow: Offset = {t_offset_2}')
ax.set_xlim(position_of_1 - 30, position_of_2 + 10)#x and y limits
ax.set_ylim(0, red_light_end_times_2[-1] + 50)#sets y limit
plt.grid(True, alpha=0.2)#adds a grid
plt.show()