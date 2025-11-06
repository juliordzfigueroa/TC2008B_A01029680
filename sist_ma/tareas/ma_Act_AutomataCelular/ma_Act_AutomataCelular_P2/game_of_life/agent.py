# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent # No le permitas mover este agente con FixedAgent

class Cell(FixedAgent): # La clase de celula esta heredando los comportamientos base de FixedAgent
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    @property # Para dar comportamiento adicional, como getter y setter
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD): # Constructor de la clase Cell
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model) # Manda a llamar el constructor de la clase padre FixedAgent con el modelo como parametro
        # Marca atributos de la clase Cell usando self.xxxxxx
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick.  This is
        based on the number of alive or dead neighbors.  The state is not
        changed here, but is just computed and stored in self._nextState,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        """
        # Get the neighbors and apply the rules on whether to be alive or dead
        # Se crean los registros de los 3 vecinos de arriba vivos
        top_neighbors = self.get_UpNeighbors()
        # Assume nextState is unchanged, unless changed below.
        self._next_state = self.state

        # Creamos variables booleanas para revisar si los vecinos de arriba estan vivos o muertos
        a0 = getattr(top_neighbors[0], 'is_alive', False)
        a1 = getattr(top_neighbors[1], 'is_alive', False)
        a2 = getattr(top_neighbors[2], 'is_alive', False)

        if a0 and a1 and a2: # Caso 1: 111
            self._next_state = self.DEAD
        elif a0 and a1 and not a2: # Caso 2: 110
            self._next_state = self.ALIVE
        elif a0 and not a1 and a2: # Caso 3: 101
            self._next_state = self.DEAD
        elif a0 and not a1 and not a2: # Caso 4: 100
            self._next_state = self.ALIVE
        elif not a0 and a1 and a2: # Caso 5: 011
            self._next_state = self.ALIVE
        elif not a0 and a1 and not a2: # Caso 6: 010
            self._next_state = self.DEAD
        elif not a0 and not a1 and a2: # Caso 7: 001
            self._next_state = self.ALIVE
        else: # Caso 8: 000
            self._next_state = self.DEAD
            

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        if self._next_state is not None:
            self.state = self._next_state
            self._next_state = None

    def get_UpNeighbors(self):
        """Regresa los 3 vecinos de arriba de la celda actual"""
        neighbors = self.neighbors
        top_neighbors = [None, None, None] # Inicializa la lista de vecinos de arriba

        # Usar modulo para considerar el grid con el torus solo de manera vertical.
        height = self.model.grid.height
        width = self.model.grid.width

        target_y = (self.y + 1) % height # La fila de arriba

        if target_y >= height:
            return top_neighbors
    
        left_x = self.x - 1

        mid_x = self.x % width
        right_x = self.x + 1

        for neighbor in neighbors:
            nx, ny = neighbor.cell.coordinate
            if ny == target_y and nx == left_x:
                top_neighbors[0] = neighbor
            elif ny == target_y and nx == mid_x:
                top_neighbors[1] = neighbor
            elif ny == target_y and nx == right_x:
                top_neighbors[2] = neighbor

        return top_neighbors
        
