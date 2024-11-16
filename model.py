# agents.py
from mesa import Agent
from typing import Tuple, List, Optional

class Building(Agent):
    """Static building agent that occupies space on the grid."""
    def __init__(self, model, position: Tuple[int, int]):
        super().__init__(model)
        self.color = "#87CEEB"  # Light blue color

    def step(self):
        pass

class SpawnPoint(Agent):
    """Agent representing a vehicle spawn point."""
    def __init__(self, model, position: Tuple[int, int], direction: Tuple[int, int], spawn_id: int):
        super().__init__(model)
        self.direction = direction
        self.spawn_id = spawn_id
        self.color = "#FFFF00"  # Yellow color
        self.pos = position

    def step(self):
        pass

class TrafficLight(Agent):
    """Traffic light agent that controls traffic flow."""
    def __init__(self, model, position: Tuple[int, int], light_set: int):
        super().__init__(model)
        self.state = "red"
        self.color = "#FF0000"
        self.light_set = light_set
        self.countdown = model.random.randint(1, 5)

    def change_state(self):
        if self.state == "red":
            self.state = "green"
            self.color = "#00FF00"
        else:
            self.state = "red"
            self.color = "#FF0000"

    def step(self):
        self.countdown -= 1
        if self.countdown <= 0:
            self.change_state()
            self.countdown = self.model.random.randint(3, 7)

class Vehicle(Agent):
    """Vehicle agent that moves to a destination."""
    
    def __init__(self, model):
        super().__init__(model)
        
        # Get all spawn points
        spawn_points = [agent for agent in model.schedule.agents if isinstance(agent, SpawnPoint)]
        if not spawn_points:
            raise ValueError("No spawn points available")
            
        # Select random spawn point
        spawn_point = self.random.choice(spawn_points)
        self.spawn_id = spawn_point.spawn_id
        self.direction = spawn_point.direction
        self.initial_pos = spawn_point.pos
        
        # Select random destination from remaining spawn points
        possible_destinations = [sp for sp in spawn_points if sp.spawn_id != spawn_point.spawn_id]
        destination_point = self.random.choice(possible_destinations)
        self.destination = destination_point.pos
        
        # State variables
        self.waiting = False
        self.patience = self.random.randint(3, 7)
        self.speed = self.random.uniform(0.8, 1.2)
        
        # Set color based on destination
        self.color = self.get_color_for_destination(destination_point.spawn_id)

    def get_color_for_destination(self, destination_id: int) -> str:
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FF00FF", "#00FFFF", 
                 "#FFA500", "#800080", "#008000", "#FFC0CB", "#FFD700"]
        return colors[destination_id % len(colors)]

    def calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        x1, y1 = pos1
        x2, y2 = pos2
        return abs(x2 - x1) + abs(y2 - y1)

    def check_traffic_light(self, pos: Tuple[int, int]) -> bool:
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        for agent in cell_contents:
            if isinstance(agent, TrafficLight) and agent.state == "red":
                return True
        return False

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        if not self.pos:
            return []
        
        x, y = self.pos
        possible_moves = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        valid_moves = []
        
        for move in possible_moves:
            if (0 <= move[0] < self.model.grid.width and 
                0 <= move[1] < self.model.grid.height):
                cell_contents = self.model.grid.get_cell_list_contents(move)
                if not any(isinstance(agent, (Building, Vehicle)) for agent in cell_contents):
                    valid_moves.append(move)
        
        return valid_moves

    def get_next_move(self) -> Optional[Tuple[int, int]]:
        if not self.pos:
            return None
            
        valid_moves = self.get_valid_moves()
        if not valid_moves:
            return None
            
        move_distances = {}
        for move in valid_moves:
            if self.check_traffic_light(move):
                continue
            distance = self.calculate_distance(move, self.destination)
            distance += self.random.uniform(0, 0.5)  # Add randomness
            move_distances[move] = distance
            
        if not move_distances:
            self.waiting = True
            return None
            
        min_distance = min(move_distances.values())
        best_moves = [move for move, dist in move_distances.items() 
                     if abs(dist - min_distance) < 0.1]
        
        self.waiting = False
        return self.random.choice(best_moves)

    def move(self):
        if not self.pos:
            return
            
        # Check if reached destination
        if self.pos == self.destination:
            self.model.remove_vehicle(self)
            return
            
        next_pos = self.get_next_move()
        
        if next_pos:
            self.waiting = False
            self.model.grid.move_agent(self, next_pos)
            self.patience = max(self.patience, 3)
        else:
            self.waiting = True
            self.patience -= 1

    def step(self):
        if self.random.random() < self.speed:
            self.move()

# model.py
from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector


class IntersectionModel(Model):
    """Model representing a traffic intersection with buildings, spawn points, and traffic lights."""
    def __init__(self, width=24, height=24):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        
        # Initialize the environment
        self.setup_intersection()
        
        # Set up data collection
        self.datacollector = DataCollector(
            model_reporters={
                "spawn_points": lambda m: len([a for a in m.schedule.agents if isinstance(a, SpawnPoint)]),
                "buildings": lambda m: len([a for a in m.schedule.agents if isinstance(a, Building)]),
                "traffic_lights": lambda m: len([a for a in m.schedule.agents if isinstance(a, TrafficLight)]),
                "vehicles": lambda m: len([a for a in m.schedule.agents if isinstance(a, Vehicle)])
            }
        )
        
        self.running = True

    def setup_intersection(self):
        """Set up the initial state of the intersection."""
        self.create_buildings()
        self.create_traffic_lights()
        self.create_spawn_points()

    def create_spawn_points(self):
        """Create spawn points at specified locations."""
        spawn_points_data = [
            (2, 14, (1, 0), 1),   # 1
            (3, 21, (0, -1), 2),  # 2
            (3, 6, (0, -1), 3),   # 3
            (4, 12, (1, 0), 4),   # 4
            (4, 3, (0, 1), 5),    # 5
            (5, 17, (1, 0), 6),   # 6
            (8, 15, (-1, 0), 7),  # 7
            (9, 2, (0, 1), 8),    # 8
            (10, 19, (0, -1), 9), # 9
            (10, 12, (1, 0), 10), # 10
            (10, 7, (-1, 0), 11), # 11
            (17, 21, (0, -1), 12),# 12
            (17, 6, (0, -1), 13), # 13
            (17, 4, (-1, 0), 14), # 14
            (20, 18, (1, 0), 15), # 15
            (20, 15, (-1, 0), 16),# 16
            (20, 4, (0, 1), 17)   # 17
        ]
        
        for x, y, direction, spawn_id in spawn_points_data:
            # Clear existing agents at this position
            cell_contents = self.grid.get_cell_list_contents((x, y))
            for agent in cell_contents:
                self.grid.remove_agent(agent)
            
            # Create and place spawn point
            spawn_point = SpawnPoint(self, (x, y), direction, spawn_id)
            self.grid.place_agent(spawn_point, (x, y))
            self.schedule.add(spawn_point)

    def create_buildings(self):
        """Create buildings with specified coordinates."""
        buildings = [
            ((2, 21), (5, 12)),   # First building
            ((2, 7), (5, 6)),     # Second building
            ((2, 3), (5, 2)),     # Third building
            ((8, 21), (11, 19)),  # Fourth building
            ((8, 16), (11, 12)),  # Fifth building
            ((8, 7), (11, 6)),    # Sixth building
            ((8, 3), (11, 2)),    # Seventh building
            ((16, 21), (21, 18)), # Eighth building
            ((16, 15), (21, 12)), # Ninth building
            ((16, 7), (17, 2)),   # Tenth building
            ((20, 7), (21, 2))    # Eleventh building
        ]
        
        # Place buildings
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    building = Building(self, (x, y))
                    self.grid.place_agent(building, (x, y))
                    self.schedule.add(building)
        
        # Central building (13,10 to 14,9)
        for x in range(13, 15):
            for y in range(9, 11):
                building = Building(self, (x, y))
                building.color = "brown"
                self.grid.place_agent(building, (x, y))
                self.schedule.add(building)

    def create_traffic_lights(self):
        """Create traffic light sets at specified coordinates."""
        traffic_light_sets = [
            [(0, 6), (1, 6)],     # Set 1
            [(2, 4), (2, 5)],     # Set 2
            [(5, 0), (5, 1)],     # Set 3
            [(6, 2), (7, 2)],     # Set 4
            [(6, 16), (7, 16)],   # Set 5
            [(6, 21), (7, 21)],   # Set 6
            [(8, 22), (8, 23)],   # Set 7
            [(17, 8), (17, 9)],   # Set 8
            [(18, 7), (19, 7)],   # Set 9
            [(8, 17), (8, 18)]    # Set 10
        ]

        for set_idx, light_positions in enumerate(traffic_light_sets, 1):
            for pos in light_positions:
                traffic_light = TrafficLight(self, pos, set_idx)
                self.grid.place_agent(traffic_light, pos)
                self.schedule.add(traffic_light)

    def add_vehicle(self):
        """Create and add a new vehicle to the model."""
        vehicle = Vehicle(self)
        self.grid.place_agent(vehicle, vehicle.initial_pos)
        self.schedule.add(vehicle)
        return vehicle

    def remove_vehicle(self, vehicle):
        """Remove a vehicle and spawn a new one to maintain traffic flow."""
        if vehicle in self.schedule.agents:
            self.schedule.remove(vehicle)
        self.grid.remove_agent(vehicle)
        
        # Add a new vehicle with probability
        if self.random.random() < 0.5:  # 50% chance to spawn new vehicle
            self.add_vehicle()

    def step(self):
        """Advance the model by one step."""
        # Random chance to add new vehicle (10% chance each step)
        if self.random.random() < 0.1:
            self.add_vehicle()
        
        # Move all agents using the scheduler
        self.schedule.step()
        
        # Collect data
        self.datacollector.collect(self)