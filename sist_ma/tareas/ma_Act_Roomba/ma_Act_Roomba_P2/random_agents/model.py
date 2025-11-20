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
    def __init__(self, num_agents, width=8, height=8, percent_dirty = 0.3, percent_obstacles = 0.05, max_steps = 3000, seed=42):

        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.seed = seed
        self.width = width
        self.height = height
        self.percent_dirty = percent_dirty
        self.percent_obstacles = percent_obstacles
        self.max_steps = max_steps

        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        self.initial_dirty_cells = 0 # Cuántas celdas empezaron sucias
        self.cleaned_cells = 0 # Cuántas se han limpiado

        # Data collector para recopilar estadísticas con funciones lambda. 
        self.datacollector = DataCollector(
            model_reporters={
                "CleanedPatches": lambda m: sum([1 for a in m.agents_by_type[DirtPatch] if not a.dirty]),  # Celdas limpiadas
                "DirtyPatches": lambda m: sum([1 for a in m.agents_by_type[DirtPatch] if a.dirty]),  # Celdas sucias
                "TotalMoves": lambda m: sum([a.moves for a in m.roombas]),  # Total de movimientos de los Roombas
                "AvgBattery": lambda m: sum([a.battery for a in m.roombas]) / len(m.roombas) if m.roombas else 0,  # Promedio de batería
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

        # Crear los agentes Roomba
        # Crear las diferentes Roombas y sus estaciones de carga
        self.roombas = []

        for _ in range(self.num_agents):
            # escoger una celda vacía para la estación de ese agente
            cell = self.random.choice(self.grid.empties.cells)

            # Crear estación de carga
            ChargingStation(self, cell=cell)
    
            # Crear roomba en esa misma celda
            roomba = RoombaRobot(
                model=self,
                cell=cell,
                battery=100,
                low_battery_threshold=20,
            )
            self.roombas.append(roomba)
            
        self.current_step = 0
        self.running = True


    def step(self):        
        self.current_step += 1
        # Actualizar cada Roomba
        for roomba in self.roombas:
            roomba.step()
        # Determinar si toda la suciedad desapareció en cada paso
        dirt_left = sum(1 for a in self.grid.all_cells if any(isinstance(agent, DirtPatch) and agent.dirty for agent in a.agents))

        # Condiciones para terminar la simulación
        if self.current_step >= self.max_steps:
            self.running = False
            
        contDead = 0
        for roomba in self.roombas:
            if roomba.state == "DEAD":
                contDead += 1

        if contDead == len(self.roombas):
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

                # Sumamos los movimientos y batería de todos los Roombas
                total_moves = sum(roomba.moves for roomba in self.roombas)
                avg_battery = sum(roomba.battery for roomba in self.roombas) / len(self.roombas)
                print("Movimientos realizados:", total_moves)
                print("Batería restante promedio:", avg_battery)
                print("------------------------------------------------")
                return