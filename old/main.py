import yaml
import simpy
from schema import RecipeConfig
from engine import SimulationEngine, Batch
from units import MediaPrep, Fermentation, Chromatography

def load_config(path: str) -> RecipeConfig:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return RecipeConfig(**data)

def run_simulation():
    try:
        config = load_config('process.yaml')
    except FileNotFoundError:
        print("Error: process.yaml not found.")
        return

    engine = SimulationEngine()
    
    # Setup Resources
    # Assuming 1 Bioreactor available matching the volume constraint
    bioreactor = simpy.Resource(engine.env, capacity=1)
    chromatography_skids = simpy.Resource(engine.env, capacity=config.resources.chromatography_skids)
    
    # Create the Batch
    # Initializing with the bioreactor volume as the target batch size
    batch = Batch(id="Batch-001", volume_liters=config.resources.bioreactor_volume)
    
    print(f"Starting Simulation with Batch Size: {batch.volume_liters}L")

    def process_flow():
        for step_config in config.steps:
            step_type = step_config.type
            
            if step_type == "MediaPrep":
                step = MediaPrep(engine.env, step_config)
                yield from step.run(batch)
                
            elif step_type == "Fermentation":
                step = Fermentation(engine.env, step_config, resource=bioreactor)
                yield from step.run(batch)
                
            elif step_type == "Chromatography":
                step = Chromatography(engine.env, step_config, resource=chromatography_skids)
                yield from step.run(batch)
            
            # Check if batch failed (volume 0)
            if batch.volume_liters == 0:
                print("Batch failed/terminated. Stopping simulation.")
                break
        
        # Record final product
        engine.materials_manager.add_product(batch.product_mass_grams)
    
    engine.env.process(process_flow())
    engine.run()
    
    # Report
    summary = engine.materials_manager.get_summary()
    print("\n" + "="*30)
    print("       SIMULATION REPORT       ")
    print("="*30)
    print(f"Total Process Time:     {engine.now:.2f} hours")
    print(f"Total Product Produced: {summary['total_product_grams']:.2f} g")
    print("-" * 30)
    print("Inventory Consumed:")
    for item, amount in summary['inventory_consumed'].items():
        print(f"  - {item}: {amount}")
    print("-" * 30)
    print("Waste Produced:")
    if not summary['waste_produced']:
        print("  None")
    else:
        for item, amount in summary['waste_produced'].items():
            print(f"  - {item}: {amount}")
    print("="*30)

if __name__ == "__main__":
    run_simulation()
