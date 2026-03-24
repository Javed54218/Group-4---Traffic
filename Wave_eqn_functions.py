import numpy as np
'''edited back end functions, should hopefully work now but the inputs have changed.
 I have done my best and I think it works fine. it is currently 21:30. the best I can do is this. An assumption we make is going to have to be that
 the previous shockwave from a previous redlight at the second set of lights does cannot affect the next red light. its my best effort.'''
#---------------red region/linear shock wave bit---------------
#-culling test---
def cull_overlapping_segments(all_shock_waves, new_cycle_start_t, position_D2):
            m_diss = -1.0 
            new_c_diss = new_cycle_start_t - (m_diss * position_D2)
            
            for cycle_idx in range(len(all_shock_waves)):
                segments = all_shock_waves[cycle_idx]
                hit_idx = -1
                
                for i, seg in enumerate(segments):
                    m_s, t_s, t_e, x_s, x_e = seg
                    
                    # Intersection math
                    denom = (m_s - m_diss)
                    if abs(denom) < 1e-9: continue
                    
                    t_int = (x_s * m_s * m_diss - t_s * m_diss - new_c_diss * m_s) / denom
                    
                    if t_s <= t_int < t_e:
                        # 1. Update this specific segment
                        seg[2] = t_int 
                        seg[4] = x_s + (t_int - t_s) / m_s
                        
                        # 2. Mark this as the last valid segment for this cycle
                        hit_idx = i
                        break
                
                # 3. If we hit something, delete all segments that were supposed to happen after
                if hit_idx != -1:
                    all_shock_waves[cycle_idx] = segments[:hit_idx + 1]
                #this section is the setup, does the shock hit a previous wave from the last L1 light
                #or does it have free road and miss the last fan



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
        cull_overlapping_segments(shock_waves_L2, t_RL2[i], D2)
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
            elif t_current_RL2 < arrival_start:
                # We are in a gap, but we LOAD the plume into the queue 
                # so the 'while' loop can find the intersection later.
                current_s = -rho_initial
                valid_fan_arms = [[arm[0], arm[1], 0] for arm in temp_fan]

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
    inner_term = (s * (t_RL - t_G) * (t - t_G)) / (1 + s)
    x_comb = (1-2*rho_in)*(t-t_G) + D - 2*(1-rho_in)*np.sqrt(np.maximum(0, inner_term))

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
        # --- 1. Define the boundary for the next cycle ---
        if i + 1 < len(t_RL2):
            t_next_cycle_start = t_RL2[i + 1]
        else:
            # For the final cycle, let it run until the end of the simulation
            t_next_cycle_start = t_start + 700
        for t_curr in t_steps[1:]:
            dt_now = t_curr - t_GL2
            if t_curr >= t_next_cycle_start:
                break

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
def L1_shock_curves(rho_in, D1, start_list, end_list, t_RL_interval_1, t_max_limit=140):
    all_curves = []
    s = -rho_in  # shock velocity
    
    for i in range(len(start_list)):
        t_RL = start_list[i]
        t_G = end_list[i]
        
        # 1. Determine the "Cutoff Time" for the whole cycle
        if i + 1 < len(start_list):
            t_stop_cycle = start_list[i+1]
        else:
            t_stop_cycle = t_max_limit 
            
        # 2. Transition time (when the back of the queue starts moving)
        # Note: t_hit MUST be >= t_G
        t_hit = t_G + (s * (t_RL - t_G)) / (1 + s)
        
        # Phase A: Linear segment (The Red Light accumulation)
        # We cap the linear part at t_hit
        t_lin = np.linspace(t_RL, t_hit, 20)
        x_lin = s * (t_lin - t_RL) + D1
        
        # Phase B: Curved segment (The Green Light clearing)
        t_cur = np.linspace(t_hit, t_stop_cycle, 100)
        x_cur = combined_wave_front(t_cur, rho_in, D1, t_RL, t_G)

        # 3. Collision Logic (Stop the curve if it hits the NEXT red light's shock)
        if i + 1 < len(start_list):
            t_RL_next = start_list[i+1]
            x_next_shock = s * (t_cur - t_RL_next) + D1
            
            # Only collide if the time has actually reached the next red light
            active_mask = t_cur >= t_RL_next
            collision_mask = (x_cur <= x_next_shock) & active_mask
            
            if np.any(collision_mask):
                stop_idx = np.where(collision_mask)[0][0]
                t_cur = t_cur[:stop_idx]
                x_cur = x_cur[:stop_idx]
        else:
            # Final Cycle: Cap it so it doesn't shoot backwards infinitely
            t_max_allowed = t_G + t_RL_interval_1
            mask = t_cur <= t_max_allowed
            t_cur = t_cur[mask]
            x_cur = x_cur[mask]

        # 4. JOINING (This MUST happen outside the collision IF block)
        x_lin = np.atleast_1d(x_lin)
        x_cur = np.atleast_1d(x_cur)
        t_lin = np.atleast_1d(t_lin)
        t_cur = np.atleast_1d(t_cur)

        full_x = np.concatenate([x_lin, x_cur])
        full_t = np.concatenate([t_lin, t_cur])

        if len(full_x) > 0:
            all_curves.append(np.column_stack([full_x, full_t]))
        
    return all_curves

def find_intercept(m, c, coords, t_min):
    """Returns the first (t, x) intercept with a curve after t_min."""
    for k in range(len(coords) - (1 if len(coords[0]) == 2 else 0)):
        # If the input is a list of points [x, t] (2 values)
        if len(coords[k]) == 2:
            x1, t1 = coords[k]
            x2, t2 = coords[k+1]
        
        # If the input is a list of segments [m, t1, t2, x1, x2] (5 values)
        # This matches your variable_shockwave output!
        elif len(coords[k]) == 5:
            _, t1, t2, x1, x2 = coords[k]
        
        else:
            continue

        vs = (x2 - x1) / (t2 - t1) if abs(t2 - t1) > 1e-6 else 0
        denom = (1.0/m - vs)
        
        if abs(denom) > 1e-9:
            t_int = (x1 - vs*t1 + c/m) / denom
            
            # Use the min/max of the segment time bounds
            if min(t1, t2) <= t_int <= max(t1, t2) and t_int >= t_min:
                x_int = (t_int - c) / m
                return t_int, x_int
                
    return None, None

def get_finite_fan_segments(fans_raw, light_1_shock_wave_front, position_of_1, position_of_2,timings_of_1,light_2_shock_wave_front, dissipation_front):
    """
    Approximates the shockwave intersection for each fan arm.
    Returns a list of [x_shock, t_shock, x_end, t_end] for each arm.
    """
    finite_fans = []
    
    for i, cycle_equations in enumerate(fans_raw):
        if i >= len(light_1_shock_wave_front): break
        
        # This is the 'red curve' for this cycle: a list of [x, t]
        shock_coords = light_1_shock_wave_front[i]
        cycle_segments = []
        
        for m, c in cycle_equations:
            # 1. Define the 'End' of the fan (usually the next light or plot boundary)
            x_end = position_of_2
            t_end = (m * x_end) + c
            
            # 2. Find the 'Start' (The intersection with the shockwave)
            # Default to the light position if no intersection is found
            x_start, t_start = position_of_1, (m * position_of_1) + c
            
            # Iterate through the shockwave segments to find the 'floor'
            for j in range(len(shock_coords) - 1):
                x1, t1 = shock_coords[j]
                x2, t2 = shock_coords[j+1]
                
                # Slope of this tiny shockwave segment (dx/dt)
                if abs(t2 - t1) > 1e-6:
                    v_s = (x2 - x1) / (t2 - t1)
                else:
                    v_s = 0 
                
                # Linear Algebra: Solve for t where fan line meets shock segment
                # Fan: x = (t - c) / m  | Shock: x = v_s(t - t1) + x1
                # (t - c)/m = v_s(t - t1) + x1
                denom = (1.0/m - v_s) if abs(m) > 1e-9 else -v_s
                if abs(denom) > 1e-9:
                    t_int = (x1 - v_s*t1 + c/m) / denom
                    x_int = (t_int - c) / m # Now we have the raw coordinate
                    
                    # 1. Check if the time is actually within the start/end of THIS shock segment
                    if timings_of_1[i] <= t_int <= max(t1, t2):
                        
                        # 2. THE FIX: We no longer check "if x_int <= position_of_1"
                        # We simply accept this as the boundary where the fan arm hits the curve.
                        x_start, t_start = x_int, t_int
                        
                        # Once we find the point where the arm hits the curve, we stop looking
                        break
            
            # 3. Save the two points defining the finite segment
            # Format: [x1, t1, x2, t2]
            if m > 0:
                # 1. Base case: Car starts at L1 and tries to reach the L1 shockwave (the pouch)
                x_base_start, t_base_start = position_of_1, timings_of_1[i]
                x_base_end, t_base_end = x_start, t_start 
                
                # 2. THE MULTI-CYCLE CHECK: Check current (i) and previous (i-1) L2 cycles
                possible_hits = []
                
                # We check the current cycle and the one right before it
                for cycle_offset in [0, -1]:
                    check_idx = i + cycle_offset
                    if check_idx < 0: continue
                    
                    # Check L2 Shockwave for this cycle
                    if check_idx < len(light_2_shock_wave_front):
                        t_hit_s, x_hit_s = find_intercept(m, c, light_2_shock_wave_front[check_idx], t_base_start)
                        if t_hit_s: possible_hits.append((t_hit_s, x_hit_s))

                    # Check L2 Dissipation for this cycle
                    if check_idx < len(dissipation_front):
                        t_hit_d, x_hit_d = find_intercept(m, c, dissipation_front[check_idx], t_base_start)
                        if t_hit_d: possible_hits.append((t_hit_d, x_hit_d))

                # 3. Decision Logic: Find the earliest hit across ALL checked cycles
                if possible_hits:
                    possible_hits.sort() # Smallest t (first impact) comes first
                    t_l2_hit, x_l2_hit = possible_hits[0]
                    
                    # If the earliest L2 hit happens before we clear L1, or if we are in free flow
                    if t_l2_hit < t_base_end or t_base_end == t_base_start:
                        x_base_end, t_base_end = x_l2_hit, t_l2_hit

                # Re-assign variables for the append
                x_start, t_start = x_base_start, t_base_start
                x_end, t_end = x_base_end, t_base_end
                
            elif m<0:
                x_end = position_of_1
                t_end = timings_of_1[i]
            cycle_segments.append([x_start, t_start, x_end, t_end])
            
        finite_fans.append(cycle_segments)
    
    return finite_fans


def find_line_intersection(m1, c1, line2):
    # line2: [x1, t1, x2, t2]
    # Convert line2 back to y = mx + c
    if abs(line2[2] - line2[0]) < 1e-6: return None, None # Vertical
    m2 = (line2[3] - line2[1]) / (line2[2] - line2[0])
    c2 = line2[1] - m2 * line2[0]
    
    if abs(m1 - m2) < 1e-9: return None, None # Parallel
    
    # x = (c2 - c1) / (m1 - m2)
    x_int = (c2 - c1) / (m1 - m2)
    t_int = m1 * x_int + c1
    
    # Verify intersection is within the bounds of the L1 arm
    if min(line2[0], line2[2]) <= x_int <= max(line2[0], line2[2]):
        return t_int, x_int
    return None, None

def get_finite_fan_segments_L2(fans_raw_L2, light_2_shock_wave_front, position_of_2, position_of_3, 
                               timings_of_2, dissipation_front_L2, finite_fans_L1):
    """
    Specifically for L2: Clips fan arms based on the next red light (L2 shock/dissipation)
    and intersections with incoming L1 plumes.
    """
    finite_fans_L2 = []
    
    for i, cycle_equations in enumerate(fans_raw_L2):
        if i >= len(light_2_shock_wave_front): break
        
        # The 'red boundaries' for this L2 cycle
        shock_coords = light_2_shock_wave_front[i]
        cycle_segments = []
        
        for m, c in cycle_equations:
            # 1. DEFAULT START: The Light 2 position
            x_start, t_start = position_of_2, timings_of_2[i]
            
            # 2. FIND THE END: Where the car hits a boundary
            # Default to some world boundary (position_of_3)
            x_end = position_of_3
            t_end = (m * x_end) + c
            
            possible_hits = []

            # --- Check A: Hit the L2 Shockwave (the back of the current queue) ---
            t_hit_s, x_hit_s = find_intercept(m, c, shock_coords, t_start)
            if t_hit_s: possible_hits.append((t_hit_s, x_hit_s))

            # --- Check B: Hit the L2 Dissipation (the front of the current queue) ---
            if i < len(dissipation_front_L2):
                t_hit_d, x_hit_d = find_intercept(m, c, dissipation_front_L2[i], t_start)
                if t_hit_d: possible_hits.append((t_hit_d, x_hit_d))

            # --- Check C: Interaction with L1 Fan Arms (The Plume) ---
            # This handles where the release wave from L2 meets the plume arriving from L1
            for cycle_l1 in finite_fans_L1:
                for arm_l1 in cycle_l1:
                    # arm_l1 format: [x1, t1, x2, t2]
                    # We treat L1 arms as moving boundaries
                    t_hit_l1, x_hit_l1 = find_line_intersection(m, c, arm_l1)
                    if t_hit_l1 and t_hit_l1 > t_start:
                        possible_hits.append((t_hit_l1, x_hit_l1))

            # 3. Decision Logic: Closest impact wins
            if possible_hits:
                possible_hits.sort()
                t_end, x_end = possible_hits[0]

            # 4. Handle Slope Direction
            if m > 0:
                # Standard release: Start at light, end at first obstruction
                cycle_segments.append([x_start, t_start, x_end, t_end])
            elif m < 0:
                # Backward moving waves (Shockwaves within the fan itself)
                cycle_segments.append([x_end, t_end, x_start, t_start])
                
        finite_fans_L2.append(cycle_segments)
    
    return finite_fans_L2

def get_release_time(x_car, dissipation_curves):
    """
    Finds the time t when the dissipation curve reaches the stopped car's x.
    Uses linear interpolation across the maroon curve points.
    """
    for curve in dissipation_curves:
        if len(curve) < 2: continue
        
        c = np.array(curve)
        # c[:, 0] is x, c[:, 1] is t
        x_min, x_max = np.min(c[:, 0]), np.max(c[:, 0])
        
        # Check if the car's stopped position is within the range of this clearing wave
        if x_min <= x_car <= x_max:
            # We want t for a given x, so we interp(target_x, xp, fp)
            # Note: dissipation curves move from left to right, so x is typically increasing
            t_release = np.interp(x_car, c[:, 0], c[:, 1])
            return t_release
            
    return None
def find_intercept_single(v_veh, x_start, t_start, shock_list):
    """
    Standardized intersection: only looks for hits in the FUTURE.
    """
    hits = []
    for cycle in shock_list:
        for j in range(len(cycle) - 1 if len(cycle[0]) == 2 else len(cycle)):
            seg = cycle[j]
            if len(seg) == 5:
                _, t1, t2, x1, x2 = seg
            else:
                x1, t1 = cycle[j]; x2, t2 = cycle[j+1]
            
            # --- CRITICAL: Skip cycles that ended before our current time ---
            if max(t1, t2) < t_start: continue 

            if abs(t2 - t1) < 1e-6: continue
            v_s = (x2 - x1) / (t2 - t1)
            
            denom = (v_veh - v_s)
            if abs(denom) < 1e-9: continue 
            
            t_int = (x1 - v_s*t1 - x_start + v_veh*t_start) / denom
            
            # Intersection must be within segment AND in the car's future
            if min(t1, t2) <= t_int <= max(t1, t2) and t_int > t_start + 0.05:
                x_int = x_start + v_veh * (t_int - t_start)
                hits.append((t_int, x_int))
                
    if hits:
        hits.sort() # Get the SOONEST future hit
        return hits[0] 
    return None, None

def get_active_tg(curr_t, green_starts):
    """Finds the most recent green light start time."""
    past_starts = [t for t in green_starts if t <= curr_t]
    return past_starts[-1] if past_starts else None

def get_fan_velocity(x, t, t_G, light_pos, v_max):
    """Calculates the theoretical velocity inside an expansion fan."""
    # FIX: If there is no active green light yet, velocity is 0
    if t_G is None or t <= t_G: 
        return 0.0
    
    # Standard fan formula
    v_fan = 0.5 * ((x - light_pos) / (t - t_G) + 1)
    
    # Ensure we stay between 0 and v_max
    return min(v_max, max(0.0, v_fan))

def get_release_time_filtered(x_car, dissipation_curves, current_time):
    for curve in dissipation_curves:
        c = np.array(curve)
        if np.min(c[:, 0]) <= x_car <= np.max(c[:, 0]):
            t_rel = np.interp(x_car, c[:, 0], c[:, 1])
            # Only return this release time if it's in the future!
            if t_rel > current_time + 0.1:
                return t_rel
    return None

def find_intercept_all_cycles(v_car, x0, t0, all_shocks):
    best_t = float('inf')
    best_x = None

    for cycle in all_shocks:
        for seg in cycle:
            # --- NEW: HANDLE DIFFERENT DATA STRUCTURES ---
            if len(seg) == 2:
                # It's a Light 1 "Full Line" [m, c]
                m_s, c_s = seg
                # We treat these as infinite lines, but you can bound 
                # them by your simulation time (e.g., 0 to 700)
                t_s_start, t_s_end = 0, 700 
            elif len(seg) == 5:
                # It's a Light 2 "Physical Segment" [m, t_s, t_e, x_s, x_e]
                m_s, t_s_start, t_s_end, x_s_start, x_s_end = seg
                c_s = t_s_start - m_s * x_s_start
            else:
                continue # Skip unknown formats

            # --- MATH: Solve for intersection ---
            # Car: x = x0 + v_car * (t - t0)
            # Shock: x = (t - c_s) / m_s
            denom = (v_car * m_s - 1)
            if abs(denom) < 1e-9: continue
            
            t_int = (x0 * m_s - v_car * t0 * m_s - c_s) / denom
            x_int = x0 + v_car * (t_int - t0)
            
            # --- VALIDATION ---
            # 1. Must be within the time-bounds of the shockwave segment
            # 2. Must be in the car's future (t_int >= t0)
            if t_s_start - 1e-3 <= t_int <= t_s_end + 1e-3:
                if t_int >= t0 - 1e-6:
                    if t_int < best_t:
                        best_t = t_int
                        best_x = x_int
                        
    return (best_t, best_x) if best_t != float('inf') else (None, None)

def track_vehicle_full_physics(t_start, v_in_norm, D1, D2, shock_L1, shock_L2, g_starts_1, g_starts_2, r_starts_1, r_starts_2, V_MAX_REAL):
    curr_x, curr_t = 0.0, t_start
    path = [[curr_x, curr_t]]
    dt = 0.2
    is_stopped = False

    while curr_x < (D2 + 50/V_MAX_REAL) and curr_t < 700:
        # 1. SELECT LIGHT ZONE
        if curr_x < (D1 + D2)/2:
            shocks, g_starts, r_starts, pos = shock_L1, g_starts_1, r_starts_1, D1
        else:
            shocks, g_starts, r_starts, pos = shock_L2, g_starts_2, r_starts_2, D2

        # 2. CHECK FAN VELOCITY
        active_tg = get_active_tg(curr_t, g_starts)
        v_fan = get_fan_velocity(curr_x, curr_t, active_tg, pos, v_in_norm)

        # 3. STOPPED LOGIC
        if is_stopped:
            if v_fan > 0.05: # Threshold for release
                is_stopped = False
            else:
                curr_t += dt
                path.append([curr_x, curr_t])
                continue

        # 4. ENHANCED COLLISION CHECK
        # We must flatten the shocks list or search all cycles to avoid "cycle gaps"
        t_hit, x_hit = find_intercept_all_cycles(v_in_norm, curr_x, curr_t, shocks)
        
        # Check for intersection within this time step
        if t_hit and curr_t <= t_hit <= curr_t + dt:
            curr_x, curr_t = x_hit, t_hit
            path.append([curr_x, curr_t])
            is_stopped = True
            continue

        # 5. GHOSTING PROTECTION (The "Emergency Brake")
        # If no shockwave was found, but the light is red and we are at the line:
        is_red = any(rs <= curr_t < gs for rs, gs in zip(r_starts, g_starts))
        if is_red and (pos - v_in_norm * dt) <= curr_x <= pos:
            curr_x = pos # Snap to the light
            path.append([curr_x, curr_t])
            is_stopped = True
            continue

        # 6. MOVEMENT
        v_limit = v_fan if (active_tg and curr_x <= pos) else v_in_norm
        v_move = min(v_in_norm, v_limit)

        curr_x += v_move * dt
        curr_t += dt
        path.append([curr_x, curr_t])
            
    return np.array(path)