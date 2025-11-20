from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector

from .agent import ObstacleAgent, RoombaRobot, DirtPatch, ChargingStation


class RandomModel(Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, num_agents=1, width=8, height=8, percent_dirty = 0.3, percent_obstacles = 0.05, max_steps = 3000, seed=42):

        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.seed = seed
        self.width = width
        self.height = height
        self.percent_dirty = percent_dirty
        self.percent_obstacles = percent_obstacles
        self.max_steps = max_steps

        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        self.initial_dirty_cells = 0 # cuántas celdas empezaron sucias
        self.cleaned_cells = 0 # cuántas se han limpiado

        # Configuramos el DataCollector con funciones para recolectar datos
        self.datacollector = DataCollector(
            model_reporters={
                # Cuántos parches siguen sucios
                "DirtyPatches": lambda m: sum(
                    1 for a in m.agents_by_type[DirtPatch] if a.dirty
                ),
                # Cuántos ya están limpios
                "CleanPatches": lambda m: sum(
                    1 for a in m.agents_by_type[DirtPatch] if not a.dirty
                ),
                # Batería del Roomba
                "Battery": lambda m: m.roomba.battery,
                # Movimientos acumulados
                "Moves": lambda m: m.roomba.moves,
            }
        )

        # Identify the coordinates of the border of the grid
        border = [(x,y)
                  for y in range(height)
                  for x in range(width)
                  if y in [0, height-1] or x in [0, width - 1]]

        # Create the border cells
        for _, cell in enumerate(self.grid):
            if cell.coordinate in border:
                ObstacleAgent(self, cell=cell)

        # Creamos los obstaculos internos aleatoriamente
        for cell in self.grid.all_cells:
            if cell.coordinate in border:
                continue  # ya tienen obstáculo

            if cell.coordinate == (1, 1):
                continue  # la estación de carga vive aquí

            if self.random.random() < self.percent_obstacles:
                ObstacleAgent(self, cell=cell)
        
        # Crear las celdas de suciedad aleatoriamente
        for cell in self.grid.all_cells:
            # No ensuciar obstáculo
            if any(isinstance(a, ObstacleAgent) for a in cell.agents):
                continue

            if self.random.random() < self.percent_dirty:
                DirtPatch(self, cell)
                self.initial_dirty_cells += 1

        # Crear la estación de carga en (1,1)
        home_cell = next(
            c for c in self.grid.all_cells if c.coordinate == (1, 1)
        )
        ChargingStation(self, cell=home_cell)

        self.roomba = RoombaRobot(
            model=self,
            cell=home_cell,
            battery=100,
            low_battery_threshold=20,
        )

        self.current_step = 0
        self.running = True
        self.datacollector.collect(self)

    # Definimos metodos para poder contar 

    def step(self):        
        self.current_step += 1
        self.agents.shuffle_do("step")
        # Determinar si toda la suciedad desapareció en cada paso
        dirt_left = sum(
        1 for a in self.agents_by_type[DirtPatch] if a.dirty
        )

        # Condiciones para terminar la simulación
        if self.current_step >= self.max_steps:
            self.running = False
            
        if self.roomba.state == "DEAD":
            self.running = False

        if dirt_left <= 0:
            self.running = False

        self.datacollector.collect(self)

        if self.running == False:
                print("------------------------------------------------")
                print("Simulación terminada en paso", self.current_step)
                cleaned = self.initial_dirty_cells - dirt_left
                print("Celdas limpiadas:", cleaned)
                print("Celdas restantes sucias:", dirt_left)
                print("Movimientos realizados:", self.roomba.moves)
                print("Batería restante:", self.roomba.battery)
                print("------------------------------------------------")
                return