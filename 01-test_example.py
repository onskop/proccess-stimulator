import simpy

# --- basic commands and toolbox function ---

# yield env.timeout(hours) # wait for hours
# yield container.get(amount) # get amount from container
# yield container.put(amount) # put amount into container
# yield resource.request() # request resource
# yield resource.release() # release resource

#yield from my_function(): use this when calling your own function that contains yields inside

# --- define objects ---
#tank1 = simpy.Container(env, capacity=100, init=0)
#tank2 = simpy.Container(env, capacity=100, init=0)
#resource1 = simpy.Resource(env, capacity=1)
#resource2 = simpy.Resource(env, capacity=1)

# --- define processes ---
#def process_flow():
#    yield tank1.get(10)
#    yield tank2.put(10)

# env.process(process_flow()) # process flow
# env.run() # run simulation


def tank_fill(env, tank, amount):
    print(f"[{env.now:5.2f}] FILL : Filling tank with {amount}L/h")
    tank.status = "Filling"
    while tank.level < tank.capacity:
        yield env.timeout(1)
        yield tank.put(amount)

    print(f"[{env.now:5.2f}] FILL : Tank is full at {tank.level}L")


def tank_empty(env, tank, amount):
    print(f"[{env.now:5.2f}] EMPTY : Emptying tank with {amount}L/h")
    tank.status = "Emptying"
    while tank.level >= amount:
        yield env.timeout(1)
        yield tank.get(amount)

    print(f"[{env.now:5.2f}] EMPTY : Tank is empty at {tank.level}L")

def process_flow(env, tank):
    print(f"[{env.now:5.2f}] PROCESS : Starting process")
    tank.status = "Processing"
    
    # "yield from" means: Run this function completely, wait for it to finish, then come back.
    yield from tank_fill(env, tank, 10)
    
    yield from tank_empty(env, tank, 10)

    tank.status = "Idle"

    
    
    print(f"[{env.now:5.2f}] PROCESS : Process completed at {env.now} hours")

# --- NEW FUNCTION: THE REPORTER ---
def reporter(env, tank):
    # Run forever
    while tank.status != "Idle":
        # Print current status
        print(f"[{env.now:5.2f}] REPORT : {tank.name} is {tank.status}, level is {tank.level}L")
        
        # Wait 2 hours before checking again
        yield env.timeout(1)



# EXECUTION PHASE

# --- setup environment, mandatory command ---
env = simpy.Environment()

# --- define objects ---

tank1 = simpy.Container(env, capacity=130, init=0)
tank1.name = "Media Tank"


# --- run process ---

env.process(process_flow(env, tank1))
env.process(reporter(env, tank1))

print("Starting simulation...")
env.run()
print("Simulation completed.")

