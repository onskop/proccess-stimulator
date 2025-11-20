import simpy
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
TANK_CAPACITY = 100.0    # Liters
BIOREACTOR_FLOW = 2.0    # Liters per hour
CLEANING_TIME = 4.0      # Hours to clean a tank
FILLING_TIME = 2.0       # Hours to make media and fill tank
SIM_DURATION = 1500       # Hours

# --- SHARED STATE ---
# This dictionary acts as the "brain" that all functions can see
system_state = {
    "active_tank_name": "MT1" # Starts consuming from MT1
}

# --- PROCESS 1: THE BIOREACTOR (CONSUMER) ---
def bioreactor_process(env, tanks, product_tank, waste_tank):
    print(f"[{env.now:5.1f}] BIO   : Production Started")
    
    while env.now <= SIM_DURATION:
        # 1. Identify which tank is currently active
        active_name = system_state["active_tank_name"]
        active_tank = tanks[active_name]
        
        # 2. CHECK FOR SWITCH
        # If active tank doesn't have enough for the next hour, switch!
        if active_tank.level < BIOREACTOR_FLOW:
            print(f"[{env.now:5.1f}] SWITCH: {active_name} is empty! Switching tanks.")
            
            # Toggle the name
            if active_name == "MT1":
                system_state["active_tank_name"] = "MT2"
            else:
                system_state["active_tank_name"] = "MT1"
            
            # Update our local variable to the new tank
            active_name = system_state["active_tank_name"]
            active_tank = tanks[active_name]
            
            print(f"[{env.now:5.1f}] SWITCH: New Active Tank is {active_name} (Level: {active_tank.level}L)")

        # 3. CONSUME (Wait 1 hour for the flow)
        yield env.timeout(1)
        
        # Take media from the active tank
        # We use Try/Except just in case we run out completely
        if active_tank.level >= BIOREACTOR_FLOW:
            yield active_tank.get(BIOREACTOR_FLOW)
            
            # 4. PERFUSION SPLIT (ATF)
            # 5% to Product, 95% to Waste
            to_product = BIOREACTOR_FLOW * 0.05
            to_waste = BIOREACTOR_FLOW * 0.95
            
            yield product_tank.put(to_product)
            yield waste_tank.put(to_waste)
        else:
            print(f"[{env.now:5.1f}] ALARM : CRITICAL - BOTH TANKS EMPTY! Process Paused.")


# --- PROCESS 2: THE MEDIA MANAGER (PRODUCER) ---
def media_refiller_process(env, tanks):
    """Checks for empty, idle tanks and refills them."""
    while env.now <= SIM_DURATION:
        # Check status of both tanks
        for name, tank in tanks.items():
            
            # Logic: If tank is empty AND it is NOT the one being used
            is_idle = (name != system_state["active_tank_name"])
            is_empty = (tank.level < 1.0) # virtually empty
            
            if is_idle and is_empty:
                print(f"[{env.now:5.1f}] MEDIA : {name} is empty and idle. Starting Clean & Refill.")
                
                # Step A: Cleaning (Delay)
                yield env.timeout(CLEANING_TIME)
                
                # Step B: Filling (Delay + Action)
                yield env.timeout(FILLING_TIME)
                yield tank.put(TANK_CAPACITY)
                
                print(f"[{env.now:5.1f}] MEDIA : {name} Refilled to {tank.level}L. Ready.")
        
        # Check again every 6 minutes (0.1 hours) to be responsive
        yield env.timeout(0.1)


# --- PROCESS 3: THE REPORTER (DATA LOGGING) ---
def reporter_process(env, tanks, product_tank, waste_tank, data_log):
    while env.now <= SIM_DURATION:
        # Record current state
        data_log.append({
            "Time": env.now,
            "MT1_Level": tanks['MT1'].level,
            "MT2_Level": tanks['MT2'].level,
            "Product_Vol": product_tank.level,
            "Waste_Vol": waste_tank.level,
            "Active_Tank": system_state["active_tank_name"]
        })
        # Wait 1 hour
        yield env.timeout(1)













# --- MAIN EXECUTION ---

# 1. Setup Environment
env = simpy.Environment()










# 2. Create Objects
# MT1 starts full, MT2 starts empty (to test refill logic immediately)
tanks = {
    "MT1": simpy.Container(env, capacity=TANK_CAPACITY, init=TANK_CAPACITY),
    "MT2": simpy.Container(env, capacity=TANK_CAPACITY, init=0)
}
product_tank = simpy.Container(env, capacity=1000, init=0)
waste_tank = simpy.Container(env, capacity=10000, init=0)

# List to store data for charts
data_log = []










# 3. Add Processes
env.process(bioreactor_process(env, tanks, product_tank, waste_tank))
env.process(media_refiller_process(env, tanks))
env.process(reporter_process(env, tanks, product_tank, waste_tank, data_log))










# 4. Run
print("--- Simulation Start ---")
env.run(until=SIM_DURATION)
print("--- Simulation End ---")











# --- VISUALIZATION (Matplotlib) ---
print("\nGenerating Chart...")
df = pd.DataFrame(data_log)

plt.figure(figsize=(12, 6))

# Plot Media Tanks
plt.plot(df['Time'], df['MT1_Level'], label='Media Tank 1', color='blue')
plt.plot(df['Time'], df['MT2_Level'], label='Media Tank 2', color='cyan', linestyle="--")

# Plot Product (Multiplied by 10 just to make it visible on the same scale)
plt.plot(df['Time'], df['Product_Vol'], label='Product (Accumulated)', color='green', linewidth=2)

# Formatting
plt.title('Perfusion Process: Swing Tank Switching')
plt.xlabel('Time (hours)')
plt.ylabel('Volume (L)')
plt.axhline(y=0, color='black', linewidth=0.5)
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()