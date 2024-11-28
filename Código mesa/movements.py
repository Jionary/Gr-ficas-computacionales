from typing import Dict, List, Tuple, Set

# Define movement vectors
NORTH = (0, 1)   # Move up
SOUTH = (0, -1)  # Move down
EAST = (1, 0)    # Move right
WEST = (-1, 0)   # Move left
def create_road_segments() -> Dict[str, List[Tuple[int, int]]]:
    """Create dictionary of road segments with directional information."""
    return {
        # North to South Roads (y decreasing)
        'NS1': [(1, y) for y in range(22, 1, -1)], # Leftmost NS road - single lane
        'NS2': [(6, y) for y in range(7, 1, -1)] + [(7, y) for y in range(7, 1, -1)], # Left-middle NS road
        'NS3': [(12, y) for y in range(21, 11, -1)] + [(13, y) for y in range(21, 11, -1)], # Middle NS road upper
        'NS4': [(12, y) for y in range(7, 1, -1)] + [(13, y) for y in range(7, 1, -1)], # Middle NS road lower
        'NS5': [(12, y) for y in range(10, 8, -1)], # Middle NS road connector
        
        # South to North Roads (y increasing)
        'SN1': [(22, y) for y in range(1, 22)], # Rightmost SN road - single lane
        'SN2': [(18, y) for y in range(2, 8)] + [(19, y) for y in range(2, 8)], # Right-middle SN road
        'SN3': [(14, y) for y in range(2, 8)] + [(15, y) for y in range(2, 8)], # Middle SN road lower
        'SN4': [(14, y) for y in range(12, 22)] + [(15, y) for y in range(12, 22)], # Middle SN road upper
        'SN5': [(6, y) for y in range(12, 22)] + [(7, y) for y in range(12, 22)], # Left-middle SN road upper
        'SN6': [(15, y) for y in range(9, 11)], # Middle SN road connector
        
        # West to East Roads (x increasing)
        'WE1': [(x, 1) for x in range(1, 23)], # Bottom WE road - single lane
        'WE2': [(x, 5) for x in range(8, 12)] + [(x, 4) for x in range(8, 12)], # Lower middle WE road
        'WE3': [(x, 9) for x in range(2, 12)] + [(x, 8) for x in range(2, 12)], # Middle WE road left
        'WE4': [(x, 9) for x in range(16, 22)] + [(x, 8) for x in range(16, 22)], # Middle WE road right
        'WE5': [(x, 8) for x in range(12, 16)], # Middle WE road connector
        'WE6': [(x, 11) for x in range(12, 16)], # Upper middle connector
        
        # East to West Roads (x decreasing)
        'EW1': [(x, 22) for x in range(22, 0, -1)], # Top EW road - single lane
        'EW2': [(x, 17) for x in range(21, 15, -1)] + [(x, 16) for x in range(21, 15, -1)], # Upper middle EW road
        'EW3': [(x, 11) for x in range(21, 15, -1)] + [(x, 10) for x in range(21, 15, -1)], # Middle EW road right
        'EW4': [(x, 11) for x in range(11, 1, -1)] + [(x, 10) for x in range(11, 1, -1)], # Middle EW road left
        'EW5': [(x, 5) for x in range(5, 1, -1)] + [(x, 4) for x in range(5, 1, -1)] # Lower EW road
    }

def create_movement_rules() -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """Create movemeant rules dictionary based on road segments."""
    rules = {}
    road_segments = create_road_segments()
    
    # Helper function to determine road direction
    def get_road_direction(road_name: str) -> Tuple[int, int]:
        if road_name.startswith('NS'):
            return SOUTH
        elif road_name.startswith('SN'):
            return NORTH
        elif road_name.startswith('EW'):
            return WEST
        elif road_name.startswith('WE'):
            return EAST
        return (0, 0)

    # Create set of all road coordinates for quick lookup
    road_coords: Set[Tuple[int, int]] = set()
    for segments in road_segments.values():
        road_coords.update(segments)

    # Process each road segment
    for road_name, coordinates in road_segments.items():
        main_direction = get_road_direction(road_name)
        
        for coord in coordinates:
            if coord not in rules:
                rules[coord] = []
            
            # Add main direction
            if main_direction not in rules[coord]:
                rules[coord].append(main_direction)
            
            # Add perpendicular movements at intersections
            x, y = coord
            perpendicular_moves = []
            if main_direction in [NORTH, SOUTH]:
                perpendicular_moves = [(1, 0), (-1, 0)]  # East and West
            elif main_direction in [EAST, WEST]:
                perpendicular_moves = [(0, 1), (0, -1)]  # North and South
            
            # Check if perpendicular moves lead to valid road cells
            for move in perpendicular_moves:
                new_pos = (x + move[0], y + move[1])
                if new_pos in road_coords and move not in rules[coord]:
                    rules[coord].append(move)

    return rules

def get_valid_moves(x: int, y: int) -> List[Tuple[int, int]]:
    """Returns list of valid moves for a given position."""
    return _movement_rules.get((x, y), [])

def find_intersections() -> List[Tuple[int, int]]:
    """Find all road intersections."""
    road_segments = create_road_segments()
    all_coordinates = set()
    intersections = set()
    
    for coordinates in road_segments.values():
        for coord in coordinates:
            if coord in all_coordinates:
                intersections.add(coord)
            all_coordinates.add(coord)
    
    return sorted(list(intersections))

def is_valid_direction(current_pos: Tuple[int, int], next_pos: Tuple[int, int]) -> bool:
    """Check if movement between positions follows road rules."""
    if current_pos not in _movement_rules:
        return False
        
    movement = (next_pos[0] - current_pos[0], next_pos[1] - current_pos[1])
    return movement in _movement_rules[current_pos]

# Initialize movement rules when module is imported
_movement_rules = create_movement_rules()