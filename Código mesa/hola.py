from model import IntersectionModel
from typing import Dict, List, Any
import json
from flask import Flask, jsonify

app = Flask(__name__)

# Initialize the model globally
model = IntersectionModel(
    width=24,
    height=24,
    vehicle_spawn_rate=0.3,
    min_vehicles=5,
    max_vehicles=20
)

def get_vehicle_data() -> List[Dict[str, Any]]:
    """Extract vehicle data from the model."""
    vehicles = []
    for agent in model.agents:
        if hasattr(agent, 'waiting_time'):  # Check if agent is a vehicle
            x, y = agent.pos
            vehicles.append({
                "id": agent.unique_id,
                "posX": x,
                "posY": y,
                "dirX": agent.current_direction[0],
                "dirY": agent.current_direction[1],
                "waiting_time": agent.waiting_time
            })
    return vehicles

def get_traffic_light_data() -> List[Dict[str, Any]]:
    """Extract traffic light data from the model."""
    lights = []
    for agent in model.agents:
        if hasattr(agent, 'light_set'):  # Check if agent is a traffic light
            lights.append({
                "id": agent.light_set,
                "state": agent.state.value,
                "position": agent.position
            })
    return lights

@app.route('/step', methods=['GET'])
def step():
    """Execute one step of the model and return the current state."""
    # Execute model step
    model.step()
    
    # Collect current state
    state = {
        "vehicles": get_vehicle_data(),
        "traffic_lights": get_traffic_light_data(),
        "statistics": {
            "total_vehicles": len([a for a in model.agents if hasattr(a, 'waiting_time')]),
            "waiting_vehicles": len([a for a in model.agents if hasattr(a, 'waiting_time') and a.waiting_time > 0]),
            "green_lights": len([a for a in model.agents if hasattr(a, 'light_set') and a.state.value == 'green'])
        }
    }
    
    return jsonify(state)

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the model to initial state."""
    global model
    model = IntersectionModel(
        width=24,
        height=24,
        vehicle_spawn_rate=0.3,
        min_vehicles=5,
        max_vehicles=40
    )
    return jsonify({"status": "Model reset successfully"})

if __name__ == '__main__':
    app.run(debug=True)