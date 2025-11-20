import streamlit as st
import yaml
from streamlit_agraph import agraph
from schema import RecipeConfig
from viz import render_process_map
import io
import sys
from engine import SimulationEngine, Batch
from units import MediaPrep, Fermentation, Chromatography
import simpy

st.set_page_config(layout="wide", page_title="Pharma Process Simulator")

def run_sim_logic(config_yaml_str):
    try:
        data = yaml.safe_load(config_yaml_str)
        config = RecipeConfig(**data)
    except Exception as e:
        return None, f"Error parsing YAML: {e}"

    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    try:
        engine = SimulationEngine()
        bioreactor = simpy.Resource(engine.env, capacity=1)
        chromatography_skids = simpy.Resource(engine.env, capacity=config.resources.chromatography_skids)
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
                
                if batch.volume_liters == 0:
                    print("Batch failed/terminated.")
                    break
            
            engine.materials_manager.add_product(batch.product_mass_grams)
        
        engine.env.process(process_flow())
        engine.run()
        
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

    except Exception as e:
        print(f"Simulation Error: {e}")
    finally:
        sys.stdout = old_stdout
        
    return mystdout.getvalue(), None

st.sidebar.title("Process Configuration")
try:
    with open("process.yaml", "r") as f:
        default_yaml = f.read()
except:
    default_yaml = ""

yaml_content = st.sidebar.text_area("Edit YAML", value=default_yaml, height=600)

st.title("Pharma Process Simulator & Visualizer")

tab1, tab2 = st.tabs(["Process Map", "Simulation Results"])

with tab1:
    if yaml_content:
        try:
            data = yaml.safe_load(yaml_content)
            config = RecipeConfig(**data)
            
            nodes, edges, config_obj = render_process_map(config)
            
            agraph(nodes=nodes, edges=edges, config=config_obj)
            
        except Exception as e:
            st.error(f"Error rendering graph: {e}")

with tab2:
    if st.button("Run Simulation"):
        output, err = run_sim_logic(yaml_content)
        if err:
            st.error(err)
        else:
            st.text_area("Simulation Output", value=output, height=400)
