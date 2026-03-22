import numpy as np

#---------------red region/linear shock wave bit---------------

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

def variable_shockwave(rho_initial, fan1_equations, D2, t_RL2, d_RL2):
    '''
    This function is for the second light and recalculates the shockwave everytime it hits a fan arm as s
    changes with the incoming traffic density.

    Input Variables:
    fan1_equations - the gradient and intercept of the initial green fan arms from the first light
    rho_initial - the density of the initial traffic when it hits the second light,
    this is variable as it could be traffic that missed the first light or traffic that hit the first light, it depends.


    Input constants:
    D2 - the position of the second traffic light in x
    t_RL2 - time of the second red light. 
    d_RL2 - length of the second red light, i.e. how long after t_RL2 does the greenlight occur.

    '''
    t_current = t_RL2#start the clock at t_current for the second red light
    x_current = D2# position in space where we start the clock for the second red light
    t_GL2 = t_RL2 + d_RL2#time when the light turns green, i.e. the new fan starts
    shock_path = [[x_current, t_current]]#a list to store x and y points of the back of the queue
    current_s = -rho_initial # defines intial gradient for the shock wave
    #so it can be plotted later
    
    # Filter for positive gradients (v_char > 0) 
    # This keeps arms that move forward in x and t.
    valid_fan_arms = [arm for arm in fan1_equations if arm[0] >= 0]

    # First arm of the second green fan (The Dissipation Signal)
    first_arm_second_green_gradient = -1
    first_arm_second_green_intercept = t_GL2 - (first_arm_second_green_gradient*D2)
    

    shock_segments = []
    arm_index = 0
    active = True

    while active and arm_index < len(valid_fan_arms):
        m_fan, c_fan = valid_fan_arms[arm_index]
        if current_s == 0:
            # The shockwave is a vertical line: x = x_current
            # Solves for where the fan arm t = m_fan * x + c_fan hits this x
            x_fan_int = x_current
            t_fan_int = m_fan * x_fan_int + c_fan
            
            # Solve for where the dissipation signal hits this x
            # t = m_diss * x + c_diss
            x_diss = x_current
            t_diss = first_arm_second_green_gradient * x_diss + first_arm_second_green_intercept
            
            # Since s=0, the segment doesn't have a standard m_shock/c_shock
            # We can use a very large number for m_shock to represent 'vertical'
            m_shock = -1e12 
            c_shock = t_current - (m_shock * x_current)
        else:
            # --- Your existing Linear Math ---
            m_shock = 1 / current_s
            c_shock = t_current - (m_shock * x_current)
            
            x_fan_int = (c_fan - c_shock) / (m_shock - m_fan)
            t_fan_int = m_shock * x_fan_int + c_shock
            
            x_diss = (first_arm_second_green_intercept - c_shock) / (m_shock - first_arm_second_green_gradient)
            t_diss = m_shock * x_diss + c_shock
            if t_fan_int <= t_current + 1e-6: t_fan_int = float('inf')
            if t_diss <= t_current + 1e-6: t_diss = float('inf')


        if t_diss <= t_fan_int:
            # The green signal from L2 is the SOONEST event. 
            # Record final segment and BREAK.
            shock_segments.append([m_shock, c_shock, t_current, t_diss, x_current, x_diss])
            active = False
        else:
            # The Fan 1 arm is hit first. Record this segment.
            shock_segments.append([m_shock, c_shock, t_current, t_fan_int, x_current, x_fan_int])
            
            # Update starting point for the next segment
            x_current = x_fan_int
            t_current = t_fan_int
            
            # Reverse engineer density from the arm after the one just hit
            if arm_index + 1 < len(valid_fan_arms):
                next_m_fan, _ = valid_fan_arms[arm_index + 1]
                # rho = (1 - 1/m) / 2
                new_rho = (1 - (1 / next_m_fan)) / 2
            else:
                # If no more arms, use the density of the current arm
                new_rho = (1 - (1 / m_fan)) / 2
            
            current_s = -new_rho
            arm_index += 1

    return np.array(shock_segments)



#----------greenwave fan bit-------------------


def green_wave_fan(rho_in, t_G1, D, number_of_segements_of_fan):
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
    densities = np.linspace(0,1.0, number_of_segements_of_fan)
    
    fan_equations = []
    
    for rho_f in densities:
        # Characteristic speed in dimensionless units
        v_char = 1 - 2 * rho_f
        
        # Avoid true division by zero for the vertical arm
        if np.abs(v_char) < 1e-10:
            gradient = 1e12 # Represents a vertical line
        else:
            gradient = 1 / v_char
            
        intercept = t_G1 - (gradient * D)
        fan_equations.append([gradient, intercept])
    
    return np.array(fan_equations) # Returns an array of lists where each list has a gradient and intercept of that fan line



#-------combined wavefront bit----------------------


#combined waves for first and second lights
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
    s = -rho_in
    #full formula as a function of position vs time
    x_comb = (1-2*rho_in)*(t-t_G)+D-2*(1-rho_in)*np.sqrt((s*(t_RL-t_G)*(t-t_G))/(1+s))

    return x_comb

def variable_dissipation_curve(shock_segments, fan1_equations, D2, t_RL2, d_RL2):
    '''This function is the worst one as it accounts for how the shockwave decays,
    depending on the incoming density.

    Input variables:
    shock_segments - the segments of the 'red' shock wave before it hits the second green fan
    fan1_equations - the equations for the first fan as a variable density

    Input constants:
    D2 - position of the second light
    t_RL2 - time the redlight occurs at
    d_RL2 - duration of the red light (i.e. the time from red to green)
    '''
    last_seg = shock_segments[-1]#finds the last entry in the list (last point on the red shock wave)
    t_current, x_current = last_seg[3], last_seg[5] # Point where linear shock hit the green signal
    t_GL2 = t_RL2 + d_RL2#defines the time when the green light occured
    
    valid_fan_arms = sorted(fan1_equations, key=lambda x: x[0])
    #sorts fans so that the shockwave hits the correct arm on the second fan first
    
    # determines which arm the shockwave is currently on
    distances = [abs((m * x_current + c) - t_current) for m, c in valid_fan_arms]
    arm_index = distances.index(min(distances))#takes the arm closest to it out of the valid arms
    
    curve_points = [[x_current, t_current]]# plots the first set of points as where the red curve ends

    while arm_index < len(valid_fan_arms):
        m_f, c_f = valid_fan_arms[arm_index]#determines the first arm hit
        
        # Updates the incoming density based on the arm from the first traffic light
        rho_in = (1 - (1 / m_f)) / 2 if abs(m_f) > 1e-6 else 0.5
        
        # Recalculates K for this specific segment to maintain continuity
        # Solves: x_current = D2 + (1-2*rho_in)*(t_current - t_GL2) + K*sqrt(t_current - t_GL2)
        dt = t_current - t_GL2
        if dt <= 0: # Safety for points exactly at the green light trigger
            K = 0   #This is unphysical so shouldnt happen though, its just a safety 'if'
        else:
            K = (x_current - D2 - (1 - 2 * rho_in) * dt) / np.sqrt(dt)
            #calculates k

        # Find the intersection with the next fan arm
        # Intersection of: x = D2 + (1-2*rho_in)(t-t_GL2) + K*sqrt(t-t_GL2)
        # and Fan Arm: x = (t - c_f) / m_f
        
        v_diff = (1 - 2 * rho_in) - (1 / m_f)
        constant_part = D2 - (c_f / m_f) + (t_GL2 / m_f) - (1 - 2 * rho_in) * t_GL2 # This is simplified
        
        # It is easier to solve in terms of u = sqrt(t - t_GL2)
        # Let u = sqrt(t - t_GL2). Then t = u^2 + t_GL2
        # (u^2 + t_GL2 - c_f)/m_f = D2 + (1-2*rho_in)u^2 + K*u
        
        A = (1 / m_f) - (1 - 2 * rho_in)
        B = -K
        C = (t_GL2 - c_f) / m_f - D2
        
        discriminant = B**2 - 4 * A * C #discriminant
        
        if discriminant < 0 or abs(A) < 1e-12:
            # If no intersection, this curve segment lasts "forever" or is where it dissipates
            t_final = t_current + 10
            # Just add a few points for the plot and exit
            ts = np.linspace(t_current, t_final, 20)
            for t in ts[1:]:
                u = np.sqrt(t - t_GL2)
                x_t = D2 + (1 - 2 * rho_in) * (t - t_GL2) + K * u
                curve_points.append([x_t, t])#zooms in and plots 20 final points before it ends
            break

        # Solve for u, then t_hit
        u_roots = [(-B + np.sqrt(discriminant)) / (2 * A), (-B - np.sqrt(discriminant)) / (2 * A)]
        valid_u = [u for u in u_roots if u > np.sqrt(dt) + 1e-6]
        #1e-6 is a tiny buffer value to prevent errors from rounding
        #only car about solutions where the time is after the current time
        if not valid_u:
            arm_index += 1
            continue #if it doesnt hit this arm it checks the next
        
        t_hit = min(valid_u)**2 + t_GL2
        x_hit = (t_hit - c_f) / m_f #
        
        # Stores points for this segment (Smooths out the curve)
        segment_ts = np.linspace(t_current, t_hit, 10)
        for t in segment_ts[1:]:
            u = np.sqrt(t - t_GL2)
            x_t = D2 + (1 - 2 * rho_in) * (t - t_GL2) + K * u
            curve_points.append([x_t, t])
            
        # Advance to next state/ segment region
        t_current, x_current = t_hit, x_hit
        arm_index += 1
        
        if x_current >= D2: # Queue cleared, it is cut here as we dont care about after the second light
            break

    return np.array(curve_points)