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
            x, y = cell.coordinate
            init_state = (
                Cell.ALIVE
                if (y == self.current_row and self.random.random() < initial_fraction_alive) # Solo la fila inicial
                else Cell.DEAD
            )
            agent = Cell(
                self,   # modelo
                cell,   # celda 
                init_state=init_state,
            )
            # Acceso rápido por coordenadas
            self.cell_grid[(x, y)] = agent

        self.running = True


    def step(self):
        # Detener la simulacion cuando se llegue a la fila 0
        if self.current_row <= 0:
            self.running = False
            return

        width = self.grid.width
        
        # Actualizar la fila actual
        previous_row = self.current_row
        next_row = self.current_row - 1

        # Primero determinar el estado de la siguiente fila
        for x in range(width):
            next_agent = self.cell_grid[(x, next_row)]
            next_agent.determine_state()

        # Ahora actualizar el estado de la siguiente fila
        for x in range(width):
            next_agent = self.cell_grid[(x, next_row)]
            next_agent.assume_state()

        self.current_row = next_row

