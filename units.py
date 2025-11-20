import simpy
import random
from typing import Generator, Optional
from engine import Batch, MaterialsManager
from schema import StepConfig, FermentationConfig, ChromatographyConfig, MediaPrepConfig

class UnitOperation:
    """Base class for all unit operations."""
    def __init__(self, env: simpy.Environment, config: StepConfig):
        self.env = env
        self.config = config
        self.materials = MaterialsManager()

    def run(self, batch: Batch) -> Generator:
        """
        Main execution logic for the unit op.
        Must be a generator (yield env.timeout or resource.request).
        """
        # Default behavior: just wait for duration if specified
        if self.config.duration_hours:
            yield self.env.timeout(self.config.duration_hours)

class MediaPrep(UnitOperation):
    def __init__(self, env: simpy.Environment, config: MediaPrepConfig):
        super().__init__(env, config)

    def run(self, batch: Batch) -> Generator:
        print(f"[{self.env.now:.2f}] Starting MediaPrep: {self.config.name}")
        
        # Consume materials
        for material, amount in self.config.consumables.items():
            self.materials.consume(material, amount)
        
        if self.config.duration_hours:
            yield self.env.timeout(self.config.duration_hours)
            
        print(f"[{self.env.now:.2f}] Finished MediaPrep: {self.config.name}")

class Fermentation(UnitOperation):
    def __init__(self, env: simpy.Environment, config: FermentationConfig, resource: simpy.Resource):
        super().__init__(env, config)
        self.resource = resource

    def run(self, batch: Batch) -> Generator:
        print(f"[{self.env.now:.2f}] Requesting Bioreactor for {self.config.name}")
        
        with self.resource.request() as req:
            yield req
            print(f"[{self.env.now:.2f}] Started Fermentation: {self.config.name}")
            
            # Consume materials
            for material, amount in self.config.consumables.items():
                self.materials.consume(material, amount)

            # Process
            yield self.env.timeout(self.config.duration_hours)

            # Stochastic Failure
            if random.random() < self.config.contamination_risk:
                print(f"[{self.env.now:.2f}] FAILURE: Contamination in {self.config.name}")
                self.materials.add_waste("Contaminated Batch", batch.volume_liters)
                batch.volume_liters = 0
                batch.product_mass_grams = 0
                batch.contaminants_grams += 1000 
                batch.log(f"Failed at {self.config.name} due to contamination")
                return

            # Growth
            # growth_rate is g/L per run
            produced_mass = batch.volume_liters * self.config.growth_rate
            batch.product_mass_grams += produced_mass
            batch.log(f"Completed {self.config.name}, produced {produced_mass}g")
            
            print(f"[{self.env.now:.2f}] Finished Fermentation: {self.config.name}. Produced {produced_mass}g product.")

class Chromatography(UnitOperation):
    def __init__(self, env: simpy.Environment, config: ChromatographyConfig, resource: simpy.Resource):
        super().__init__(env, config)
        self.resource = resource

    def run(self, batch: Batch) -> Generator:
        print(f"[{self.env.now:.2f}] Requesting Chromatography Skid for {self.config.name}")
        
        with self.resource.request() as req:
            yield req
            print(f"[{self.env.now:.2f}] Started Chromatography: {self.config.name}")

            total_cycles = self.config.cycles
            cycle_time = self.config.cycle_time_hours
            
            # Run cycles
            for i in range(total_cycles):
                yield self.env.timeout(cycle_time)
            
            # Consumables (Total for step)
            for material, amount in self.config.consumables.items():
                self.materials.consume(material, amount)

            # Yield loss
            original_mass = batch.product_mass_grams
            final_mass = original_mass * self.config.yield_step
            loss = original_mass - final_mass
            
            batch.product_mass_grams = final_mass
            self.materials.add_waste("Purification Waste", loss)
            
            batch.log(f"Completed {self.config.name}, yield {self.config.yield_step*100}%")
            print(f"[{self.env.now:.2f}] Finished Chromatography: {self.config.name}. Yield: {self.config.yield_step*100}%. Final Mass: {final_mass:.2f}g")
