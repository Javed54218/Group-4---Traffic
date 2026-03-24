import numpy as np
import matplotlib.pyplot as plt
from Wave_eqn_functions import green_wave_fan, shock_wave_linear, variable_shockwave
from Wave_eqn_functions import variable_dissipation_curve, L1_shock_curves,get_finite_fan_segments
from Wave_eqn_functions import get_finite_fan_segments_L2,track_vehicle_full_physics
# --- 1. USER INPUTS (REAL WORLD UNITS) ---
V_MAX_REAL = 13.4      
RHO_JAM_REAL = 0.22727272727
FLUX_IN = 0.08        

no_cycles = 10

position_of_1 = 40.0     
t_RL_interval_1 = 60   
t_RL_length_1 = 30     

position_of_2 = position_of_1 + 250
t_RL_interval_2 = 60.0   
t_RL_length_2 = 25.0     
t_offset_2 = 50.0        

# --- 2. THE CONVERSION CALCULATIONS ---
def get_rho_from_flux(q, v_max, r_max):
    q_max = 0.25 * v_max * r_max
    if q > q_max: q = q_max
    disc = v_max**2 - (4 * v_max * q / r_max)
    return ((v_max - np.sqrt(disc)) / (2 * v_max / r_max)) / r_max

rho_initial = get_rho_from_flux(FLUX_IN, V_MAX_REAL, RHO_JAM_REAL)

# Scaled Positions
D1 = position_of_1 / V_MAX_REAL
D2 = position_of_2 / V_MAX_REAL

# Correct Timing Lists (Used by all functions)
# Note: Adding +1 to range creates the "Ghost Cycle" to terminate the last shockwave
start_list_1 = np.array([i * t_RL_interval_1 for i in range(no_cycles + 1)])
end_list_1 = start_list_1 + t_RL_length_1

start_list_2 = np.array([t + t_offset_2 for t in [i * t_RL_interval_2 for i in range(no_cycles + 1)]])
end_list_2 = start_list_2 + t_RL_length_2

# --- 3. FUNCTION COMBINATION (REORDERED FOR CLIPPING) ---
light_1_shock_wave_front = L1_shock_curves(rho_initial, D1, start_list_1, end_list_1, t_RL_interval_1)


fan1_raw = green_wave_fan(end_list_1, D1, 200) 

shock_segments = variable_shockwave(rho_initial, fan1_raw, D2, 
                                       start_list_2, t_RL_length_2, 
                                       D1, start_list_1)

curves_2 = variable_dissipation_curve(shock_segments, fan1_raw, D2, 
                                       start_list_2, t_RL_length_2, rho_initial)

fan1_finite_list = get_finite_fan_segments(
    fan1_raw, 
    light_1_shock_wave_front, 
    D1, 
    D2,end_list_1,shock_segments,curves_2
)
fan2_raw = green_wave_fan(end_list_2, D2, 200)

# 2. Get Finite Segments for Light 2
# This clips the L2 release lines against its own red zones and the incoming L1 traffic
fan2_finite_list = get_finite_fan_segments_L2(
    fan2_raw, 
    shock_segments,        # The L2 shockwaves
    D2,                    # Start position
    D2 + 500,              # End position (or D3 if you have a third light)
    end_list_2,            # Green light timings for L2
    curves_2,              # The L2 dissipation curves
    fan1_finite_list       # The already-clipped L1 plumes
)

start_times = np.arange(0, 100, 5)
all_trajectories = []
curves_1 = []

for i, cycle_points in enumerate(light_1_shock_wave_front):
    t_green = end_list_1[i] # When the light turns green for this cycle
    
    # Extract only the points that happen AFTER the green light starts
    # These points represent the 'Dissipation' or 'Clearing' phase
    release_phase = [pt for pt in cycle_points if pt[1] >= t_green]
    
    if release_phase:
        curves_1.append(release_phase)
for t_start in start_times:
    # The call line for the dual-light system
    traj = track_vehicle_full_physics(
        t_start=t_start, 
        v_in_norm=1.0, 
        D1=D1, 
        D2=D2, 
        shock_L1=light_1_shock_wave_front,  # List of L1 shock cycles
        shock_L2=shock_segments,            # List of L2 shock cycles
        g_starts_1=end_list_1,              # Timestamps when L1 turns green
        g_starts_2=end_list_2, r_starts_1 = start_list_1, r_starts_2 =start_list_2,
        V_MAX_REAL=V_MAX_REAL
    )
    all_trajectories.append(traj)

# ---------- Fixed Plotting Functions ----------------

def plot_L1_full(l1_curves, position, v_max, ax):
    import matplotlib.collections as mcoll
    for p in l1_curves:
        # We MUST multiply p[:, 0] by v_max to move it from ~3.0 to 40.0m
        x_meters = p[:, 0] * v_max
        t_seconds = p[:, 1]
        
        # Calculate Velocity (this remains 0 to 1.0)
        dx = np.diff(x_meters)
        dt = np.diff(t_seconds)
        with np.errstate(divide='ignore', invalid='ignore'):
            # Velocity in m/s, then normalized to 0-1 for the colormap
            v_real = np.where(dt > 1e-9, dx/dt, 0)
            v_norm = v_real / v_max 

        # Create segments for the color mapped line
        points = np.array([x_meters, t_seconds]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        lc = mcoll.LineCollection(segments, cmap='RdYlGn', linewidths=2.5, zorder=4)
        lc.set_array(v_norm)
        lc.set_clim(vmin=0, vmax=1.0)
        ax.add_collection(lc)

    ax.axvline(position, color='green', alpha=0.3)



def plot_variable_shock(red_light_start_2, red_light_end_2, position_of_2, shock_segments_f, v_max):
    for i in range(len(red_light_start_2)):
        # shock_segments_f[i] is a list of [m, t_start, t_end, x_start, x_end]
        for seg in shock_segments_f[i]:
            m_s, t_s, t_e, x_s, x_e = seg
            
            # 1. Plot the red line segment
            ax.plot([x_s * v_max, x_e * v_max], [t_s, t_e], color='red', lw=2)
            
            '''# 2. Plot black dots at the "kinks" (the start of the segment)
            # We use zorder=5 to make sure the dots sit on top of the lines
            ax.plot(x_s * v_max, t_s, 'ko', markersize=3, zorder=5)
            
        # Optional: Plot a dot at the very last endpoint of the shockwave
        if shock_segments_f[i]:
            last_seg = shock_segments_f[i][-1]
            ax.plot(last_seg[4] * v_max, last_seg[2], 'ko', markersize=3, zorder=5)'''
    
def plot_variable_dissipation_curve(diss_curves, ax, v_max):
    import matplotlib.collections as mcoll
    for curve in diss_curves:
        if len(curve) < 2: continue
        p = np.asanyarray(curve)
        # Scale X to meters
        xs_m = p[:, 0] * v_max
        ts = p[:, 1]
        
        dx = np.diff(xs_m)
        dt = np.diff(ts)
        v_norm = np.where(dt > 1e-9, (dx/dt)/v_max, 0)
        
        points = np.array([xs_m, ts]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        lc = mcoll.LineCollection(segments, cmap='RdYlGn', linewidths=2.5, zorder=4)
        lc.set_array(v_norm)
        lc.set_clim(vmin=0, vmax=1.0)
        ax.add_collection(lc)


# ----- Updated main plotting calls ------------------
fig, ax = plt.subplots(figsize=(11, 8))
# Plotting the vehicle paths in a distinct color (Yellow or White)
for traj in all_trajectories:
    # Scale x (index 0) by V_MAX_REAL, keep t (index 1) as is
    ax.plot(traj[:, 0] * V_MAX_REAL, traj[:, 1], 
            color='yellow', linewidth=1.2, alpha=0.8, zorder=10)


# 1. Plot Light 1
plot_L1_full(light_1_shock_wave_front, position_of_1, V_MAX_REAL, ax)

for cycle in fan1_finite_list:
    for x1, t1, x2, t2 in cycle:
        # Scale dimensionless x-coordinates to real meters
        x1_m = x1 * V_MAX_REAL
        x2_m = x2 * V_MAX_REAL
        
        # Plot using the scaled meters for X and raw seconds for T
        ax.plot([x1_m, x2_m], [t1, t2], 
                color='green', 
                alpha=1, 
                linewidth=0.5, 
                zorder=1)
for cycle in fan2_finite_list:
    for x1, t1, x2, t2 in cycle:
        # Scale dimensionless x to real meters
        ax.plot([x1 * V_MAX_REAL, x2 * V_MAX_REAL], [t1, t2], 
                color='cyan', alpha=0.6, linewidth=0.7, zorder=1)

# 3. Plot variable shock (Added V_MAX_REAL)
plot_variable_shock(start_list_2, end_list_2, position_of_2, shock_segments, V_MAX_REAL)

# 4. Plot dissipation (Added V_MAX_REAL)
plot_variable_dissipation_curve(curves_2, ax, V_MAX_REAL)

# ... (Formatting remains the same)

# --- Final Formatting ---
# Vertical lines to show where the traffic lights are physically located
ax.axvline(position_of_1, color='green', alpha=0.5, label='Light 1') 
ax.axvline(position_of_2, color='green', alpha=0.5, linestyle='--', label='Light 2')

ax.set_xlabel('Position (meters)')
ax.set_ylabel('Time (seconds)')
ax.set_title(f'Integrated Traffic Flow: Offset = {t_offset_2}s')

# x and y limits based on your real-world meters and total time
ax.set_xlim(position_of_1 - 50, position_of_2 + 10)
ax.set_ylim(0, end_list_2[-1] + 20)

plt.legend(loc='upper right')
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()