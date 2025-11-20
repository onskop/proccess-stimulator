import simpy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

class Tank:
    def __init__(self, env, dt, name, capacity, initial_level=0):
        self.env = env
        self.name = name
        self.dt = dt
        self.status = "Idle"  # Defined here once, safe to use everywhere
        
        # The "Engine" is hidden inside the class
        self.container = simpy.Container(env, capacity=capacity, init=initial_level)


    def fill_to_level(self, target_level, rate):
        print(f"[{self.env.now:5.2f}] {self.name} : Filling to {target_level}L at {rate}L/h")
        self.status = "Filling"
        while self.container.level < target_level:
            yield self.env.timeout(self.dt)
            space_available = self.container.capacity - self.container.level
            yield self.container.put(min(rate*self.dt, space_available))
        self.status = "Idle"
        print(f"[{self.env.now:5.2f}] {self.name} : Filled to {self.container.level}L")

    def empty_to_level(self, target_level, rate):
        print(f"[{self.env.now:5.2f}] {self.name} : Emptying to {target_level}L at {rate}L/h")
        self.status = "Emptying"
        while self.container.level > target_level:
            yield self.env.timeout(self.dt)
            remaining_volume = self.container.level - target_level
            yield self.container.get(min(rate*self.dt, remaining_volume))
        self.status = "Idle"
        print(f"[{self.env.now:5.2f}] {self.name} : Emptied to {self.container.level}L")


# --- MAIN PROCESS ---

def main_process(env, tank):
    print(f"[{env.now:5.2f}] MASTER : Starting process")

    yield from tank.fill_to_level(100, 8)
    yield env.timeout(4) # 4 hours of hold time
    yield from tank.empty_to_level(50, 6)

    print(f"[{env.now:5.2f}] MASTER : Process completed")



def reporter_process(env, tank, data_log):

    while True:

        yield env.timeout(tank.dt)
        bar = "|" * int(tank.container.level / 10)
        print(f"   [REPORT] {tank.name} [{tank.status:^10}] : {tank.container.level:5.1f}L {bar}")
        data_log.append({
            "Time": env.now,
            "Tank": tank.name,
            "Level": tank.container.level,
            "Status": tank.status
        })


# --- MAIN EXECUTION ---

env = simpy.Environment()
SIM_DURATION = 30
DT = 0.1
data_log = []

print("Starting simulation...")
tank = Tank(env, DT, "Tank1", 100, 0)

env.process(main_process(env, tank))
env.process(reporter_process(env, tank, data_log))

env.run(until=SIM_DURATION)

print("Simulation completed.")











# --- REPORTING AND VISUALIZATION ---

df = pd.DataFrame(data_log)

# Create figure with two subplots
fig = plt.figure(figsize=(14, 10))

# --- SUBPLOT 1: Tank Content Chart ---
ax1 = plt.subplot(2, 1, 1)
ax1.plot(df['Time'], df['Level'], linewidth=2.5, color='#2E86AB', label='Tank Level')
ax1.axhline(y=tank.container.capacity, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Capacity')
ax1.fill_between(df['Time'], df['Level'], alpha=0.3, color='#2E86AB')
ax1.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Volume (L)', fontsize=11, fontweight='bold')
ax1.set_title(f'Tank Content Over Time - {tank.name}', fontsize=13, fontweight='bold', pad=15)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='best', framealpha=0.9)
ax1.set_xlim(left=0)

# --- SUBPLOT 2: Gantt Chart for Status ---
ax2 = plt.subplot(2, 1, 2)

# Status color mapping
status_colors = {
    'Idle': '#95A5A6',      # Gray
    'Filling': '#27AE60',   # Green
    'Emptying': '#E74C3C'   # Red
}

# Process data_log to identify status transitions for Gantt chart
# Group by status and find continuous periods
status_periods = []
current_status = None
period_start = None

for idx, row in df.iterrows():
    if current_status != row['Status']:
        # Status changed - end previous period and start new one
        if current_status is not None and period_start is not None:
            status_periods.append({
                'start': period_start,
                'end': row['Time'],
                'status': current_status
            })
        current_status = row['Status']
        period_start = row['Time']

# Add the last period
if current_status is not None and period_start is not None:
    status_periods.append({
        'start': period_start,
        'end': df['Time'].iloc[-1],
        'status': current_status
    })

# Build Gantt chart
y_pos = 0  # Single row for this tank
bar_height = 0.6

for period in status_periods:
    start_time = period['start']
    end_time = period['end']
    status = period['status']
    duration = end_time - start_time
    
    color = status_colors.get(status, '#95A5A6')
    
    # Draw the bar
    ax2.barh(y_pos, duration, left=start_time, height=bar_height, 
             color=color, edgecolor='black', linewidth=1.5, alpha=0.8)
    
    # Add label in the middle of the bar if it's wide enough
    if duration > 0.5:  # Only label if bar is wide enough
        mid_time = start_time + duration / 2
        ax2.text(mid_time, y_pos, status, ha='center', va='center', 
                fontweight='bold', fontsize=10, color='white')

# Format Gantt chart
ax2.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Tank', fontsize=11, fontweight='bold')
ax2.set_title('Tank Status Timeline (Gantt Chart)', fontsize=13, fontweight='bold', pad=15)
ax2.set_yticks([y_pos])
ax2.set_yticklabels([tank.name])
ax2.set_xlim(left=0)
ax2.grid(True, alpha=0.3, linestyle='--', axis='x')

# Create legend for status colors
legend_elements = [mpatches.Patch(facecolor=color, edgecolor='black', label=status) 
                   for status, color in status_colors.items()]
ax2.legend(handles=legend_elements, loc='upper right', framealpha=0.9)

plt.tight_layout()
plt.show()

# Print summary statistics
print("\n" + "="*60)
print("SIMULATION SUMMARY")
print("="*60)
print(f"Total Duration: {df['Time'].max():.2f} hours")
print(f"Final Tank Level: {df['Level'].iloc[-1]:.2f} L")
print(f"Maximum Tank Level: {df['Level'].max():.2f} L")
print(f"Minimum Tank Level: {df['Level'].min():.2f} L")
print("\nStatus Summary:")
status_counts = df['Status'].value_counts()
for status, count in status_counts.items():
    duration = count * tank.dt
    percentage = (duration / df['Time'].max()) * 100
    print(f"  {status:10s}: {duration:6.2f} hours ({percentage:5.1f}%)")
print("="*60)