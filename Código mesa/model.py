# model.py
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from typing import Tuple, List
from movements import NORTH, SOUTH, EAST, WEST, create_road_segments

class Building(Agent):
    """Static building agent that occupies space on the grid."""
    def __init__(self, model, position: Tuple[int, int]):
        super().__init__(model)
        self.color = "#87CEEB"  # Light blue color

    def step(self):
        """Buildings don't perform any actions."""
        pass

class SpawnPoint(Agent):
    """Agent representing a vehicle spawn point."""
    def __init__(self, model, position: Tuple[int, int], direction: Tuple[int, int], spawn_id: int):
        super().__init__(model)
        self.direction = direction
        self.spawn_id = spawn_id
        self.color = "#FFFF00"  # Yellow color for spawn points

    def step(self):
        """Spawn points don't perform any actions."""
        pass

def calculate_total_happiness(model):
    """Calculate the average happiness of all vehicles in the model"""
    vehicles = [agent for agent in model.agents if isinstance(agent, Vehicle)]
    if not vehicles:
        return 0
    return sum(vehicle.happiness for vehicle in vehicles) / len(vehicles)

from enum import Enum
from typing import Dict, List, Tuple

class LightState(Enum):
    """Traffic light states"""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

class TrafficLight(Agent):
    """Traffic light agent with timing and state management."""
    
    def __init__(self, model: Model, position: Tuple[int, int], light_set: int):
        super().__init__(model)
        self.position = position
        self.light_set = light_set
        self.state = LightState.RED
        self.time_in_state = 0
        
        # Define timing parameters (in steps)
        self.green_time = 10
        self.yellow_time = 3
        self.red_time = 13  # Should equal green_time + yellow_time of opposing lights
        
        # Update visualization color
        self.update_color()
    
    def update_color(self):
        """Update agent color based on current state."""
        if self.state == LightState.RED:
            self.color = "#FF0000"  # Red
        elif self.state == LightState.YELLOW:
            self.color = "#FFFF00"  # Yellow
        else:
            self.color = "#00FF00"  # Green
    
    def step(self):
        """Update light state based on timing."""
        self.time_in_state += 1
        
        # Check for state transitions
        if self.state == LightState.GREEN and self.time_in_state >= self.green_time:
            self.state = LightState.YELLOW
            self.time_in_state = 0
        elif self.state == LightState.YELLOW and self.time_in_state >= self.yellow_time:
            self.state = LightState.RED
            self.time_in_state = 0
        elif self.state == LightState.RED and self.time_in_state >= self.red_time:
            # Only transition to green if it's this light's turn in the sequence
            if self.should_turn_green():
                self.state = LightState.GREEN
                self.time_in_state = 0
        
        self.update_color()
    
    def should_turn_green(self) -> bool:
        """Determine if this light should turn green based on the coordination rules."""
        # Get all traffic lights
        all_lights = [agent for agent in self.model.agents if isinstance(agent, TrafficLight)]
        
        # Group lights by their set
        light_sets: Dict[int, List[TrafficLight]] = {}
        for light in all_lights:
            if light.light_set not in light_sets:
                light_sets[light.light_set] = []
            light_sets[light.light_set].append(light)
        
        # Define compatible light sets that can be green simultaneously
        compatible_sets = {
            1: [2, 3],  # Set 1 can be green with sets 2 and 3
            2: [1, 3],  # Set 2 can be green with sets 1 and 3
            3: [1, 2],  # Set 3 can be green with sets 1 and 2
            4: [5, 6],  # Set 4 can be green with sets 5 and 6
            5: [4, 6],  # Set 5 can be green with sets 4 and 6
            6: [4, 5],  # Set 6 can be green with sets 4 and 5
            7: [8, 9],  # Set 7 can be green with sets 8 and 9
            8: [7, 9],  # Set 8 can be green with sets 7 and 9
            9: [7, 8],  # Set 9 can be green with sets 7 and 8
            10: []      # Set 10 must operate independently
        }
        
        # Check if any incompatible sets have green lights
        for other_set, lights in light_sets.items():
            if other_set != self.light_set and other_set not in compatible_sets[self.light_set]:
                if any(light.state == LightState.GREEN for light in lights):
                    return False
        
        return True

class VehicleState(Enum):
    """Vehicle emotional states that affect behavior."""
    CALM = "calm"
    ANGRY = "angry"
    BROKEN = "broken"  # New state for broken vehicles


class MechanicVehicle(Agent):
    """Mechanic vehicle that responds to broken vehicles."""
    
    def __init__(self, model, spawn_point, target_vehicle):
        super().__init__(model)
        self.color = "#FFD700"  # Gold color for mechanic vehicles
        self.spawn_point = spawn_point
        self.previous_pos = None
        self.current_direction = spawn_point.direction
        self.target_vehicle = target_vehicle
        self.destination = target_vehicle.pos
        self.active = True
        self.road_segments = create_road_segments()
        self.waiting_time = 0
        self.has_made_first_move = False
        self.repair_time = 5  # Steps needed to repair a vehicle
        self.repairing = False
        self.repair_counter = 0
        
        # Create sets for each road type (for movement checks)
        self.ns_roads = {pos for segment in ['NS1', 'NS2', 'NS3', 'NS4', 'NS5'] 
                        for pos in self.road_segments[segment]}
        self.sn_roads = {pos for segment in ['SN1', 'SN2', 'SN3', 'SN4', 'SN5', 'SN6'] 
                        for pos in self.road_segments[segment]}
        self.we_roads = {pos for segment in ['WE1', 'WE2', 'WE3', 'WE4', 'WE5'] 
                        for pos in self.road_segments[segment]}
        self.ew_roads = {pos for segment in ['EW1', 'EW2', 'EW3', 'EW4', 'EW5'] 
                        for pos in self.road_segments[segment]}

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def check_collision(self, pos):
        """Check if a position is occupied by another vehicle."""
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        return any(isinstance(agent, (Vehicle, MechanicVehicle)) for agent in cell_contents 
                  if agent != self.target_vehicle)  # Allow moving to target vehicle's position

    def check_traffic_light(self, next_pos):
        """Check if there's a red/yellow light blocking the path. Mechanics ignore traffic lights."""
        return True  # Mechanics ignore traffic lights to reach broken vehicles quickly

    def check_adjacent_roads(self, pos):
        """Check for valid adjacent road segments."""
        if not self.active:
            return []
            
        x, y = pos
        valid_moves = []
        
        # Define adjacent positions
        adjacent = [
            (x+1, y), (x-1, y),  # East, West
            (x, y+1), (x, y-1)   # North, South
        ]
        
        current_direction = None
        if pos in self.ns_roads:
            current_direction = SOUTH
        elif pos in self.sn_roads:
            current_direction = NORTH
        elif pos in self.we_roads:
            current_direction = EAST
        elif pos in self.ew_roads:
            current_direction = WEST
            
        # Check each adjacent position
        for next_pos in adjacent:
            # Don't allow direct reversal of direction
            if current_direction:
                new_direction = (next_pos[0] - x, next_pos[1] - y)
                if new_direction == (-current_direction[0], -current_direction[1]):
                    continue
            
            # Check if it's a valid road segment (mechanics ignore traffic lights)
            if (next_pos in self.ns_roads or next_pos in self.sn_roads or 
               next_pos in self.we_roads or next_pos in self.ew_roads):
                valid_moves.append(next_pos)
                
        return valid_moves

    def get_valid_moves(self):
        """Get list of valid next positions."""
        if not self.active:
            return []
            
        x, y = self.pos
        valid_moves = []

        # Check if target is adjacent
        target_x, target_y = self.target_vehicle.pos
        if abs(x - target_x) + abs(y - target_y) == 1:
            return [self.target_vehicle.pos]
        
        # If at spawn point, try spawn direction first
        if not self.has_made_first_move:
            dx, dy = self.spawn_point.direction
            next_pos = (x + dx, y + dy)
            if (next_pos in self.ns_roads or next_pos in self.sn_roads or 
                next_pos in self.we_roads or next_pos in self.ew_roads):
                if not self.check_collision(next_pos):
                    return [next_pos]
                return [(x, y)] if self.previous_pos != (x, y) else []
        
        # Handle road-specific movements
        straight_move = None
        if (x, y) in self.ns_roads:
            straight_move = (x, y - 1)  # Move south
            if straight_move in self.ns_roads and not self.check_collision(straight_move):
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.sn_roads:
            straight_move = (x, y + 1)  # Move north
            if straight_move in self.sn_roads and not self.check_collision(straight_move):
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.we_roads:
            straight_move = (x + 1, y)  # Move east
            if straight_move in self.we_roads and not self.check_collision(straight_move):
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.ew_roads:
            straight_move = (x - 1, y)  # Move west
            if straight_move in self.ew_roads and not self.check_collision(straight_move):
                valid_moves.append(straight_move)
        
        # Only check adjacent roads if no straight move is available
        if not valid_moves:
            adjacent_moves = self.check_adjacent_roads(self.pos)
            valid_adjacent = []
            for move in adjacent_moves:
                if not self.check_collision(move):
                    valid_adjacent.append(move)
            if valid_adjacent:
                valid_moves.extend(valid_adjacent)
            else:
                return [(x, y)] if self.previous_pos != (x, y) else []
        
        return valid_moves

    def step(self):
        """Execute one step of mechanic vehicle movement or repair."""
        if not self.active:
            return
            
        # Update destination to match target vehicle's position
        if self.target_vehicle and self.target_vehicle.active:
            self.destination = self.target_vehicle.pos
            
        # If at same position as target vehicle, start repairing
        if self.pos == self.target_vehicle.pos:
            if not self.repairing:
                self.repairing = True
                self.repair_counter = 0
            
            self.repair_counter += 1
            if self.repair_counter >= self.repair_time:
                # Repair complete
                self.target_vehicle.state = VehicleState.CALM
                self.target_vehicle.color = "#0000FF"
                self.target_vehicle.broken = False
                self.target_vehicle.happiness = 100
                # Remove mechanic
                self.active = False
                self.model.grid.remove_agent(self)
                return
            return

        # If not at target vehicle, move towards it
        valid_moves = self.get_valid_moves()
        
        if valid_moves:
            # If target is in valid moves, prioritize it
            if self.target_vehicle.pos in valid_moves:
                next_pos = self.target_vehicle.pos
            else:
                # Sort valid moves by distance to target
                valid_moves_with_distances = [
                    (pos, self.manhattan_distance(pos, self.target_vehicle.pos))
                    for pos in valid_moves
                ]
                valid_moves_with_distances.sort(key=lambda x: x[1])  # Sort by distance
                
                # Choose from the moves that get us closest to target
                best_distance = valid_moves_with_distances[0][1]
                best_moves = [pos for pos, dist in valid_moves_with_distances if dist == best_distance]
                
                # If multiple best moves, prefer continuing in same direction if possible
                same_direction_moves = [
                    pos for pos in best_moves
                    if (pos[0] - self.pos[0], pos[1] - self.pos[1]) == self.current_direction
                ]
                
                if same_direction_moves and self.random.random() < 0.7:  # 70% chance to continue straight
                    next_pos = self.random.choice(same_direction_moves)
                else:
                    next_pos = self.random.choice(best_moves)
                    
            self.previous_pos = self.pos
            self.current_direction = (
                next_pos[0] - self.pos[0],
                next_pos[1] - self.pos[1]
            )
            
            self.model.grid.move_agent(self, next_pos)
            self.waiting_time = 0
            
            if not self.has_made_first_move:
                self.has_made_first_move = True
        else:
            self.waiting_time += 1


class Vehicle(Agent):
    """Vehicle agent that moves along predefined road segments following traffic rules."""
    
    def __init__(self, model, spawn_point):
        """Initialize a new vehicle agent."""
        super().__init__(model)
        self.color = "#0000FF"  # Start with blue for calm vehicles
        self.spawn_point = spawn_point
        self.previous_pos = None
        self.current_direction = spawn_point.direction
        self.waiting_time = 0
        self.has_made_first_move = False
        self.road_segments = create_road_segments()
        self.active = True  # Flag to track if agent should be removed
        
        # Happiness and state attributes
        self.happiness = 100  # Start at maximum happiness
        self.state = VehicleState.CALM
        self.happiness_decay_rate = 5  # Points lost per waiting step
        self.happiness_threshold = 30  # Threshold for becoming angry
        self.happiness_recovery_rate = 2  # Points gained per moving step
        
        # Breakdown mechanics
        self.broken = False
        self.steps_taken = 0
        self.breakdown_chance = 0.001  # 0.1% chance per step
        
        # Initialize destination
        all_spawn_points = [agent for agent in model.agents if isinstance(agent, SpawnPoint)]
        destination_point = self.random.choice([sp for sp in all_spawn_points if sp != spawn_point])
        self.destination = destination_point.pos
        
        # Create sets for each road type
        self.ns_roads = {pos for segment in ['NS1', 'NS2', 'NS3', 'NS4', 'NS5'] 
                        for pos in self.road_segments[segment]}
        self.sn_roads = {pos for segment in ['SN1', 'SN2', 'SN3', 'SN4', 'SN5', 'SN6'] 
                        for pos in self.road_segments[segment]}
        self.we_roads = {pos for segment in ['WE1', 'WE2', 'WE3', 'WE4', 'WE5'] 
                        for pos in self.road_segments[segment]}
        self.ew_roads = {pos for segment in ['EW1', 'EW2', 'EW3', 'EW4', 'EW5'] 
                        for pos in self.road_segments[segment]}

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def update_happiness(self, is_moving: bool):
        """Update happiness based on whether the vehicle is moving or waiting."""
        if is_moving:
            self.happiness = min(100, self.happiness + self.happiness_recovery_rate)
        else:
            self.happiness = max(0, self.happiness - self.happiness_decay_rate)
        
        # Update state and color based on happiness
        if self.happiness < self.happiness_threshold and self.state == VehicleState.CALM:
            self.state = VehicleState.ANGRY
            self.color = "#FF0000"  # Red for angry vehicles
        elif self.happiness >= self.happiness_threshold and self.state == VehicleState.ANGRY:
            self.state = VehicleState.CALM
            self.color = "#0000FF"  # Blue for calm vehicles

    def debug_position(self):
        """Print debug information for stuck vehicles."""
        if not self.active:
            return
            
        x, y = self.pos
        print(f"\nDEBUG Vehicle {self.unique_id}:")
        print(f"Current Position: ({x}, {y})")
        print(f"Current Direction: {self.current_direction}")
        print(f"Previous Position: {self.previous_pos}")
        print(f"Waiting Time: {self.waiting_time}")
        print(f"Happiness Level: {self.happiness}")
        print(f"Current State: {self.state.value}")
        print(f"Destination: {self.destination}")
        print(f"Broken: {self.broken}")
        
        # Check road type
        road_type = "Unknown"
        if (x, y) in self.ns_roads:
            road_type = "North-South Road (Southbound only)"
        elif (x, y) in self.sn_roads:
            road_type = "South-North Road (Northbound only)"
        elif (x, y) in self.we_roads:
            road_type = "West-East Road (Eastbound only)"
        elif (x, y) in self.ew_roads:
            road_type = "East-West Road (Westbound only)"
        print(f"Road Type: {road_type}")
        
        # Get and print allowed directions
        allowed = self.get_valid_moves()
        print(f"Valid moves: {allowed}")
        
        # Check possible next positions
        for next_pos in allowed:
            print(f"Checking {next_pos}:")
            cell_contents = self.model.grid.get_cell_list_contents(next_pos)
            if any(isinstance(agent, Vehicle) for agent in cell_contents):
                print(f"  - Blocked by vehicle")
            else:
                print(f"  - Clear path")

    def check_traffic_light(self, next_pos):
        """Check if there's a red/yellow light blocking the path."""
        if not self.active:
            return False
            
        # If vehicle is angry, ignore traffic lights
        if self.state == VehicleState.ANGRY:
            return True
            
        current_direction = (next_pos[0] - self.pos[0], next_pos[1] - self.pos[1])
        next_cell = self.model.grid.get_cell_list_contents(next_pos)
        
        # First check if the cell is occupied by another vehicle
        if any(isinstance(agent, Vehicle) for agent in next_cell):
            return False
            
        # Then check for traffic lights in next position
        for cell in next_cell:
            if isinstance(cell, TrafficLight):
                if cell.state == LightState.RED or cell.state == LightState.YELLOW:
                    return False
        return True

    def check_adjacent_roads(self, pos):
        """Check for valid adjacent road segments."""
        if not self.active:
            return []
            
        x, y = pos
        valid_moves = []
        
        # Define adjacent positions
        adjacent = [
            (x+1, y), (x-1, y),  # East, West
            (x, y+1), (x, y-1)   # North, South
        ]
        
        current_direction = None
        if pos in self.ns_roads:
            current_direction = SOUTH
        elif pos in self.sn_roads:
            current_direction = NORTH
        elif pos in self.we_roads:
            current_direction = EAST
        elif pos in self.ew_roads:
            current_direction = WEST
            
        # Check each adjacent position
        for next_pos in adjacent:
            # Don't allow direct reversal of direction
            if current_direction:
                new_direction = (next_pos[0] - x, next_pos[1] - y)
                if new_direction == (-current_direction[0], -current_direction[1]):
                    continue
            
            # Check if it's a valid road segment and either angry or no red/yellow light
            if (next_pos in self.ns_roads or next_pos in self.sn_roads or 
               next_pos in self.we_roads or next_pos in self.ew_roads) and \
               self.check_traffic_light(next_pos):
                valid_moves.append(next_pos)
                
        return valid_moves

    def check_collision(self, pos):
        """Check if a position is occupied by another vehicle."""
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        return any(isinstance(agent, Vehicle) for agent in cell_contents)

    def check_breakdown(self):
        """Check if vehicle breaks down and spawn mechanic if needed."""
        if not self.broken and self.state != VehicleState.BROKEN:
            if self.random.random() < self.breakdown_chance:
                self.broken = True
                self.state = VehicleState.BROKEN
                self.color = "#000000"  # Black for broken vehicles
                
                # Find available spawn point for mechanic
                spawn_points = [agent for agent in self.model.agents if isinstance(agent, SpawnPoint)]
                available_points = [sp for sp in spawn_points 
                                 if not any(isinstance(agent, Vehicle) 
                                          for agent in self.model.grid.get_cell_list_contents(sp.pos))]
                
                if available_points:
                    spawn_point = self.random.choice(available_points)
                    mechanic = MechanicVehicle(self.model, spawn_point, self)
                    self.model.grid.place_agent(mechanic, spawn_point.pos)

    def get_valid_moves(self):
        """Get list of valid next positions."""
        if not self.active or self.broken:  # Don't move if broken
            return []
            
        x, y = self.pos
        
        # Handle specific coordinate rules
        if x == 15 and y == 10:
            next_pos = (15, 11)
            if not self.check_collision(next_pos) and self.check_traffic_light(next_pos):
                return [next_pos]
            return [(x, y)] if self.previous_pos != (x, y) else []
            
        if x == 15 and y == 11:
            valid_special = []
            possible_moves = [(14, 11), (15, 12)]
            for next_pos in possible_moves:
                if not self.check_collision(next_pos) and self.check_traffic_light(next_pos):
                    valid_special.append(next_pos)
            if valid_special:
                return valid_special
            return [(x, y)] if self.previous_pos != (x, y) else []
            
        if x == 12 and y == 12:
            next_pos = (12, 11)
            if not self.check_collision(next_pos) and self.check_traffic_light(next_pos):
                return [next_pos]
            return [(x, y)] if self.previous_pos != (x, y) else []
            
        if x == 13 and y == 12:
            next_pos = (13, 11)
            if not self.check_collision(next_pos) and self.check_traffic_light(next_pos):
                return [next_pos]
            return [(x, y)] if self.previous_pos != (x, y) else []
            
        if x == 13 and y == 11:
            next_pos = (12, 11)
            if not self.check_collision(next_pos) and self.check_traffic_light(next_pos):
                return [next_pos]
            return [(x, y)] if self.previous_pos != (x, y) else []
        
        valid_moves = []
        
        # Check if destination is adjacent
        destination_x, destination_y = self.destination
        if abs(x - destination_x) + abs(y - destination_y) == 1:
            if self.check_collision(self.destination) or not self.check_traffic_light(self.destination):
                return [(x, y)] if self.previous_pos != (x, y) else []
            return [self.destination]
        
        # If at spawn point, try spawn direction first
        if not self.has_made_first_move:
            dx, dy = self.spawn_point.direction
            next_pos = (x + dx, y + dy)
            if next_pos in self.ns_roads or next_pos in self.sn_roads or \
            next_pos in self.we_roads or next_pos in self.ew_roads:
                if self.check_collision(next_pos) or not self.check_traffic_light(next_pos):
                    return [(x, y)] if self.previous_pos != (x, y) else []
                return [next_pos]
        
        # Handle road-specific movements
        straight_move = None
        if (x, y) in self.ns_roads:
            straight_move = (x, y - 1)  # Move south
            if straight_move in self.ns_roads:
                if not self.check_traffic_light(straight_move) or self.check_collision(straight_move):
                    return [(x, y)] if self.previous_pos != (x, y) else []
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.sn_roads:
            straight_move = (x, y + 1)  # Move north
            if straight_move in self.sn_roads:
                if not self.check_traffic_light(straight_move) or self.check_collision(straight_move):
                    return [(x, y)] if self.previous_pos != (x, y) else []
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.we_roads:
            straight_move = (x + 1, y)  # Move east
            if straight_move in self.we_roads:
                if not self.check_traffic_light(straight_move) or self.check_collision(straight_move):
                    return [(x, y)] if self.previous_pos != (x, y) else []
                valid_moves.append(straight_move)
                        
        elif (x, y) in self.ew_roads:
            straight_move = (x - 1, y)  # Move west
            if straight_move in self.ew_roads:
                if not self.check_traffic_light(straight_move) or self.check_collision(straight_move):
                    return [(x, y)] if self.previous_pos != (x, y) else []
                valid_moves.append(straight_move)
        
        # Only check adjacent roads if no straight move is available
        if not valid_moves:
            adjacent_moves = self.check_adjacent_roads(self.pos)
            if adjacent_moves:
                valid_moves.extend(adjacent_moves)
            else:
                return [(x, y)] if self.previous_pos != (x, y) else []
        
        return valid_moves

    def step(self):
        """Execute one step of vehicle movement."""
        if not self.active:
            return
            
        # Check for breakdown before moving
        self.check_breakdown()
        
        if self.broken:
            return
            
        # Check if we've reached our destination
        if self.pos == self.destination:
            self.active = False
            self.model.grid.remove_agent(self)
            return
            
        valid_moves = self.get_valid_moves()
        
        if valid_moves:
            # If destination is in valid moves, prioritize it
            if self.destination in valid_moves:
                next_pos = self.destination
            else:
                # Sort valid moves by distance to destination
                valid_moves_with_distances = [
                    (pos, self.manhattan_distance(pos, self.destination))
                    for pos in valid_moves
                ]
                valid_moves_with_distances.sort(key=lambda x: x[1])  # Sort by distance
                
                # Choose from the moves that get us closest to destination
                best_distance = valid_moves_with_distances[0][1]
                best_moves = [pos for pos, dist in valid_moves_with_distances if dist == best_distance]
                
                # If multiple best moves, prefer continuing in same direction if possible
                same_direction_moves = [
                    pos for pos in best_moves
                    if (pos[0] - self.pos[0], pos[1] - self.pos[1]) == self.current_direction
                ]
                
                if same_direction_moves and self.random.random() < 0.7:  # 70% chance to continue straight
                    next_pos = self.random.choice(same_direction_moves)
                else:
                    next_pos = self.random.choice(best_moves)
                    
            self.previous_pos = self.pos
            self.current_direction = (
                next_pos[0] - self.pos[0],
                next_pos[1] - self.pos[1]
            )
            
            self.model.grid.move_agent(self, next_pos)
            self.waiting_time = 0
            self.update_happiness(is_moving=True)
            
            if not self.has_made_first_move:
                self.has_made_first_move = True
            
            # Increment steps taken after successful movement
            self.steps_taken += 1
        else:
            self.waiting_time += 1
            self.update_happiness(is_moving=False)
            
            if self.waiting_time > 40:
                self.color = "#FF00FF"  # Purple for stuck vehicles
                self.debug_position()  # Print debug info




class IntersectionModel(Model):
    """Enhanced intersection model with breakdown mechanics."""
    
    def __init__(self, width=24, height=24, vehicle_spawn_rate=0.3, min_vehicles=5, max_vehicles=40):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.vehicle_spawn_rate = vehicle_spawn_rate
        self.min_vehicles = min_vehicles
        self.max_vehicles = max_vehicles
        
        # Initialize the environment
        self.setup_intersection()
        
        # Enhanced data collection with mechanic metrics
        self.datacollector = DataCollector(
            model_reporters={
                "spawn_points": lambda m: len([a for a in m.agents if isinstance(a, SpawnPoint)]),
                "buildings": lambda m: len([a for a in m.agents if isinstance(a, Building)]),
                "traffic_lights": lambda m: len([a for a in m.agents if isinstance(a, TrafficLight)]),
                "vehicles": lambda m: len([a for a in m.agents if isinstance(a, Vehicle) and not isinstance(a, MechanicVehicle)]),
                "mechanics": lambda m: len([a for a in m.agents if isinstance(a, MechanicVehicle)]),
                "broken_vehicles": lambda m: len([a for a in m.agents if isinstance(a, Vehicle) and a.broken]),
                "green_lights": lambda m: len([a for a in m.agents if isinstance(a, TrafficLight) and a.state == LightState.GREEN]),
                "waiting_vehicles": lambda m: len([a for a in m.agents if isinstance(a, Vehicle) and a.waiting_time > 0]),
                "average_happiness": calculate_total_happiness,
                "angry_vehicles": lambda m: len([a for a in m.agents if isinstance(a, Vehicle) and a.state == VehicleState.ANGRY])
            }
        )
        
        self.running = True

    def setup_intersection(self):
        """Set up the initial state of the intersection."""
        self.create_buildings()
        self.create_traffic_lights()
        self.create_spawn_points()
        self.initialize_traffic_light_sequence()

    def initialize_traffic_light_sequence(self):
        """Initialize the traffic light sequence with offset starting states."""
        traffic_lights = [agent for agent in self.agents if isinstance(agent, TrafficLight)]
        
        # Group lights by their set
        light_sets = {}
        for light in traffic_lights:
            if light.light_set not in light_sets:
                light_sets[light.light_set] = []
            light_sets[light.light_set].append(light)
        
        # Set initial states with offsets for each group
        for set_id, lights in light_sets.items():
            initial_state = LightState.RED
            initial_time = 0
            
            # Set different initial states for each group to create an offset
            if set_id in [1, 4, 7]:  # First group starts with GREEN
                initial_state = LightState.GREEN
            elif set_id in [2, 5, 8]:  # Second group starts partway through RED
                initial_state = LightState.RED
                initial_time = 5
            elif set_id in [3, 6, 9]:  # Third group starts near end of RED
                initial_state = LightState.RED
                initial_time = 10
            
            # Apply the initial state to all lights in this set
            for light in lights:
                light.state = initial_state
                light.time_in_state = initial_time
                light.update_color()

    def create_spawn_points(self):
        """Create spawn points at specified locations, replacing existing buildings."""
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
            # First remove any existing agents at this position
            cell_contents = self.grid.get_cell_list_contents((x, y))
            for agent in cell_contents:
                self.grid.remove_agent(agent)
            
            # Then create and place the spawn point
            spawn_point = SpawnPoint(self, (x, y), direction, spawn_id)
            self.grid.place_agent(spawn_point, (x, y))

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
        
        # First clear all existing agents
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    cell_contents = self.grid.get_cell_list_contents((x, y))
                    for agent in cell_contents:
                        self.grid.remove_agent(agent)
        
        # Then place new buildings
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    building = Building(self, (x, y))
                    self.grid.place_agent(building, (x, y))
        
        # Handle central building (13,10 to 14,9)
        # First clear the area
        for x in range(13, 15):
            for y in range(9, 11):
                cell_contents = self.grid.get_cell_list_contents((x, y))
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
        
        # Then place the central building
        for x in range(13, 15):
            for y in range(9, 11):
                building = Building(self, (x, y))
                building.color = "brown"
                self.grid.place_agent(building, (x, y))

    def create_traffic_lights(self):
        """Create traffic light sets at specified coordinates."""
        traffic_light_sets = [
            # Set 1
            [(0, 6), (1, 6)],
            # Set 2
            [(2, 4), (2, 5)],
            # Set 3
            [(5, 0), (5, 1)],
            # Set 4
            [(6, 2), (7, 2)],
            # Set 5
            [(6, 16), (7, 16)],
            # Set 6
            [(6, 21), (7, 21)],
            # Set 7
            [(8, 22), (8, 23)],
            # Set 8
            [(17, 8), (17, 9)],
            # Set 9
            [(18, 7), (19, 7)],
            # Set 10
            [(8, 17), (8, 18)]
        ]

        # Clear and place traffic lights for each set
        for set_idx, light_positions in enumerate(traffic_light_sets, 1):
            for pos in light_positions:
                # Clear existing agents
                cell_contents = self.grid.get_cell_list_contents(pos)
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
                
                # Create and place traffic light
                traffic_light = TrafficLight(self, pos, set_idx)
                self.grid.place_agent(traffic_light, pos)

    def get_vehicle_count(self):
        """Get current number of vehicles in the model."""
        return len([agent for agent in self.agents if isinstance(agent, Vehicle)])

    def spawn_vehicles(self):
        """Attempt to spawn vehicles at spawn points while respecting min/max limits."""
        current_vehicles = self.get_vehicle_count()
        
        # If below minimum, force spawn until minimum is reached
        if current_vehicles < self.min_vehicles:
            spawn_points = [agent for agent in self.agents if isinstance(agent, SpawnPoint)]
            available_points = [sp for sp in spawn_points 
                              if not any(isinstance(agent, Vehicle) 
                                       for agent in self.grid.get_cell_list_contents(sp.pos))]
            
            while current_vehicles < self.min_vehicles and available_points:
                spawn_point = self.random.choice(available_points)
                vehicle = Vehicle(self, spawn_point)
                self.grid.place_agent(vehicle, spawn_point.pos)
                current_vehicles += 1
                available_points.remove(spawn_point)
        
        # If below maximum, allow random spawning based on rate
        elif current_vehicles < self.max_vehicles:
            spawn_points = [agent for agent in self.agents if isinstance(agent, SpawnPoint)]
            
            for spawn_point in spawn_points:
                if self.random.random() < self.vehicle_spawn_rate:
                    cell_contents = self.grid.get_cell_list_contents(spawn_point.pos)
                    if not any(isinstance(agent, Vehicle) for agent in cell_contents):
                        vehicle = Vehicle(self, spawn_point)
                        self.grid.place_agent(vehicle, spawn_point.pos)
                        current_vehicles += 1
                        
                        if current_vehicles >= self.max_vehicles:
                            break

    def step(self):
        """Advance the model by one step."""
        # First update traffic lights
        traffic_lights = [agent for agent in self.agents if isinstance(agent, TrafficLight)]
        for light in traffic_lights:
            light.step()
            
        # Then update vehicles one by one
        vehicles = [agent for agent in self.agents if isinstance(agent, Vehicle)]
        self.random.shuffle(vehicles)  # Randomize order to prevent bias
        for vehicle in vehicles:
            vehicle.step()
            
        # Finally spawn new vehicles
        self.spawn_vehicles()
        
        # Collect data
        self.datacollector.collect(self)
### 