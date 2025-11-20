from random_agents.agent import RoombaRobot, ObstacleAgent, DirtPatch, ChargingStation # Importar las clases necesarias de nuestros agentes
from random_agents.model import RandomModel # Importar el modelo

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, ChargingStation):
        portrayal.color = "blue"
        portrayal.marker = "s"
        portrayal.size = 80
    elif isinstance(agent, RoombaRobot):
        if agent.state != "DEAD":
            portrayal.color = "red"
            portrayal.size = 70
        else:
            portrayal.color = "black"
            portrayal.size = 70
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "gray"
        portrayal.marker = "s"
        portrayal.size = 100
    elif isinstance(agent, DirtPatch):
        if agent.dirty:
            portrayal.color = "brown" # sucia
            portrayal.size = 50
        else:
            portrayal.color = "white" # limpia
            portrayal.size = 50

    return portrayal

def post_process(ax):
    ax.set_aspect("equal")

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    }, 
    "width": Slider("Grid width", 28, 1, 50),
    "height": Slider("Grid height", 28, 1, 50),
    "percent_dirty": Slider("Percentage of dirty patches", 0.3, 0.0, 1.0, 0.05),
    "percent_obstacles": Slider("Percentage of obstacle patches", 0.05, 0.0, 0.3, 0.05),
    "max_steps": Slider("Maximum steps", 3000, 1000, 10000, 1000),
}

# Create the model using the initial parameters from the settings
model = RandomModel(
    width=model_params["width"].value,
    height=model_params["height"].value,
    seed=model_params["seed"]["value"]
)

space_component = make_space_component(
        random_portrayal,
        draw_grid = False,
        post_process=post_process
)

plot_component = make_plot_component(
    [
        "Moves",
        "DirtyPatches",
        "CleanPatches",
        "Battery", 
    ]
)

page = SolaraViz(
    model,
    components=[space_component, plot_component],
    model_params=model_params,
    name="Random Model",
)
