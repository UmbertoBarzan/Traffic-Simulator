import pygame
import math
import random
import mysql.connector
from datetime import time, datetime

# Grafo globale per la definizione delle traiettorie
graph = {
    1: [1, 40, 9, 24, 32],
    2: [[2, 40, 10, 21, 29], [2, 40, 10, 19, 27]],
    3: [3, 40, 11, 18, 26],
    4: [[4, 40, 12, 23, 31], [4, 40, 12, 21, 29]],
    5: [5, 40, 13, 20, 28],
    6: [[6, 40, 14, 17, 25], [6, 40, 14, 23, 31]],
    7: [7, 40, 15, 22, 30],
    8: [[8, 40, 16, 19, 27], [8, 40, 16, 17, 25]]
}


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, plate, source, start_speed, points, start_time, car_image, road, simulation_day):
        super().__init__()

        # Inizalizzazione dei dati del veicolo
        self.plate = plate
        self.source = points[source]
        self.source_index = source
        self.x = self.source[0]
        self.y = self.source[1]
        self.speed = start_speed 
        self.car_image = car_image
        self.acceleration = 13.3
        self.deceleration = -1
        self.reference_traffic_light = points[source + 8]
        self.crashed = False

        # Gestione dati traiettorie
        self.set_direction(points, source)
        self.target = 1
        self.target_point = self.path[self.target]
        self.target_distance = 300
        self.moving_angle = self.set_linear_moving_angle((self.x, self.y), self.path[2])
        self.image_angle = self.set_image_angle((self.x, self.y), self.path[2])
        self.image = pygame.transform.rotate(car_image, math.degrees(self.image_angle))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.calculate_40(source)
        self.angolo1 = None
        self.angolo2 = None

        # Gestione delle velocità
        self.max_speed = 50
        self.target_speed = self.max_speed
        self.state = 'Accelerate'
        self.speed_graphic = []
        self.count_updates = 0

        # Gestione dati temporali
        self.start_time = start_time
        self.timer = start_time
        self.system_time = 0
        self.crash_timer = 0
        self.wait_timer = 0
        self.simulation_day = simulation_day

        # Gestione rettangoli e superfici per l'interfaccia grafica
        self.fov_surface = pygame.Surface((220, 68), pygame.SRCALPHA)
        self.fov_rect = self.fov_surface.get_rect()
        self.rotated_fov_surface = pygame.Surface((68, 220))
        self.rotated_fov_rect = self.rotated_fov_surface.get_rect(center=(self.x, self.y))
        self.fov_direction = 0
        self.distance = 300


    def update_fov(self):
        """Gestisce il cambio di rotazione del FOV"""

        if self.image_angle == 0 or self.image_angle == math.pi:
            self.fov_surface = pygame.transform.scale(self.fov_surface, (280, 280))
        else:
            self.fov_surface = pygame.transform.scale(self.fov_surface, (280, 280))
    
        self.fov_direction = self.image_angle
   

    def calculate_40(self, source):
        """Calcola il punto 40 (Stop al semaforo)"""

        if self.target == 1:
            if source == 1 or source == 2:
                self.path[self.target] = (self.path[self.target+1][0], self.path[self.target+1][1] + self.rect.height / 2 + 4)
            elif source == 3 or source == 4:
                self.path[self.target] = (self.path[self.target+1][0] + self.rect.width/2 + 4, self.path[self.target+1][1])
            elif source == 5 or source == 6:
                self.path[self.target] = (self.path[self.target+1][0], self.path[self.target+1][1] - self.rect.height / 2 - 4)
            else:
                self.path[self.target] = (self.path[self.target+1][0] - self.rect.width/2 - 4, self.path[self.target+1][1])
        self.target_point = self.path[self.target]


    def set_direction(self, points, source):
        """Imposta direzione e percorso in base alla sorgente. Traduce in coordinate i punti del percorso"""
       
        if source % 2 == 1:
            self.direction = 'SX'
            self.path = graph[source]
        else:
            dx_fw = random.randint(0, 1)
            if dx_fw == 0:
                self.direction = 'FW'
                self.path = graph[source][dx_fw]
            else:
                self.direction = 'DX'
                self.path = graph[source][dx_fw]
        self.path = [points[x] if x != 40 else x for x in self.path]


    def calculate_distance(self, target):
        """Calcolo della distanza euclidea"""

        dx = target[0] - self.x
        dy = target[1] - self.y
        distance = math.hypot(dx, dy)
        return dx, dy, distance


    def convert_ms_to_time(self, convert_time):
        """Conversione da millisecondi in dati temporali"""

        seconds = convert_time // 1000
        minutes = seconds // 60
        hours = minutes // 60
        seconds %= 60
        minutes %= 60
        return time(hours, minutes, seconds)


    def insert_query_vehicles(self, avg_speed):
        """Inserimento dei dati del veicolo nel DB"""

        conn = mysql.connector.connect(
            host="localhost",
            user="user", 
            password="userpassword",  
            database = "simulation_db"  
        )
        cursor = conn.cursor()

        # Standardizzazione dei dati temporali del veicolo
        day_sim = str(self.simulation_day)
        spawn_datetime = datetime.strptime(f"2025-05-{day_sim:02} {self.convert_ms_to_time(self.start_time)}", "%Y-%m-%d %H:%M:%S")
        exit_datetime = datetime.strptime(f"2025-05-{day_sim:02} {self.convert_ms_to_time(self.timer)}", "%Y-%m-%d %H:%M:%S")

        query = """
            INSERT INTO Vehicle (plate, source, spawn_time, exit_time, wait_time, avg_speed, type, system_time, spawn_datetime, exit_datetime) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (self.plate, self.source_index, self.convert_ms_to_time(self.start_time), self.convert_ms_to_time(self.timer), 
                  self.wait_timer // 1000, int(avg_speed), self.__class__.__name__, self.system_time, spawn_datetime, exit_datetime)

        cursor.execute(query, values)
        conn.commit()
        conn.close()


    def update_traffic_lights_sensor(self, traffic_light):
        """Aggiornamento dei dati del sensore di prossimità"""

        conn = mysql.connector.connect(
            host="localhost",
            user="user", 
            password="userpassword",  
            database = "simulation_db" 
        )
        cursor = conn.cursor()

        query = "UPDATE Traffic_Light SET n_vehicle = %s WHERE id = %s"
        values = (traffic_light.proximity_sensor, traffic_light.id)

        cursor.execute(query, values)
        conn.commit()
        conn.close()


    def case_kill(self, distance, scaled_dt, dt):
        """Gestione caso uscita dall'incrocio e inserimento nel DB dei dati del veicolo"""

        total_speed = 0

        if round(distance) <= 80 and self.target > 3:
            self.system_time = (self.timer - self.start_time) / 1000
            for speed in self.speed_graphic:
                total_speed += speed
            avg_speed = total_speed / len(self.speed_graphic)
            
            self.insert_query_vehicles(avg_speed)

            self.kill()


    def update_target_distance(self, dt, scaled_dt):
        """Aggiornamento della target distance"""

        if self.source_index == 1 or self.source_index == 2 or self.source_index == 5 or self.source_index == 6:
            self.target_distance = self.rect.height * 0.5 + (4 * (scaled_dt // dt))
        else:
            self.target_distance = self.rect.width * 0.7 + (4 * (scaled_dt // dt))


    def calculate_stopping_distance(self):
        """Calcolo della distanza d'arresto"""

        return self.stopping_distance(self.kmh_to_pxs()) if self.kmh_to_pxs() > 0 else 0


    def calculate_distance_collisions(self, target):
        """Calcola la distanza nei casi di collisione"""

        dx = target[0] - self.x
        dy = target[1] - self.y
        return math.hypot(dx, dy)


    def traffic_light_collision_red(self, distance, stop_distance):
        """Gestione comportamento con semaforo rosso"""

        if distance > stop_distance:
            if self.target_distance + 40 <= distance:
                self.state = 'Accelerate'
            else:
                if self.speed == 0 and self.target_distance <= distance:
                    self.state = 'Accelerate'
                else:
                    self.state = 'Brake'
        else:
            self.state = 'Brake'


    def traffic_light_collision_yellow(self, distance, stop_distance, yellow_remaining_time):
        """Gestione comportamento con semaforo giallo"""

        stop_time = (distance / self.kmh_to_pxs()) * 1000 if self.kmh_to_pxs() > 0 else 0

        if stop_time > yellow_remaining_time and self.target < 3:

            if distance > stop_distance:
                if self.target_distance + 40 <= distance:
                    self.state = 'Accelerate'
                else:
                    if self.speed == 0 and self.target_distance <= distance:
                        self.state = 'Accelerate'
                    else:
                        self.state = 'Brake'
        else:
            self.state = 'Accelerate'


    def traffic_light_collision(self, traffic_light, stop_distance, yellow_remaining_time, dt, scaled_dt):
        """Gestione visione del semaforo"""

        distance = self.calculate_distance_collisions((traffic_light.x, traffic_light.y))
        self.update_target_distance(dt, scaled_dt)

        if traffic_light.state == 'GREEN':
            self.state = 'Accelerate'
        elif traffic_light.state == 'RED':
            self.traffic_light_collision_red(distance, stop_distance)
           
        elif traffic_light.state == 'YELLOW':
            self.traffic_light_collision_yellow(distance, stop_distance, yellow_remaining_time)      


    def update_vehicle_collision_target(self, enemy_length, dt, scaled_dt):
        """Aggiorna il target di distanza in base all'orientamento del veicolo"""

        if 1 <= self.source_index <= 2 or 5 <= self.source_index <= 6:
            self.target_distance = self.rect.height / 2 + enemy_length / 2 + 12 + (2 * (scaled_dt / dt))
        else:
            self.target_distance = self.rect.width / 2 + enemy_length / 2 + 12 + (2 * (scaled_dt / dt))


    def update_vehicle_collision_speed(self, stop_distance, enemy_speed, distance):
        """Aggiorna lo stato in base alle collisioni e alla velocità delle altre macchine"""

        if self.target < 3:
            # Prima del semaforo
            if self.speed >= enemy_speed:
                # Velocita maggiore uguale a quello davanti
                if distance > stop_distance:
                    # Distanza maggiore uguale alla distanza d'arresto (velocità maggiore/ prima semaforo)
                    if self.target_distance + 40 <= distance:
                        # Target minore della distanza
                        self.state = 'Accelerate'
                    else:
                        # Target maggiore della distanza
                        if self.speed == 0 and self.target_distance <= distance:
                            self.state = 'Accelerate'
                        else:
                            self.state = 'Brake'
                else:
                    # Distanza minore alla distanza d'arresto (velocità maggiore( prima semaforo))
                    self.state = 'Brake'
            else:
                # Velocita minore a quello davanti
                self.state = 'Accelerate'
        else:
            # Dopo il semaforo
            self.state = 'Accelerate'


    def vehicle_collision(self, enemy_car_coords, enemy_length, enemy_speed, enemy_source_index, stop_distance, dt, scaled_dt):
        """Gestione collisioni tra FOV e veicoli"""

        distance = self.calculate_distance_collisions(enemy_car_coords)
        self.update_vehicle_collision_target(enemy_length, dt, scaled_dt)
        self.update_vehicle_collision_speed(stop_distance, enemy_speed, distance)
       

    def update_car_state(self, traffic_light, yellow_remaining_time, enemy_car_coords, enemy_speed, enemy_length, enemy_source_index, dt, scaled_dt):
        """Aggiornamento stato accelerazione e frenata"""

        # Calcolo della distanza di arresto
        stop_distance = self.calculate_stopping_distance()

        # Aggiornamento visione del veicolo
        if enemy_car_coords is None and enemy_speed is None and enemy_length is None and enemy_source_index != self.source_index:
            self.traffic_light_collision(traffic_light, stop_distance, yellow_remaining_time, dt, scaled_dt)
        else:
            self.vehicle_collision(enemy_car_coords, enemy_length, enemy_speed, enemy_source_index, stop_distance, dt, scaled_dt)


    def no_collision_case(self, dt):
        """Caso di non collisione con veicoli e semafori"""

        self.state = 'Accelerate'
        self.update_speed(dt, None)


    def crash_case(self, enemy_car, scaled_dt):
        """Gestione caso incidente"""

        self.crashed = True
        enemy_car.crashed = True

        self.update_speed(scaled_dt, None)
        self.update_speed(scaled_dt, enemy_car)

        # Gestione del timer dell'incidente
        self.crash_timer += scaled_dt

        if self.crash_timer >= 1_800_000:
            self.kill()
            enemy_car.kill()


    def update_speed(self, dt, enemy_car):
        """Aggiornamento della velocità in base a accelerazione o frenata"""

        if self.crashed == False:
            # Gestione di accelerazioni e frenate
            if self.state == 'Accelerate':
                speed_ax = self.speed + (self.acceleration * ((dt / 1000)))
                self.speed = min(speed_ax, self.max_speed)
            else:
                speed_ax = self.speed + (self.deceleration * ((dt / 1000)))
                self.speed = max(0, speed_ax)
        else:
            # Gestione macchina in un incidente
            if enemy_car:
                enemy_car.speed = 0
                enemy_car.state = 'Brake'
            else:
                self.speed = 0
                self.state = 'Brake'


    def update_rotated_fov_rect(self):
        """Aggiorna il rettangolo del FOV"""

        self.rotated_fov_surface = pygame.transform.rotozoom(self.fov_surface, math.degrees(self.image_angle - math.pi/2), 1.0)
        self.rotated_fov_rect = self.rotated_fov_surface.get_rect()


    def calculate_curve_trajectory(self, dt):
        """Calcolo effettivo di movimento lungo la curva"""

        # Inizializzazione degli angoli
        if self.angolo1 == None or self.angolo2 == None:
            self.angolo1, self.angolo2 = self.calcolo_angoli((self.x, self.y), self.target_point)

        # Calcolo dei raggi e interpolazione degli angoli
        raggio_medio = (self.raggio1 + self.raggio2) / 2
        angle = (self.kmh_to_pxs() * (dt /1000)) / raggio_medio
        self.update_angle(angle) 
        self.update_image_angle()

        # Interpolazione delle coordinate dei veicoli
        self.x = self.centro[0] + self.raggio1 * math.cos(self.angolo1)
        self.y = self.centro[1] - self.raggio2 * math.sin(self.angolo1)

        # Aggiornamento del rettangolo
        old_rect = self.rect 
        self.image = pygame.transform.rotate(self.car_image, math.degrees(self.image_angle))
        self.rect = self.image.get_rect()

        self.update_rotated_fov_rect()
       
        self.rect.center = old_rect.center


    def calculate_linear_trajectory(self, dx, dy, distance, dt):
        """Calcolo del movimento lungo una traiettoria lineare"""

        dx /= distance
        dy /= distance

        self.x += dx * self.kmh_to_pxs() * ((dt / 1000))
        self.y += dy * self.kmh_to_pxs() * ((dt / 1000))


    def update_target(self, distance, dt, traffic_light_obj):
        """Aggiorna il target alla traiettoria successiva in base al tempo e calcola centro e raggio per curve"""

        if (distance / max(1, self.kmh_to_pxs()) <= (dt / 800)):

            # Incremento del target
            if self.target == 4:
                pass
            else:
                self.target += 1

            self.target_point = self.path[self.target]

            # Calcolo di una traiettoria circolare e aggiornamento sensore di prossimità
            if self.target == 3:
                self.calcolo_centro_raggi((self.x, self.y), self.target_point)
                traffic_light_obj.proximity_sensor += 1
                self.update_traffic_lights_sensor(traffic_light_obj)

            # Aggiornamento degli angoli
            self.moving_angle = self.set_linear_moving_angle(self.path[self.target-1], self.path[self.target])
            if self.direction != 'FW':
                self.image_angle = self.set_image_angle(self.path[self.target-1], self.path[self.target])
            if self.target == 4:
                self.image = pygame.transform.rotate(self.car_image, math.degrees(self.image_angle))
            self.rect = self.image.get_rect(center=(self.x, self.y))


    def update_speed_data(self):
        """Aggiorna dati della velocità ogni n frame"""

        self.count_updates += 1
        if self.count_updates % 5 == 0:
            if self.speed != 0:
                self.speed_graphic.append(round(self.speed, 2))


    def update_timer(self, dt):
        """Aggiornamento del timer per calcolo tempo nel sistema"""
       
        self.timer += dt


    def update(self, scaled_dt, dt, traffic_light_obj):
        """Aggiorna il movimento della macchina"""

        dx, dy, distance = self.calculate_distance(self.target_point) # Calcolo distanza

        self.target_distance = distance # Aggiorna la distanza target per le traiettorie

        self.case_kill(distance, scaled_dt, dt) # Uscita dall'incrocio

        self.update_speed(scaled_dt, None) # Modifica effettiva della velocità in base a accelerazione o frenata
        self.update_speed_data() # Aggiorna lista delle velocità

        if self.target == 3 and self.direction != 'FW': # Controllo caso curva o caso lineare
            self.calculate_curve_trajectory(scaled_dt)      
        else:
            self.calculate_linear_trajectory(dx, dy, distance, scaled_dt)

        self.update_target(distance, scaled_dt, traffic_light_obj) # Aggiornamento del target

        self.rect.center = (self.x, self.y)

        self.update_fov() # Aggiornamento del FOV

        self.update_timer(scaled_dt) # Aggiornamento del timer

        if self.target < 3 and 0 <= round(self.speed) < 2:
            self.update_wait_timer(scaled_dt)


    def update_wait_timer(self, scaled_dt):
        """Aggiorna il tempo di attesa al semaforo"""

        self.wait_timer += scaled_dt


    def stopping_distance(self, speed_pxs):
        """Calcola della distanza di arresto --> d = v**2 / 2a"""

        return (speed_pxs ** 2) / (2 * - self.deceleration)


    def kmh_to_pxs(self):
        """Conversione da km/h a px/s"""

        speed_ms = self.speed / 3.6  # km/h -> m/s
        return speed_ms * 15.55  # m/s -> px/s


    def set_linear_moving_angle(self, p1, p2):
        """Imposta l'angolo per il movimento lungo la traiettoria"""

        x1, y1 = p1
        x2, y2 = p2
        if x1 < x2: return math.pi*3/2
        elif x1 > x2: return math.pi/2
        elif y1 > y2: return math.pi*2
        else: return math.pi


    def set_image_angle(self, p1, p2):
        """Imposta l'angolo per disegnare la macchina routata"""
       
        x1, y1 = p1
        x2, y2 = p2
        if self.direction == 'DX':
            if x1 < x2:
                if self.target == 3:
                    return math.pi * 2
                else:
                    return 0
            elif x1 > x2:
                if self.target == 3:
                    return math.pi * 3/2
                else:
                    return math.pi
            elif y1 > y2:
                if self.target == 3:
                    return math.pi
                else:
                    return math.pi/2
            else:
                if self.target == 3:
                    return math.pi * 2
                else:
                    return math.pi * 3/2
        else:
            if x1 < x2:
                if self.target == 3:
                    return math.pi/2
                else:
                    return 0
            elif x1 > x2:
                if self.target == 3:
                    return math.pi * 3/2
                else:
                    return math.pi
            elif y1 > y2:
                if self.target == 3:
                    return math.pi
                else:
                    return math.pi / 2
            else:
                if self.target == 3:
                    return 0
                else:
                    return math.pi * 3/2


    def definizione_casi(self, p1, p2):
        """Definizione del quadrante di circonferenza da utilizzare. Ritorna un numero da 1 a 4"""

        x1, y1 = p1
        x2, y2 = p2
        if self.direction == 'SX':
            if x1 > x2 and y1 > y2:
                return 1
            elif x1 > x2 and y1 < y2:
                return 2
            elif x1 < x2 and y1 < y2:
                return 3
            else:
                return 4
        if self.direction == 'DX':
            if x1 > x2 and y1 > y2:
                return 2
            elif x1 > x2 and y1 < y2:
                return 3
            elif x1 < x2 and y1 < y2:
                return 4
            else:
                return 1


    def calcolo_centro(self, p1, p2):
        """Calcola il centro su cui applicare la traiettoria circolare"""

        caso = self.definizione_casi(p1, p2)
        x1, y1 = p1
        x2, y2 = p2
        if caso == 1:
            self.centro = x2, y1
        elif caso == 2:
            self.centro = x1, y2
        elif caso == 3:
            self.centro = x2, y1
        else:
            self.centro = x1, y2


    def calcolo_raggi(self, p1, p2):
        """Calcola i raggi"""

        x1, y1 = p1
        x2, y2 = p2
        self.raggio1 = abs(x1 - x2)
        self.raggio2 = abs(y1 - y2)


    def calcolo_angoli(self, p1, p2):
        """Ritorna angolo di inizio e fine del quadrante di circonferenza da utilizzare"""

        caso = self.definizione_casi(p1, p2)
        if self.direction == 'SX':
            if caso == 1:
                return 0, math.pi/2
            elif caso == 2:
                return math.pi/2, math.pi
            elif caso == 3:
                return math.pi, math.pi * 3/2
            else:
                return math.pi * 3/2, 2 * math.pi
        else:
            if caso == 1:
                return math.pi, math.pi/2
            elif caso == 2:
                return math.pi*3/2, math.pi
            elif caso == 3:
                return 2*math.pi, math.pi*3/2
            else:
                return math.pi/2, 0


    def calcolo_centro_raggi(self, p1, p2):
        """Calcolo del centro e dei raggi per una traiettoria circolare tra 2 punti"""

        self.calcolo_centro(p1, p2)
        self.calcolo_raggi(p1, p2)


    def update_angle(self, angle):
        """Aggiornamento dell'angolo iniziale aggiungendo o togliendo una parte di angolo
        che corrisponde alla variazione ogni frame"""

        if self.direction == 'SX':
            self.angolo1 += angle
        else:
            self.angolo1 -= angle


    def update_image_angle(self):
        """Aggiornamento dell'angolo dell'immagine"""

        if self.direction == 'SX':
            self.image_angle = self.angolo1 + math.pi/2
        else:
            self.image_angle = self.angolo1 - math.pi/2


# Definizione delle classi ereditarie per differenziare indici di accelerazione e decelerazione

class Car(Vehicle):
    def __init__(self, plate, source, start_speed, points, start_time, car_image, road, simulation_day):
        super().__init__(plate, source, start_speed, points, start_time, car_image, road, simulation_day)

        self.acceleration = 14
        self.deceleration = -30


class Bus(Vehicle):
    def __init__(self, plate, source, start_speed, points, start_time, car_image, road, simulation_day):
        super().__init__(plate, source, start_speed, points, start_time, car_image, road, simulation_day)

        self.acceleration = 10
        self.deceleration = -26


class Truck(Vehicle):
    def __init__(self, plate, source, start_speed, points, start_time, car_image, road, simulation_day):
        super().__init__(plate, source, start_speed, points, start_time, car_image, road, simulation_day)

        self.acceleration = 10
        self.deceleration = -24


class Moto(Vehicle):
    def __init__(self, plate, source, start_speed, points, start_time, car_image, road, simulation_day):
        super().__init__(plate, source, start_speed, points, start_time, car_image, road, simulation_day)

        self.acceleration = 12
        self.deceleration = -28