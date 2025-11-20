import simpy

# --- THE TOOLBOX FUNCTIONS ---

def work_delay(env, name, hours):
    """Tool 1: Simple delay"""
    print(f"[{env.now:5.2f}] {name}: Started processing...")
    yield env.timeout(hours)
    print(f"[{env.now:5.2f}] {name}: Finished.")

def transfer_liquid(env, source, dest, amount, flow_rate_L_per_hr):
    """Tool 3: Pumping liquid"""
    duration = amount / flow_rate_L_per_hr
    print(f"[{env.now:5.2f}] PUMP : Moving {amount}L (Expected time: {duration:.2f}h)")
    
    # Take form source -> Wait -> Put in Dest
    yield source.get(amount)
    yield env.timeout(duration)
    yield dest.put(amount)
    
    print(f"[{env.now:5.2f}] PUMP : Transfer Done.")

# --- THE PROCESS LOGIC ---

def main_process(env, mixing_tank, hold_tank, filter_skid):
    
    # STEP 1: MAKE MEDIA
    # We assume mixing tank starts empty. We "create" liquid by putting it there.
    print(f"[{env.now:5.2f}] STEP 1: Mixing Media")
    yield env.process(work_delay(env, "Mixing", hours=2.0))
    
    # "Create" the liquid in the tank
    yield mixing_tank.put(100) 
    print(f"[{env.now:5.2f}] INV  : Mixing Tank now has {mixing_tank.level}L")


    # STEP 2: TRANSFER TO HOLD TANK
    # We can't start step 3 until this is done, so we yield the process
    print(f"[{env.now:5.2f}] STEP 2: Transfer to Hold")
    yield env.process(transfer_liquid(env, mixing_tank, hold_tank, amount=100, flow_rate_L_per_hr=50))


    # STEP 3: FILTRATION
    # This requires a Resource (The Filter Skid)
    print(f"[{env.now:5.2f}] STEP 3: Requesting Filter Skid")
    
    with filter_skid.request() as req:
        yield req # Wait for skid to be available
        
        print(f"[{env.now:5.2f}] RES  : Skid acquired. Starting Filtration.")
        
        # Filtration is just moving liquid through a restriction (slow flow)
        # Let's assume it goes out of Hold Tank into a "Final Bag" (not simulated here, we just remove it)
        yield hold_tank.get(100)
        yield env.timeout(4.0) # Filtration takes 4 hours
        
        print(f"[{env.now:5.2f}] RES  : Filtration complete. Releasing Skid.")


# --- SETUP AND RUN ---

env = simpy.Environment()

# EQUIPEMENT
mixing_tank = simpy.Container(env, capacity=200, init=0)
hold_tank   = simpy.Container(env, capacity=200, init=0)
mixing_tank2 = simpy.Container(env, capacity=200, init=0)
hold_tank2 = simpy.Container(env, capacity=200, init=0)
filter_skid = simpy.Resource(env, capacity=1) # Only 1 filter skid available

# START
env.process(main_process(env, mixing_tank, hold_tank, filter_skid))
env.process(main_process(env, mixing_tank2, hold_tank2, filter_skid))

env.run()