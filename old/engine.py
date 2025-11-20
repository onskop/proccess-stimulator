import simpy
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class Batch:
    """Represents the liquid material moving through the process."""
    id: str
    volume_liters: float
    product_mass_grams: float = 0.0
    contaminants_grams: float = 0.0
    history: List[str] = field(default_factory=list)

    def log(self, message: str):
        self.history.append(message)

class MaterialsManager:
    """Singleton-like class to track global inventory and waste."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MaterialsManager, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.inventory: Dict[str, float] = {}
        self.waste: Dict[str, float] = {}
        self.product_produced: float = 0.0

    def consume(self, material: str, amount: float):
        if material not in self.inventory:
            self.inventory[material] = 0.0
        self.inventory[material] += amount

    def add_waste(self, waste_type: str, amount: float):
        if waste_type not in self.waste:
            self.waste[waste_type] = 0.0
        self.waste[waste_type] += amount

    def add_product(self, amount: float):
        self.product_produced += amount

    def get_summary(self):
        return {
            "inventory_consumed": self.inventory,
            "waste_produced": self.waste,
            "total_product_grams": self.product_produced
        }

class SimulationEngine:
    """Wrapper around simpy Environment."""
    def __init__(self):
        self.env = simpy.Environment()
        self.materials_manager = MaterialsManager()
        self.materials_manager.reset()
        # registry of tanks / buffers
        self.tanks = {}

    def run(self, until=None):
        self.env.run(until=until)

    def create_tank(self, name, capacity):
        self.tanks[name] = simpy.Container(self.env, capacity=capacity)

    @property
    def now(self):
        return self.env.now
