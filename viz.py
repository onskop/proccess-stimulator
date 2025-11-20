import networkx as nx
from streamlit_agraph import agraph, Node, Edge, Config
from schema import RecipeConfig

def build_graph(config: RecipeConfig) -> nx.DiGraph:
    G = nx.DiGraph()
    
    # Add nodes
    for step in config.steps:
        G.add_node(step.name, type=step.type, duration=step.duration_hours)
        
    # Add edges
    for step in config.steps:
        if step.input_batch:
            if step.input_batch in G.nodes:
                G.add_edge(step.input_batch, step.name)
            else:
                pass
                
    return G

def get_node_color(step_type: str):
    if step_type == "Fermentation":
        return "#90EE90" # Light Green
    elif step_type == "Chromatography":
        return "#98FB98" # Pale Green
    elif step_type == "MediaPrep":
        return "#ADD8E6" # Light Blue
    else:
        return "#FFCCCB" # Light Red

def render_process_map(config: RecipeConfig):
    G = build_graph(config)
    
    # We can still use networkx layout if we want fixed positions, 
    # but agraph handles layout automatically (physics based).
    # However, user requested "Topological Sort" or "Generational Layout".
    # agraph supports 'hierarchical' layout via Config.
    
    nodes = []
    edges = []
    
    for node_name in G.nodes:
        node_data = G.nodes[node_name]
        step_type = node_data['type']
        duration = node_data.get('duration', 0)
        
        label = f"{node_name}\n({step_type})\n{duration}h"
        color = get_node_color(step_type)
        
        nodes.append(Node(
            id=node_name,
            label=label,
            size=25,
            color=color,
            shape="box"
        ))
        
    for u, v in G.edges:
        edges.append(Edge(
            source=u,
            target=v,
            type="CURVE_SMOOTH"
        ))
        
    config_obj = Config(
        width=800,
        height=600,
        directed=True, 
        physics=False, 
        hierarchical=True, # This enforces the tree/DAG layout
        # hierarchy options can be tuned if needed
    )
        
    return nodes, edges, config_obj
