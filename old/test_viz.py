import yaml
from schema import RecipeConfig
from viz import render_process_map

def test_viz():
    with open('process.yaml', 'r') as f:
        data = yaml.safe_load(f)
    config = RecipeConfig(**data)
    
    print("Rendering Process Map...")
    nodes, edges, config_obj = render_process_map(config)
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    # Basic assertions
    assert len(nodes) == len(config.steps)
    assert any(n.id == "Make Media" for n in nodes)
    assert any(n.id == "Main Culture" for n in nodes)
    assert config_obj.hierarchical is True
    
    print("\nTest Passed!")

if __name__ == "__main__":
    test_viz()
