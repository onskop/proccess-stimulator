import simpy
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Liquid:
    volume: float  # Liters
    # Composition: {'Water': 900g, 'Glucose': 50g, 'Salt': 10g}
    contents: Dict[str, float] = field(default_factory=dict)

    def __repr__(self):
        # Pretty print for debugging
        s = [f"{k}: {v:.2f}g" for k, v in self.contents.items()]
        return f"<Liquid {self.volume:.2f}L | {', '.join(s)}>"

class AdvancedTank:
    def __init__(self, env, name, capacity):
        self.env = env
        self.name = name
        
        # 1. COMPLEX STATE (Goal #1)
        # We use a dict so we can track multiple dimensions of reality
        self.state = {
            "op_mode": "Idle",      # Idle, Filling, Emptying
            "cip_status": "Dirty",  # Clean, Dirty, Sterile
            "temperature": 20.0     # Celsius
        }

        # 2. PHYSICS ENGINE (Volume Limits)
        self.container = simpy.Container(env, capacity=capacity, init=0)
        
        # 3. CHEMISTRY ENGINE (Mass Balance)
        # Tracks total grams of each substance in the tank
        self._inventory = Counter() 

    @property
    def current_volume(self):
        return self.container.level

    def get_concentration(self, substance):
        """Returns g/L of a specific substance."""
        if self.current_volume == 0: return 0.0
        return self._inventory[substance] / self.current_volume

    def put_liquid(self, liquid: Liquid):
        """
        Add a 'Liquid' object to the tank. 
        Mixes it perfectly with existing contents.
        """
        print(f"[{self.env.now:5.2f}] {self.name}: Adding {liquid}")
        
        # 1. Blocking Logic: Wait for space (Volume)
        yield self.container.put(liquid.volume)
        
        # 2. Mass Balance Logic: Add ingredients
        for substance, mass in liquid.contents.items():
            self._inventory[substance] += mass
            
        # Update state example
        self.state["op_mode"] = "Filling"

    def get_liquid(self, volume_needed) -> Liquid:
        """
        Extract a volume. Returns a Liquid object with 
        proportional ingredients (perfect mixing assumption).
        """
        # 1. Blocking Logic: Wait for liquid
        yield self.container.get(volume_needed)
        
        # 2. Calculate what comes out (Proportionality)
        # If we take 10% of volume, we take 10% of the sugar, 10% of the salt.
        # Note: We use the volume AFTER the 'get' to calculate total previous volume
        total_vol_before = self.container.level + volume_needed
        fraction = volume_needed / total_vol_before
        
        extracted_contents = {}
        
        for substance, total_mass in self._inventory.items():
            mass_removed = total_mass * fraction
            extracted_contents[substance] = mass_removed
            
            # Update internal inventory
            self._inventory[substance] -= mass_removed
            
        self.state["op_mode"] = "Emptying"
        
        return Liquid(volume=volume_needed, contents=extracted_contents)

def lab_process(env, tank):
    # --- STEP 1: CREATE CONCENTRATE ---
    # Create 10L of high-sugar media (100g/L)
    concentrate = Liquid(volume=10, contents={"Water": 9000, "Glucose": 1000, "Salt": 100})
    
    print("\n--- ADDING CONCENTRATE ---")
    yield from tank.put_liquid(concentrate)
    
    # Check internals
    gluc_conc = tank.get_concentration("Glucose")
    print(f"Debug: Tank Volume: {tank.current_volume}L, Glucose Conc: {gluc_conc:.2f} g/L")


    # --- STEP 2: DILUTE ---
    # Add 10L of Pure Water
    water = Liquid(volume=10, contents={"Water": 10000})
    
    print("\n--- DILUTING WITH WATER ---")
    yield from tank.put_liquid(water)
    
    # At this point:
    # Total Vol: 20L
    # Total Glucose: 1000g
    # Expected Conc: 50g/L
    
    gluc_conc = tank.get_concentration("Glucose")
    print(f"Debug: Tank Volume: {tank.current_volume}L, Glucose Conc: {gluc_conc:.2f} g/L")


    # --- STEP 3: PROCESS / CONSUME ---
    # Take 2L out for "Production"
    print("\n--- DRAWING SAMPLE ---")
    sample = yield from tank.get_liquid(2.0)
    
    print(f"Sample Extracted: {sample}")
    
    # Validate the physics
    # We took 2L out of 20L (10%). We should have 10% of the glucose (100g).
    print(f"Sample Glucose Mass: {sample.contents['Glucose']:.2f}g (Expected 100g)")
    print(f"Tank Remaining Glucose: {tank._inventory['Glucose']:.2f}g (Expected 900g)")

# --- EXECUTION ---
env = simpy.Environment()
smart_tank = AdvancedTank(env, "Bioreactor", capacity=100)

env.process(lab_process(env, smart_tank))
env.run()