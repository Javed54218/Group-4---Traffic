import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.collections as mcoll
from Wave_eqn_functions import green_wave_fan, shock_wave_linear, combined_wave_front, variable_shockwave, variable_dissipation_curve

# ----- DEFINE VARIABLES -------------
'''maths uses dimensionless quantities so careful with units
velocity and density are defined as fractions of the total velocity and density'''

# Universal variables: --------------
rho_initial = 0.4      # initial density entering the system approaching the first set of lights
no_cycles = 6          # number of green/red light cycles to simulate

# Traffic light set 1 variables (L1): ---------------
position_of_1 = 0      # D1: position of the first set of traffic lights
t_RL_interval_1 = 5   # time interval between red lights
t_RL_length_1 = 4     # duration the light stays red (d_RL1)
# Derived L1 timings
t_RL1 = np.array([i * (t_RL_interval_1 + t_RL_length_1) for i in range(no_cycles + 2)])
t_G1 = t_RL1 + t_RL_length_1

# Traffic light set 2 variables (L2): --------------
position_of_2 = 15     # D2: position of the second set of traffic lights
t_RL_interval_2 =  10  # time interval between red lights
t_RL_length_2 = 2     # duration the light stays red (d_RL2)
t_offset_2 = 5        # time offset/delay between Light 1 and Light 2 cycles
# Derived L2 timings
t_RL2 = t_RL1 + t_offset_2
t_G2 = t_RL2 + t_RL_length_2

# --- 2. RUNNING THE PHYSICS ENGINE ---

# Step A: Generate the traffic plumes coming from Light 1
# Resolution of 50 segments provides smooth density transitions
fan1 = green_wave_fan(rho_initial, t_G1, position_of_1, 50)

# Step B: Calculate the accumulation shockwaves at Light 2
# Returns segments: [slope, t_start, t_end, x_start, x_end]
shock_waves = variable_shockwave(rho_initial, fan1, position_of_2, t_RL2, t_RL_length_2, position_of_1, t_RL1)

# Step C: Calculate the curved dissipation (clearing) waves
# Uses the shockwave endpoints to initiate the parabolic clearing curves
curves = variable_dissipation_curve(shock_waves, fan1, position_of_2, t_RL2, t_RL_length_2, rho_initial)


# --- 3. PLOTTING THE SPACE-TIME DIAGRAM ---

# Set up color cycle for visual clarity between light phases
colors = cm.rainbow(np.linspace(0, 1, len(fan1)))
plt.figure(figsize=(14, 8))

#--- PLOT PLUMES AND DISCHARGE ---
for i in range(len(t_G1)):
    cycle_color = colors[i]
    
    # Plot Fan 1 (Plumes arriving from Light 1)
    for arm_idx, arm in enumerate(fan1[i]):
        m, c = arm[0], arm[1]
        t_s = m * position_of_1 + c
        t_e = t_s + 100 
        # FIX: Calculate x_end using the line equation (t = mx + c) -> x = (t - c) / m
        current_x_end = (t_e - c) / m
        
        plt.plot([position_of_1, current_x_end], [t_s, t_e], color=cycle_color, alpha=0.2, lw=1, 
                 label=f"Cycle {i+1} Plume" if arm_idx == 0 else "")

    # Plot Fan 2 (Discharge leaving Light 2)
    # We use t_G2[i] which was defined as t_RL2[i] + t_RL_length_2
    fan2_current = green_wave_fan(rho_initial, [t_G2[i]], position_of_2, 20)[0]
    for arm_idx, arm in enumerate(fan2_current):
        m, c = arm[0], arm[1]
        t_s = m * position_of_2 + c
        t_e = t_s + 60
        current_x_end_L2 = (t_e - c) / m
        
        plt.plot([position_of_2, current_x_end_L2], [t_s, t_e], color=cycle_color, alpha=0.4, lw=1, ls='--', 
                 label=f"L2 Discharge {i+1}" if arm_idx == 0 else "")

# --- PLOT SHOCKWAVES (RED) ---
for i, cycle_segments in enumerate(shock_waves):
    for j, seg in enumerate(cycle_segments):
        m_s, t_s, t_e, x_s, x_e = seg
        plt.plot([x_s, x_e], [t_s, t_e], color='red', lw=2.5, zorder=5,
                 label='Shockwave' if i==0 and j==0 else "")
        plt.scatter(x_e, t_e, color='black', s=10, zorder=6) # Intersection points

# --- PLOT DISSIPATION CURVES (VELOCITY CODED) ---
for i, path in enumerate(curves):
    p = np.asanyarray(path)
    if p.ndim < 2 or len(p) < 2: continue
    
    xs, ts = p[:, 0], p[:, 1]
    dx, dt = np.diff(xs), np.diff(ts)
    velocities = np.where(dt > 1e-9, dx / dt, 0)
    
    points = np.array([xs, ts]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    lc = mcoll.LineCollection(segments, cmap='RdYlGn', linewidths=2, alpha=0.9, zorder=10)
    lc.set_array(velocities)
    plt.gca().add_collection(lc)
    if i == 0: plt.plot([], [], color='green', label='Car Trajectory (V-coded)')

# --- FINAL FORMATTING ---
plt.axvline(position_of_1, color='black', ls='--', label='Light 1')
plt.axvline(position_of_2, color='black', label='Light 2')

plt.xlim(position_of_1 - 5, position_of_2 + 40)
plt.ylim(0, t_RL2[-1] + 100)
plt.xlabel('Distance (x)')
plt.ylabel('Time (t)')
plt.title(f'Multi-Cycle Traffic Interaction (Offset = {t_offset_2})')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()