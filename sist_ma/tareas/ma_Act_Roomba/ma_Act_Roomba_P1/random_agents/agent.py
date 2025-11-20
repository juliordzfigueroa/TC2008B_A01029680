from mesa.discrete_space import CellAgent, FixedAgent
import heapq # Para la implementación del algoritmo de A*

# Se crean las clases de los obstaculos y estaciones de carga

class DirtPatch(FixedAgent):
    """
    Celda de suciedad. El Robot Roomba puede limpiarla.
    """
    def __init__(self, model, cell, dirty=True):
        super().__init__(model)
        self.cell = cell
        self.dirty = dirty  # True = sucia, False = limpia

    def step(self):
        # No hace nada por sí misma, solo espera a ser limpiada
        pass


class ChargingStation(FixedAgent):
    """
    Estación de carga. El Robot Roomba que esté aquí puede recargar batería.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass

class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid. Usado en el borde del grid y en obstáculos internos.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class RoombaRobot(CellAgent):
    """
    Agente de que simula ser un Robot Roomba.
    - Tiene batería
    - Puede moverse, limpiar y recargar
    - Cambia de estado dependiendo de la batería, si está baja priorizará recargar sobre limpiar
    """
    def __init__(self, model, cell, battery=100, low_battery_threshold=30):
        super().__init__(model)
        self.cell = cell
        self.battery = battery
        self.low_battery_threshold = low_battery_threshold
        self.moves = 0  # Para estadísticas
        self.home_cell = cell  # Estación inicial [1,1]
        self.homepos = cell.coordinate
        self.state = "EXPLORING"  # EXPLORING, CHARGING, CRITICAL, DEAD. Empezamos limpiando y cambiaremos dependiendo de la batería
        # Para el mapa interno del Roomba (no implementado en esta versión)
        self.known_cells = {cell.coordinate: cell} 
        self.known_graph = {cell.coordinate: set()} 
        # Saber cuáles celdas ha visitado
        self.visited_positions = set([cell.coordinate])

        self.update_knowledge()

    # Definimos getters para las acciones del Roomba, saber si cambiar de estado o limpiar una celda.
    
    def current_DirtyPatch(self):
        """
        Regresa la celda de suciedad en la que está el Roomba, o None si no hay ninguna
        """
        for agent in self.cell.agents:
            if isinstance(agent, DirtPatch) and agent.dirty:
                return agent
        return None
    
    def on_ChargingStation(self):
        """
        Regresa True si el Roomba está en una estación de carga, False en caso contrario
        """
        for agent in self.cell.agents:
            if isinstance(agent, ChargingStation):
                return True
        return False
    
    def neighbors_Without_Obstacles(self):
        """
        Regresa las celdas vecinas que no tienen obstáculos para desplazarse
        """
        return self.cell.neighborhood.select(
        lambda cell: not any(isinstance(agent, ObstacleAgent) for agent in cell.agents)
        )
    
    def is_Battery_Low(self):
        """
        Regresa True si la batería está baja, False en caso contrario
        """
        current_coord = self.cell.coordinate
        path_home = self.a_star(current_coord, self.homepos)
        if path_home is None:
            # si no hay camino conocido, ser conservador
            return self.battery <= self.low_battery_threshold

        dist_home = len(path_home) - 1  # pasos mínimos para regresar
        margen = 3 # Margen de bateria que se quiere tener al llegar, no llegar justo a 0
        return self.battery <= (dist_home + margen)
    
    def consume_Battery(self, amount = 1): # Definido como consumo por acción, ya sea moverse o limpiar
        """
        Consume la cantidad de batería especificada
        """
        self.battery = max(0, self.battery - amount)

    # Para poder actualizar el mapa interno del Roomba

    def update_knowledge(self):
        """
        Actualiza el grafo interno con:
        - la celda actual
        - sus vecinos libres de obstáculos
        """
        current_coord = self.cell.coordinate

        # Aseguramos que la celda actual está en el diccionario
        if current_coord not in self.known_cells:
            self.known_cells[current_coord] = self.cell

        # Aseguramos que la celda actual tiene una entrada en el grafo
        if current_coord not in self.known_graph:
            self.known_graph[current_coord] = set()

        # Agregamos los vecinos libres de obstáculos
        neighbors = self.neighbors_Without_Obstacles()
        for n_cell in neighbors:
            n_coord = n_cell.coordinate
            # Guardar celda y aristas en ambos sentidos
            if n_coord not in self.known_cells:
                self.known_cells[n_coord] = n_cell

            if n_coord not in self.known_graph:
                self.known_graph[n_coord] = set()

            self.known_graph[current_coord].add(n_coord)
            self.known_graph[n_coord].add(current_coord)

    def a_star(self, start, goal): # Para encontrar el camino más optimo a la estación de recarga.
        dist = {node: float("inf") for node in self.known_graph} # Distancia inicial infinita hacia cada nodo
        prev = {node: None for node in self.known_graph} # Nodo previo en el camino más corto
        dist[start] = 0 # Distancia al nodo inicial es 0

        heap = [(0, start)]  # (distancia, nodo)

        while heap: # mientras haya nodos por explorar
            current_dist, u = heapq.heappop(heap)
            if current_dist > dist[u]:
                continue
            if u == goal:
                break

            for v in self.known_graph[u]:
                alt = current_dist + 1  # costo uniforme 1 por paso
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))

        if dist[goal] == float("inf"):
            return None

        # Reconstruir el camino
        path = []
        node = goal
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path
    
    # Métodos auxiliares para las acciones del Roomba despues de recargarse

    def get_pending_positions(self):
        """
        Regresa una lista de coordenadas que el robot conoce pero que aún no ha visitado.
        """
        pending = [
            coord for coord in self.known_cells.keys()
            if coord not in self.visited_positions
            and coord in self.known_graph # Se revisa que esten en el grafo conocido
        ]
        return pending
    
    # Definimos las acciones del Roomba: moverse, limpiar y recargar
        
    def move(self):
        """
        Mueve al robot un paso hacia alguna celda pendiente por explorar si es que no hay celdas sucias en la vecindad,
        usando A*. Si no hay pendientes alcanzables, se mueve de manera aleatoria.
        """
        neighbors = self.neighbors_Without_Obstacles()
        dirty_cells = [cell for cell in neighbors if any(isinstance(a, DirtPatch) and a.dirty for a in cell.agents)]
        if dirty_cells:  # Prioriza moverse a celdas sucias en vecindad
            next_cell = self.random.choice(dirty_cells)
            self.cell = next_cell
            self.moves += 1
            self.visited_positions.add(next_cell.coordinate)
            self.update_knowledge()
            self.consume_Battery()
            dirty_cells.remove(next_cell)
            return
        
        # Si no hay celdas sucias en vecindad, buscar pendientes
        unvisited = [cell for cell in neighbors if cell.coordinate not in self.visited_positions]
        if unvisited:
            # Moverse a una celda no visitada
            next_cell = self.random.choice(unvisited)
            self.cell = next_cell
            self.moves += 1
            self.visited_positions.add(next_cell.coordinate)
            self.update_knowledge()
            self.consume_Battery()
            unvisited.remove(next_cell)
            return
        
        # Si no hay celdas no visitadas en vecindad, usar A* para ir a la más cercana pendiente
        pending_positions = self.get_pending_positions()
        if pending_positions:
            best_path = None
            for goal in pending_positions:
                path = self.a_star(self.cell.coordinate, goal)
                if path is not None: # Si hay un camino
                    if best_path is None or len(path) < len(best_path):
                        best_path = path
                
            if best_path:
                next_coord = best_path[1]  # Siguiente paso en el camino
                next_cell = self.known_cells.get(next_coord)
                if next_cell:
                    self.cell = next_cell
                    self.moves += 1
                    self.visited_positions.add(next_cell.coordinate)
                    self.update_knowledge()
                    self.consume_Battery()
                    return
                
        # Si no hay pendientes alcanzables, moverse aleatoriamente
        self.move_Random()

    # Para moverse aleatoriamente
    def move_Random(self):
        """
        Para moverse aleatoriamente a una celda vecina sin obstaculos
        """
        neighbors_collection = self.neighbors_Without_Obstacles()
        neighbors = list(neighbors_collection.cells)
        if not neighbors:
            return  # No hay movimiento posible
        next_cell = self.random.choice(neighbors)
        self.cell = next_cell
        self.moves += 1
        self.visited_positions.add(next_cell.coordinate)
        self.update_knowledge()
        self.consume_Battery()

    def clean(self):
        """
        Limpia la celda de suciedad en la que está el Roomba
        """
        dirt_patch = self.current_DirtyPatch()
        if dirt_patch and dirt_patch.dirty:
            dirt_patch.dirty = False
            self.consume_Battery()
            if hasattr(self.model, "cleaned_cells"):
                self.model.cleaned_cells += 1

    def recharge(self):
        """
        Recarga la batería del Roomba solo 5%
        """
        if self.on_ChargingStation():
            self.battery = self.battery + 5  # Recarga parcial

    def move_to_Charge(self):
        """
        Mueve al Roomba a su estación de carga
        """
        # Si ya está sobre una estación, cambiar a CHARGING
        if self.on_ChargingStation():
            self.state = "CHARGING"
            self.current_path = []  # Limpiar camino actual
            return

        current_coord = self.cell.coordinate
        goal = self.homepos
        path = self.a_star(current_coord, goal)

        if path is None or len(path) < 2:  # No hay camino o ya estamos en la estación
            self.move_Random()
            return

        # Usamos el siguiente paso en el camino encontrado
        next_coord = path[1]
        next_cell = self.known_cells.get(next_coord)

        if next_cell is None:
            self.move_Random()
            return

        self.cell = next_cell
        self.moves += 1
        self.consume_Battery()
        self.update_knowledge()


    def step(self):
        """
        Determines the new direction it will take, and then moves
        """
        if (self.battery == 0): # Si la batería está agotada, el Roomba muere
            self.state = "DEAD"
            return
        
        if self.state == "EXPLORING":
            # Prioriza recargar si la batería está baja
            if self.is_Battery_Low():
                self.state = "CRITICAL"
                self.current_path = []  # Limpiar camino actual
            else: # Sigue explorando y limpiando
                dirt_patch = self.current_DirtyPatch()
                if dirt_patch and dirt_patch.dirty:
                    self.clean()
                else:
                    self.move() # Moverse a celdas no visitadas o aleatoriamente

        elif self.state == "CHARGING":
            if self.battery >= 100:
                self.state = "EXPLORING"
            else:
                self.recharge()

        elif self.state == "CRITICAL":
            self.move_to_Charge()