import simpy

def perfusion_fermentation(env, harvest_tank):
    """
    PRODUCER: Runs for 10 days. 
    Every 1 hour, it drips 2 Liters into the harvest tank.
    """
    print(f"[{env.now:6.2f}] START: Fermentation started.")
    
    # Run for 240 hours (10 days)
    for i in range(240):
        # 1. Wait for 1 hour to pass
        yield env.timeout(1)
        
        # 2. Generate Product (2 Liters)
        amount_produced = 2.0
        
        # 3. Put it in the tank
        # This line effectively adds liquid to the container
        yield harvest_tank.put(amount_produced)
        
        # (Optional) Print status every 24 hours so we don't spam the console
        if env.now % 24 == 0:
            print(f"[{env.now:6.2f}] FERM : Bleeding {amount_produced}L. Tank Level: {harvest_tank.level}L")

    print(f"[{env.now:6.2f}] END  : Fermentation finished.")


def daily_chromatography(env, harvest_tank):
    """
    CONSUMER: Runs forever.
    Every 24 hours, it wakes up, checks the tank, and processes everything inside.
    """
    print(f"[{env.now:6.2f}] START: Chromatography skid is online.")
    
    while True:
        # 1. Wait for the daily cycle (start processing at hour 24, 48, etc.)
        yield env.timeout(24)
        
        # 2. Check how much is in the tank right now
        current_vol = harvest_tank.level
        
        if current_vol > 0:
            print(f"[{env.now:6.2f}] CHROMA: Waking up. Found {current_vol}L in tank.")
            
            # 3. Take the liquid OUT of the tank (simulating loading)
            yield harvest_tank.get(current_vol)
            
            # 4. Simulate the time it takes to run the column (e.g., 4 hours)
            processing_time = 4
            yield env.timeout(processing_time)
            
            print(f"[{env.now:6.2f}] CHROMA: Finished cycle. Processed {current_vol}L.")
        else:
            print(f"[{env.now:6.2f}] CHROMA: Tank is empty. Going back to sleep.")


# --- MAIN SIMULATION SETUP ---

# 1. Create the Environment (The Clock)
env = simpy.Environment()

# 2. Create the Shared Tank (The Buffer)
# capacity=1000 means it overflows if we put more than 1000L
harvest_tank = simpy.Container(env, capacity=1000, init=0)

# 3. "Hire the workers" (Register the processes)
# We tell SimPy to run these two functions IN PARALLEL
env.process(perfusion_fermentation(env, harvest_tank))
env.process(daily_chromatography(env, harvest_tank))

# 4. Run the simulation
print("--- Starting Perfusion Simulation ---")
env.run(until=300) # Run for 300 simulation hours
print("--- Simulation Complete ---")