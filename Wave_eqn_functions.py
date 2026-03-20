import numpy as np

#red region/linear shock wave bit---------------

def shock_wave_linear(t,rho_in,D,t_RL):
    '''
    This function is designed to model the initial linear portion of the shockwave.
    Input variables:
    t - time since the system began
    rho_in - the constant input density growing the shockwave

    Input constants:
    D - the position of the redlight in space
    t_RL - the time when the redlight begins
    '''

    #This is the shockwave velocity eqn
    s = -rho_in
    #the eqn treats v-max as 1 and rho-max as 1 so rho_in needs to be a fraction of total density possible
    #and velocity does as well.
    x_SW = D + s*(t - t_RL)

    return x_SW

def variable_shockwave(fan1_equations, D2, t_RL2, dt=0.1):
    '''
    This function is for the second light and recalcualtes the shockwave everytime it hits a fan arm as s
    changes with the incoming traffic density.

    Input Variables:
    fan1_equations - the gradient and intercept of the initial green fan from the first light

    Input constants:
    D2 - the position of the second traffic light in x
    t_RL2 - time of the second red light. 

    '''
    t_current = t_RL2
    x_current = D2
    shock_path = [[x_current, t_current]]
    
    # We loop until the shock disappears or we hit a max time
    while x_current < D2 + 5: # Small buffer
        # 1. Find which fan ray is currently at (x_current, t_current)
        # For each ray: t = m*x + c  => m = (t-c)/x
        # We find the ray whose density corresponds to the local slope
        
        # Approximate local density rho_f from the fan geometry:
        # v = x / (t - t_G1)
        # rho_f = (1 - v) / 2
        v_local = x_current / (t_current - t_G1) 
        rho_f = (1 - v_local) / 2
        
        # 2. Variable shock speed
        s_variable = -rho_f
        
        # 3. Step forward in time (actually moving backward in x)
        x_current += s_variable * dt
        t_current += dt
        
        shock_path.append([x_current, t_current])
        
        if t_current > t_max: break
        
    return np.array(shock_path)


#greenwave fan and combined wavefront bit-------------------


def green_wave_fan(rho_in, t_G1, number_of_segements_of_fan):
    '''
    This function plots the greenwave fan, this should only be applied to the data once the vehicles
    have passed the initial wavefront.

    This function returns an array containing the coeff and intercepts necessary to plot each part of the fan
    it depends only on the incoming density of traffic and the number of segments that are wanted.

    Input variables:
    rho_in - the initial traffic density
    
    Input constants:
    t_G1 - time when the gren light begins i.e. fan origin
    number_of_segments_of_fan - literally how many arms do you want on the fan
    
    '''
    # The fan covers densities from 0 (front) to rho_initial (back)
    densities = np.linspace(0, rho_in, number_of_segements_of_fan)
    
    fan_equations = []
    
    for rho_f in densities:
        # Characteristic speed in dimensionless units
        v_char = 1 - 2 * rho_f
        
        # We only care about forward-moving waves (v > 0)
        # If v = 0, the gradient is infinite (vertical line)
        if v_char <= 0:
            continue
            
        # The equation is: (t - t_G1) = (1/v_char) * (x - 0)
        # Therefore: t = (1/v_char) * x + t_G1
        gradient = 1 / v_char
        intercept = t_G1
        
        fan_equations.append([gradient, intercept])
        #this gradient is taken to have t on y axis and position-x on the x-axis
    
    return np.array(fan_equations) # Returns an array of lists where each list has a gradient and intercept of that fan line

def combined_wave_front(t, rho_in,D,t_RL,t_G):
    '''
    This function defines the 'blue' or curved wavefront for the traffic light, after the shock wave has hit
    the greenwave fan.

    Input variables:
    t-time from the scenario's start
    rho_in - density of the incoming traffic

    Input constants:
    D- position of light
    t_RL- time of the red light
    t_G - time of green light

    '''
    #shockwave velocity (before combined)
    s = (rho_in - rho_in**2)/(rho_in - 1)
    #full formula as a function of position vs time
    x_comb = (1-2*rho_in)*(t-t_G)+D-2*(1-rho_in)*np.sqrt((s*(t_RL-t_G)*(t-t_G))/(1+s))

    return x_comb
