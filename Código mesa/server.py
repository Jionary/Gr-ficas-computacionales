from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import numpy as np
from model import IntersectionModel

def agent_portrayal(agent):
    """Define how to portray each type of agent in the visualization."""
    portrayal = {
        "color": agent.color,
        "marker": "s",  # Square marker for all agents
        "size": 100  # Same size for all agents
    }
    return portrayal

def post_process_grid(ax):
    """Customize the grid plot appearance."""
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(-0.5, 23.5)
    ax.grid(True, linestyle='-', alpha=0.3)
    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_yticks(np.arange(0, 24, 1))
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.set_xlabel('X Coordinate (0-23)', fontsize=10)
    ax.set_ylabel('Y Coordinate (0-23)', fontsize=10)
    ax.tick_params(axis='x', rotation=45)

def post_process_happiness(ax):
    """Customize the happiness plot appearance."""
    ax.set_title("Vehicle Happiness Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Happiness Level (0-100)")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylim(0, 100)
    
    # Apply styling to lines after they're created
    for line in ax.get_lines():
        line.set_color("#2ecc71")
        line.set_linewidth(2)

def post_process_vehicles(ax):
    """Customize the vehicles plot appearance."""
    ax.set_title("Number of Vehicles")
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")
    ax.grid(True, linestyle='--', alpha=0.7)
    
    for line in ax.get_lines():
        line.set_color("#3498db")
        line.set_linewidth(2)

def post_process_angry(ax):
    """Customize the angry vehicles plot appearance."""
    ax.set_title("Number of Angry Vehicles")
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")
    ax.grid(True, linestyle='--', alpha=0.7)
    
    for line in ax.get_lines():
        line.set_color("#e74c3c")
        line.set_linewidth(2)

# Create model params
model_params = {
    "width": 24,
    "height": 24,
    "vehicle_spawn_rate": {
        "type": "SliderFloat",
        "value": 0.3,
        "min": 0.1,
        "max": 0.9,
        "step": 0.1,
        "label": "Vehicle Spawn Rate"
    },
    "min_vehicles": {
        "type": "SliderInt",
        "value": 1,
        "min": 1,
        "max": 40,
        "step": 1,
        "label": "Minimum Vehicles"
    },
    "max_vehicles": {
        "type": "SliderInt",
        "value": 6,
        "min": 5,
        "max": 40,
        "step": 1,
        "label": "Maximum Vehicles"
    }
}

# Create model instance
model = IntersectionModel()

# Create visualizations
space = make_space_component(
    agent_portrayal,
    post_process=post_process_grid,
    draw_grid=True
)

# Create the plots with proper parameters
happiness_plot = make_plot_component(
    measure="average_happiness",
    post_process=post_process_happiness
)

vehicles_plot = make_plot_component(
    measure="vehicles",
    post_process=post_process_vehicles
)

angry_vehicles_plot = make_plot_component(
    measure="angry_vehicles",
    post_process=post_process_angry
)

# Create the visualization page with all components
page = SolaraViz(
    model,
    [space, happiness_plot, vehicles_plot, angry_vehicles_plot],
    model_params=model_params,
    name="Traffic Grid Layout with Happiness Tracking"
)

if __name__ == "__main__":
    page  # noqa