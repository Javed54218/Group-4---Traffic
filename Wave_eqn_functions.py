import numpy as np
'''edited back end functions, should hopefully work now but the inputs have changed.
 I have done my best and I think it works fine. it is currently 21:30. the best I can do is this. An assumption we make is going to have to be that
 the previous shockwave from a previous redlight at the second set of lights does cannot affect the next red light. its my best effort.'''
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

def variable_shockwave(rho_initial, fan1_equations, D2, t_RL2, d_RL2 , D1, t_RL1):
    """
    Inputs:
    rho_initial[constant]- density entering the system as a whole 
    D2[constant]- position of second traffic light in system
    t_RL2[list]- a list of times for when each successive redlight occurs at L2
    d_RL2[constant]- length of a redlight at L2
    D1[constant]- position of the first light in the system
    t_RL1[list]- list of timings for the red lights in time
    """
    shock_waves_L2 = []
    for i in range(len(t_RL2)):

        #this section is the setup, does the shock hit a previous wave from the last L1 light
        #or does it have free road and miss the last fan
        m_diss = -1.0  # Signal travels backwards into the queue
        t_GL2 = t_RL2[i] + d_RL2
        # t = mx + c  =>  c = t - mx
        c_diss = t_GL2 - (m_diss * D2)
        t_current_RL2 = t_RL2[i]
        idx_above = np.searchsorted(t_RL1, t_current_RL2)

        if idx_above >= len(fan1_equations):
            idx_above = len(fan1_equations) - 1
        found_hit = False
        valid_fan_arms = []
        for offset in [1,2,3]:
            search_idx = idx_above - offset
            if search_idx < 0: continue
            temp_fan = [arm for arm in fan1_equations[search_idx] if arm[0] > 0]
            if not temp_fan: continue
            # Arrival times of THIS temporary fan at D2
            # Arrival = m * D2 + c
            arrival_start = temp_fan[0][0] * D2 + temp_fan[0][1]
            m_gap = 1 / ((1 - 2 * rho_initial)+1e-9)
            c_gap = t_RL1[search_idx] - (m_gap * D1)
            arrival_end = m_gap * D2 + c_gap

            if arrival_start <= t_current_RL2 <= arrival_end:
                # Calculate starting density
                cross_times = [arm[0] * D2 + arm[1] for arm in temp_fan]
                arm_idx = np.searchsorted(cross_times, t_current_RL2) - 1

                m_start = temp_fan[arm_idx][0]
                rho_start = (1 - 1/m_start) / 2
                current_s = -rho_start
                valid_fan_arms = [[arm[0], arm[1], 0] for arm in temp_fan[arm_idx+1:]]
                m_gap = 1 / ((1 - 2 * rho_initial)+1e-9)
                c_gap = t_RL1[search_idx] - (m_gap * D1)
                valid_fan_arms.append([m_gap, c_gap, 1])

                for follow_idx in range(search_idx + 1, len(fan1_equations)):
                    if follow_idx >= len(fan1_equations): 
                        break
                    f_plume = [arm for arm in fan1_equations[follow_idx] if arm[0] > 0]
                    # Add future plume with flag 0
                    valid_fan_arms.extend([[p[0], p[1], 0] for p in f_plume])
                    
                    # Add future gap with flag 1
                    c_f_gap = t_RL1[follow_idx] - (m_gap * D1)
                    valid_fan_arms.append([m_gap, c_f_gap, 1])
                
                found_hit = True
                break

        if not found_hit:
            current_s = -rho_initial
            for follow_idx in range(idx_above, idx_above + 2):
                if follow_idx >= len(fan1_equations): break
                
                f_plume = [arm for arm in fan1_equations[follow_idx] if arm[0] > 0]
                valid_fan_arms.extend([[p[0], p[1], 0] for p in f_plume])
                

                m_gap = 1 / ((1 - 2 * rho_initial)+1e-9)
                c_f_gap = t_RL1[follow_idx] - (m_gap * D1)
                valid_fan_arms.append([m_gap, c_f_gap, 1])


        t_current = t_RL2[i]#start of second red light
        x_current = D2# position of red light
        t_GL2 = t_RL2[i] + d_RL2#time when the light turns green,
        shock_segments = []
        arm_index = 0
        active = True

        while active:
            if arm_index < len(valid_fan_arms):
                m_target, c_target, is_gap = valid_fan_arms[arm_index]
            else:
                # If no more traffic is hitting the queue, it must dissipate or stop growing
                active = False
                break
            if abs(current_s) < 1e-12:
                # Shockwave is vertical (waiting at light or road is empty)
                x_fan_int, t_fan_int = x_current, m_target * x_current + c_target
                x_diss_int, t_diss_int = x_current, m_diss * x_current + c_diss
                m_shock_val = -1e12
            else:
                # Shockwave is diagonal (moving through traffic)
                m_shock = 1 / current_s
                c_shock = t_current - (m_shock * x_current)
                m_shock_val = m_shock
                
                # Intersection with next plume/gap arm
                x_fan_int = (c_target - c_shock) / (m_shock - m_target)
                t_fan_int = m_target * x_fan_int + c_target
                
                # Intersection with dissipation wave
                x_diss_int = (c_diss - c_shock) / (m_shock - m_diss)
                t_diss_int = m_shock * x_diss_int + c_shock
            
            t_clearing_here = m_diss * x_current + c_diss
            if t_current >= t_clearing_here - 1e-7:
                active = False
                break

            # 2. UPDATED: The 'Hit' Logic
            # Check if we hit the green fan BEFORE we hit the next traffic plume
            # AND ensure the hit happens in the future.
            if t_diss_int <= t_fan_int + 1e-7 and t_diss_int > t_current:
                # HIT THE L2 FAN - STOP HERE
                shock_segments.append([m_shock_val, t_current, t_diss_int, x_current, x_diss_int])
                active = False
            elif t_fan_int > t_current:
                shock_segments.append([m_shock_val, t_current, t_fan_int, x_current, x_fan_int])
                
                # 2. UPDATE the "current" position to the intersection point
                x_current, t_current = x_fan_int, t_fan_int
                
                # 3. UPDATE DENSITY (The "Curve" Logic)
                # We use the arm we JUST hit to determine the density behind the shockwave now
                if is_gap == 1:
                    # No more cars; shockwave becomes vertical (infinite slope)
                    current_s = 0 
                else:
                    # Calculate new density from the target arm's slope
                    # rho = (1 - 1/m) / 2
                    new_rho = (1 - (1 / m_target)) / 2
                    current_s = -new_rho
                
                # 4. MOVE to the next arm for the next loop iteration
                arm_index += 1
            else:
                # Safety: If t_fan_int is in the past, move to the next plume arm
                arm_index += 1
                
                arm_index += 1
        shock_waves_L2.append(shock_segments)

    return shock_waves_L2




#----------greenwave fan bit-------------------


def green_wave_fan( t_G1, D, number_of_segements_of_fan):
    '''
    This function plots the greenwave fan, this should only be applied to the data once the vehicles
    have passed the initial wavefront.

    This function returns an array containing the coeff and intercepts necessary to plot each part of the fan
    it depends only on the incoming density of traffic and the number of segments that are wanted.

    Input variables:
    rho_in - the initial traffic density
    
    Input constants:
    t_G1 - list of times when the gren light begins for L1 i.e. fan origins
    number_of_segments_of_fan - literally how many arms do you want on the fan
    
    '''
    # The fan covers densities from 0 (front) to rho_initial (back)
    densities = np.linspace(0,1.0, number_of_segements_of_fan)
    
    fan_equations = []
    fans = []
    for time in t_G1:
        for rho_f in densities:
            # Characteristic speed in dimensionless units
            v_char = 1 - 2 * rho_f
            
            # Avoid true division by zero for the vertical arm
            if np.abs(v_char) < 1e-10:
                gradient = 1e12 # Represents a vertical line
            else:
                gradient = 1 / v_char
                
            intercept = time - (gradient * D)
            fan_equations.append([gradient, intercept])
        fans.append(fan_equations)
        fan_equations = []
    
    return fans # Returns an array of lists where each list has a gradient and intercept of that fan line



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



def variable_dissipation_curve(all_shock_waves, fan1_equations, D2, t_RL2, d_RL2, rho_initial):
    '''
    all_shock_waves- output from the variable shock wave function
    fan1_equations- equations for the fans for the origional set of lights
    D2- position of second light
    t_RL2- time of the second red light changes(list)
    d_RL2-duration of second light's red light
    rho_initial- initial density of the system
    '''
    all_curves = []
    
    for i in range(len(t_RL2)):
        shock_segments = all_shock_waves[i]
        

        if not shock_segments or len(shock_segments) == 0:
            all_curves.append(np.array([]))
            continue 

        end_of_sw = shock_segments[-1]
        x_start, t_start = end_of_sw[4], end_of_sw[2]
        t_GL2 = t_RL2[i] + d_RL2
        

        locked_rho = rho_initial
        found_rho = False
        for cycle_idx in range(len(fan1_equations)):
            for arm in fan1_equations[cycle_idx]:
                if t_start <= (arm[0] * x_start + arm[1]) + 0.1:
                    locked_rho = (1 - (1 / arm[0])) / 2
                    found_rho = True
                    break
            if found_rho: break


        dt_init = max(0.1, t_start - t_GL2)
        K = (x_start - D2 - (1 - 2 * locked_rho) * dt_init) / np.sqrt(dt_init)


        t_steps = np.linspace(t_start, t_start + 700, 1000) 
        curve_points = [[x_start, t_start]]
        
        for t_curr in t_steps[1:]:
            dt_now = t_curr - t_GL2
            

            x_next = D2 + (1 - 2 * locked_rho) * dt_now + K * np.sqrt(dt_now)
            
            # Stop when the line crosses Light 2 (D2)
            if x_next >= D2 - 0.05:
                curve_points.append([D2, t_curr])
                break
                
            if x_next < -100: 
                break
                
            curve_points.append([x_next, t_curr])
        
        all_curves.append(curve_points)
    return all_curves

#----full light 1 boundary function------
def L1_shock_curves(rho_in, D1, start_list, end_list, t_max_limit=140):
    all_curves = []
    s = -rho_in # shock velocity
    
    for i in range(len(start_list)):
        t_RL = start_list[i]
        t_G = end_list[i]
        
        '''#Determines the "Cutoff Time" (the start of the next red light)
        if i + 1 < len(start_list):
            t_stop = start_list[i+1]
        else:
            t_stop = t_max_limit # For the final cycle'''
            
        #Finds the transition time (when shock meets fan)
        t_hit = t_G + (s * (t_RL - t_G)) / (1 + s)
        
        # If the next red light happens before the curve can start, skip/limit
        if t_hit > t_stop:
            t_hit = t_stop

        # Creates the Linear segment (from plot_linear logic)
        t_lin = np.linspace(t_RL, t_hit, 20)
        x_lin = s * (t_lin - t_RL) + D1
        
        #Creates the Curved segment (from combined_wave_front logic)
        # combined_wave_front should be imported or defined in your script
        t_cur = np.linspace(t_hit, t_stop, 100)
        x_cur = combined_wave_front(t_cur, rho_in, D1, t_RL, t_G)

        if i + 1 < len(start_list):
            t_RL_next = start_list[i+1]
            # Next shockwave position
            x_next_shock = (-rho_in) * (t_cur - t_RL_next) + D1
            
            # 1. Add a small 'spatial buffer' (e.g., -2) 
            # This allows the curve to exist slightly behind the 'math' point 
            # before it gets officially truncated.
            collision_mask = x_cur <= (x_next_shock - 2) 
            
            # 2. Only look for collisions AFTER the light turns green
            time_mask = t_cur > (t_G + 1)
            # Place this right after defining collision_mask
            print(f"Cycle {i} | t_G: {t_G:.1f} | First x_cur: {x_cur[0]:.2f} | Next shock at that time: {x_next_shock[0]:.2f} | Collision? {collision_mask[0]}")
            final_mask = collision_mask & time_mask
            if np.any(final_mask):
                stop_idx = np.where(final_mask)[0][0]
                t_cur = t_cur[:stop_idx]
                x_cur = x_cur[:stop_idx]
        
        #Joins them into a single trajectory
        full_x = np.concatenate([x_lin, x_cur])
        full_t = np.concatenate([t_lin, t_cur])
        
        all_curves.append(np.column_stack([full_x, full_t]))

        '''if len(t_cur) > 0 and x_cur[-1] < D1:
            # Physical meaning: The intersection is saturated.
            # Increase the density for the NEXT cycle because traffic is backed up.
            current_rho = min(0.9, current_rho + 0.1) 
        else:
            # It cleared! Reset to initial density.
            current_rho = rho_in'''
        
    return all_curves