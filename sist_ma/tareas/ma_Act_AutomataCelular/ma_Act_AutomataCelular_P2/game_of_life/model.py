from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell

# El modelo se encarga de que se ejecuten las acciones de cada agente, define el ambiente donde estan los agentes.

class ConwaysGameOfLife(Model):
    """Represents the 2-dimensional array of cells in Conway's Game of Life."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None): # Importante para poder actualizar el modelo.
        """Create a new playing area of (width, height) cells."""
        super().__init__(seed=seed)

        """Grid where cells are connected to their 8 neighbors.

        Example for two dimensions:
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        ]
        """
        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=True)

        # Place a cell at each location, with some initialized to
        # ALIVE and some to DEAD.
        # Solo para la primera fila de celdas en la simulación.

        self.cell_grid = {}

        self.current_row = height - 1  # Comenzar desde la ultima fila (height - 1)

        for cell in self.grid.all_cells:
            Cell(
                self,
                cell,
                init_state=(
                    Cell.ALIVE
                    if self.random.random() < initial_fraction_alive
                    else Cell.DEAD
                ),
            )

        self.running = True


    def step(self):
        # Realizar el paso del modelo en dos etapas:
        self.agents.do("determine_state")
        self.agents.do("assume_state")
