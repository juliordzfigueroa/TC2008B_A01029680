# from game_of_life.model import ConwaysGameOfLife
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def agent_portrayal(agent):
    return AgentPortrayalStyle(
        color="white" if agent.state == 0 else "black", # DEAD is 0, ALIVE is 1 
        marker="s", # square
        size=30,
    )

def post_process(ax): # Para quitar los ejes y los numeros de las graficas
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

model_params = { # Diccionario con los parametros del modelo, un json.
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": {
        "type": "SliderInt",
        "value": 50,
        "label": "Width",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 50,
        "label": "Height",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "initial_fraction_alive": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Cells initially alive",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
}

# Create initial model instance
gof_model = ConwaysGameOfLife() 

space_component = make_space_component( # Visualizacion del espacio
        agent_portrayal,
        draw_grid = False, # No dibujar la cuadricula de mathplotlib
        post_process=post_process
)

page = SolaraViz( # Controlar el modelo
    gof_model,
    components=[space_component],
    model_params=model_params,
    name="Game of Life",
)
