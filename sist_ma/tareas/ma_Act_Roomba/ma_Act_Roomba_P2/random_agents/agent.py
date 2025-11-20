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
        self.isOccupied = False  # Inicializamos como no ocupada

    def step(self):
        # Verificamos si algún Roomba está en la estación de carga
        self.isOccupied = any(isinstance(a, RoombaRobot) for a in self.cell.agents) == True

class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid. Usado en el borde del grid y en obstáculos internos.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

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
        self.home_cell = cell  # Celda inicial del Roomba
        self.homepos = cell.coordinate
        self.state = "EXPLORING"  # EXPLORING, CHARGING, CRITICAL, DEAD. Empezamos limpiando y cambiaremos dependiendo de la batería
        # Para el mapa interno del Roomba
        self.known_cells = {cell.coordinate: cell} 
        self.known_graph = {cell.coordinate: set()} 
        # Saber cuáles celdas ha visitado
        self.visited_positions = set()
        self.visited_positions.add(cell.coordinate)
        # Para el camino actual hacia una celda objetivo
        self.current_path = []

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
    
    def get_known_stations(self):
        """
        Regresa una lista de coordenadas donde el robot sabe
        que hay estaciones de carga.
        """
        stations = []
        for coord, cell in self.known_cells.items():
            if any(isinstance(a, ChargingStation) for a in cell.agents):
                stations.append(coord)
        return stations
    
    def get_closest_station_path(self):
        """
        Usa A* para encontrar el camino más corto a la
        estación de carga conocida más cercana.
        Regresa la lista de coordenadas o None si no hay camino.
        """
        current_coord = self.cell.coordinate
        stations = self.get_known_stations() # A partir de la coordenada actual, buscar estaciones conocidas

        best_path = None

        for goal in stations:  # Recorrer cada estación conocida
            if goal not in self.known_graph: 
                continue

            path = self.a_star(current_coord, goal)
            if path is None or len(path) < 1:
                continue

            if best_path is None or len(path) < len(best_path):
                best_path = path

        return best_path
    
    def is_Battery_Low(self):
        """
        Regresa True si la batería está baja, False en caso contrario
        """
        # Buscar en el mapa interno el camino a la estación de carga más cercana, sea la de el o no
        path = self.get_closest_station_path()
        if path is None:
            # si no hay camino conocido, ser conservador
            return self.battery <= self.low_battery_threshold

        dist_home = len(path)  # Pasos necesarios para llegar a la estación
        margen = 1 # Margen de bateria que se quiere tener al llegar, no llegar justo a 0
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

        if current_coord not in self.known_graph:
            self.known_graph[current_coord] = set()

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

    # Si el roomba se encuentra con otro puede intercambiar información de su mapa interno
    def merge_knowledge_from(self, other):
        """
        Fusiona el mapa conocido de 'other' dentro del del propio robot.
        Esta acción no consume batería.
        """
        # Celdas conocidas
        for coord, cell in other.known_cells.items():
            if coord not in self.known_cells:
                self.known_cells[coord] = cell

        # Grafo conocido
        for coord, neighbors in other.known_graph.items():
            if coord not in self.known_graph:
                self.known_graph[coord] = set()
            self.known_graph[coord] |= neighbors  # Une los conjuntos de ambos robots

    def share_knowledge(self):
        """
        Comparte conocimiento con otros Roombas que estén en los vecinos de uno.
        Esta acción no consume batería.
        """
        # Ver todos los agentes vecinos
        for cell in self.neighbors_Without_Obstacles():
            for agent in cell.agents:
                if isinstance(agent, RoombaRobot) and agent is not self:
                    # Intercambiar conocimiento
                    self.merge_knowledge_from(agent)
                    agent.merge_knowledge_from(self)

    # Para encontrar el camino más optimo a la estación de recarga.
    def a_star(self, start, goal):
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
        
        # Prioriza moverse a celdas sucias en vecindad
        if dirty_cells:  
            next_cell = self.random.choice(dirty_cells)
            self.cell = next_cell
            self.moves += 1
            self.visited_positions.add(next_cell.coordinate)
            self.update_knowledge()
            self.consume_Battery()
            return

        # Si no hay celdas sucias en vecindad, buscar pendientes
        unvisited = [cell for cell in neighbors if cell.coordinate not in self.visited_positions]
        if unvisited:
            next_cell = self.random.choice(unvisited)
            self.cell = next_cell
            self.moves += 1
            self.visited_positions.add(next_cell.coordinate)
            self.update_knowledge()
            self.consume_Battery()
            return

        # Si no hay celdas no visitadas en vecindad, usar A* para ir a la más cercana pendiente
        pending_positions = self.get_pending_positions()
        if pending_positions:
            best_path = None
            for goal in pending_positions:
                path = self.a_star(self.cell.coordinate, goal)
                if path is not None:  # Si hay un camino
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
        Limpia la celda de suciedad en la que está el Roomba.
        """
        dirt_patch = self.current_DirtyPatch()
        if dirt_patch and dirt_patch.dirty:
            dirt_patch.dirty = False  # Cambia el estado de la suciedad a limpio
            self.consume_Battery()  # Consumir batería al limpiar
            if hasattr(self.model, "cleaned_cells"):
                self.model.cleaned_cells += 1  # Aumentar el contador de celdas limpiadas

    def recharge(self):
        """
        Recarga la batería del Roomba solo 5%
        """
        if self.on_ChargingStation():
            self.battery = self.battery + 5  # Recarga parcial

    def move_to_Charge(self):
        """
        Mueve al Roomba a su estación de carga más cercana usando A*.
        """
        # Si ya está sobre una estación, cambiar a CHARGING
        if self.on_ChargingStation():
            self.state = "CHARGING"
            # Una vez que el Roomba empieza a cargar, marcamos la estación como ocupada
            for agent in self.cell.agents:
                if isinstance(agent, ChargingStation):
                    agent.isOccupied = True  # Marca la estación como ocupada
            self.current_path = []  # Limpiar camino actual
            return

        # Buscar el mejor camino a la estación más cercana conocida y libre
        path = self.get_closest_station_path()

        if path is None or len(path) < 2:  # No hay camino o ya estamos en la estación
            self.move_Random()
            return

        # Usamos el siguiente paso en el camino encontrado
        next_coord = path[1]
        next_cell = self.known_cells.get(next_coord)

        if next_cell is None:
            self.move_Random()
            return

        # Verificar si la estación de carga está ocupada
        for agent in next_cell.agents:
            if isinstance(agent, ChargingStation):
                if agent.isOccupied:  # Si la estación está ocupada busca otra estación, en caso de no conocer una, espera.
                    self.get_known_stations().remove(next_coord)
                    return

        # Si la estación no está ocupada, el Roomba se mueve allí
        self.cell = next_cell
        self.moves += 1
        self.consume_Battery()
        self.update_knowledge()


    def step(self):
        """
        Determines the new direction it will take, and then moves
        """
        if (self.battery == 0): # Si la batería llega a 0, el Roomba muere
            self.state = "DEAD"
            pass
        
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
                for agent in self.cell.agents: # Cuando cambia a EXPLORING, liberar la estación de carga
                    if isinstance(agent, ChargingStation):
                        agent.isOccupied = False  # Marca la estación como no ocupada para ser ocupada en el futuro
            else:
                self.recharge()

        elif self.state == "CRITICAL":
            self.move_to_Charge()

        elif self.state != "DEAD":
            # Compartir conocimiento con otros Roombas en vecindad
            self.share_knowledge()

        elif self.state == "DEAD":
            pass  # No hace nada si está muerto