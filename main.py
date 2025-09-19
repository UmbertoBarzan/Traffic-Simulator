import pygame
import numpy as np
import string
import math
import random
from functions.algoritmo_punti import calcola_punti as points_algorithm
from classes.vehicles import Car, Bus, Truck, Moto
from classes.traffic_light import Traffic_Light
import mysql.connector
from functions.db_functions import init_database
import webbrowser


class Intersection:
    def __init__(self, width, height, road):

        # Inizializzazione incrocio
        self.traffic_lights = {}
        self.pedestrian_traffic_lights = {}
        self.time_lapse = 1
        self.width = width
        self.height = height
        self.road = road
        self.generate_points()
        self.generate_traffic_lights()
        self.generate_pedestrian_traffic_lights()

        # Gestione traiettorie
        self.graph = {
            1: [1, 9, 24, 32],
            2: [[2, 10, 21, 29], [2, 10, 19, 27]],
            3: [3, 11, 18, 26],
            4: [[4, 12, 23, 31], [4, 12, 21, 29]],
            5: [5, 13, 20, 28],
            6: [[6, 14, 17, 25], [6, 14, 23, 31]],
            7: [7, 15, 22, 30],
            8: [[8, 16, 19, 27], [8, 16, 17, 25]]
        }

        # Gestione corsie
        self.lanes_dict = {
            1: [True, "Verticale", "SX"],
            2: [True, "Verticale", "DX"],
            3: [False, "Orizzontale", "SX"],
            4: [True, "Orizzontale", "DX"],
            5: [True, "Verticale", "SX"],
            6: [True, "Verticale", "DX"],
            7: [True, "Orizzontale", "SX"],
            8: [True, "Orizzontale", "DX"]
        }

        # Gestione veicoli
        self.car_group = pygame.sprite.Group()
        self.clock = pygame.time.Clock()
        self.car_id_counter = 0
        self.last_spawn_time = 0
        self.spawn_interval = 2000

        # Gestione tempo
        self.current_time_ms = 0 
        self.hour = 0
        self.minutes = 0
        self.seconds = 0
        self.day = 1

        # Gestione semafori
        self.couples = [(2, 6), (4, 8), (1, 5), (3, 7)]
        self.ped_couples = [((37, 38), (45, 46)), ((33, 34), (42, 41)), ((37, 38), (39, 40), (45, 46), (47, 48)), ((33, 34), (35, 36), (41, 42), (43, 44))]
        self.start_time = 0
        self.traffic_lights_timer = 0
        self.traffic_light_timer_text = self.traffic_lights_timer / 1000
        self.couples_index = 0
        self.green_time = 30000
        self.yellow_time = self.green_time + 5000
        self.deadzone = self.yellow_time + 2000
        self.green_timer = 0
        self.yellow_timer = 0

        # Color Palette
        self.day_of_time = 'Night'
        self.colors = None
        self.color_palette = {
            'Night': None,
            'Morning': None,
            'Afternoon': None,
            'Evening': None,
        }

        self.grass_colors = [(7, 48, 41), (60, 140, 70), (50, 140, 15), (215, 130, 110)]
        self.sidewalk_colors = [(80, 80, 80), (220, 220, 235), (255, 255, 230), (220, 200, 150)]
        self.road_colors = [(17, 17, 17), (50, 51, 60), (55, 55, 50), (50, 40, 40)]
        self.lane_divider_colors = [(156, 145, 52), (219, 195, 88), (255, 230, 0), (215, 180, 134)]
        self.lane_lines_colors = [(152, 152, 152), (220, 220, 233), (255, 255, 240), (230, 220, 150)]

        # Gestione incidenti
        self.min_distance_dict = {}
        self.crashed_plates = []
        self.crash_counter = 0


    def start_cycle(self):
        """Inizia il ciclo mettendo la prima coppia verde"""

        current_couple = self.couples[self.couples_index]
        index_1, index_2 = current_couple
        current_ped_couple = self.ped_couples[self.couples_index]

        self.traffic_lights[index_1].state = 'GREEN'
        self.traffic_lights[index_2].state = 'GREEN'

        for ped_tl in current_ped_couple:
            self.pedestrian_traffic_lights[ped_tl[0]].state = 'GREEN'
            self.pedestrian_traffic_lights[ped_tl[1]].state = 'GREEN'


    def update_green_yellow(self, index_1, index_2):
        """Aggiorna da verde a giallo"""

        self.green_timer = 0
        self.change_state('YELLOW', index_1)
        self.change_state('YELLOW', index_2)


    def update_yellow_red(self, index_1, index_2):
        """Aggiorna da giallo a rosso"""

        self.yellow_timer = 0
        self.change_state('RED', index_1)
        self.change_state('RED', index_2)


    def update_deadzone(self):
        """Passa alla prossima coppia"""

        self.couples_index += 1
        self.couples_index %= len(self.couples)

        if self.couples_index == 2:
            self.green_time = 20000
        if self.couples_index == 0:
            self.green_time = 30000

        self.yellow_time = self.green_time + 5000
        self.deadzone = self.yellow_time + 2000
        self.traffic_lights_timer = 0
        self.start_cycle()


    def update_traffic_lights_state(self):
        """Aggiornamento dello stato dei semafori"""

        current_couple = self.couples[self.couples_index]
        index_1, index_2 = current_couple
        current_ped_couple = self.ped_couples[self.couples_index]

        if self.traffic_lights_timer >= self.green_time:
            self.update_green_yellow(index_1, index_2)

            for ped_tl in current_ped_couple:
                self.update_green_yellow(ped_tl[0], ped_tl[1])

        if self.traffic_lights_timer >= self.yellow_time:
            self.update_yellow_red(index_1, index_2)

            for ped_tl in current_ped_couple:
                self.update_yellow_red(ped_tl[0], ped_tl[1])

        if self.traffic_lights_timer >= self.deadzone:
            self.update_deadzone()


    def change_state(self, state, index):
        """Cambia lo stato del semaforo evitando incongruenze"""

        if index < 30:
            if state == 'GREEN':
                self.traffic_lights[index].state = 'GREEN'
            elif state == 'YELLOW' and self.traffic_lights[index].state == 'GREEN':
                self.traffic_lights[index].state = 'YELLOW'
            elif state == 'RED' and self.traffic_lights[index].state == 'YELLOW':
                self.traffic_lights[index].state = 'RED'
        else:
            if state == 'GREEN':
                self.pedestrian_traffic_lights[index].state = 'GREEN'
            elif state == 'YELLOW' and self.pedestrian_traffic_lights[index].state == 'GREEN':
                self.pedestrian_traffic_lights[index].state = 'YELLOW'
            elif state == 'RED' and self.pedestrian_traffic_lights[index].state == 'YELLOW':
                self.pedestrian_traffic_lights[index].state = 'RED'


    def update_timer(self, dt):
        """Aggiornamento del timer per la temporizzazione dei semafori"""

        self.traffic_lights_timer += dt


    def update_traffic_lights_color(self):
        """Aggiorna il colore per ogni semaforo"""

        for key in self.traffic_lights:
            self.traffic_lights[key].update_color()
        for key in self.pedestrian_traffic_lights:
            self.pedestrian_traffic_lights[key].update_color()


    def init_tl_table(self):
        """Inizializza la tabella dei semafori"""

        conn = mysql.connector.connect(
            host="localhost",
            user="user",  # user
            password="userpassword",  # password
            database = "simulation_db"  # nome db
        )
        cursor = conn.cursor()

        query = """
            INSERT INTO Traffic_Light (id, n_vehicle, type) VALUES (%s, %s, %s)
        """

        for traffic_light in range(1,9):
            values = (traffic_light, 0, "Vehicles_TL")
            print(values)
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()


    def generate_traffic_lights(self):
        """Generazione degli 8 semafori alle coordinate giuste"""

        for id in range(1, 9):
            self.traffic_lights[id] = Traffic_Light(self.points[id+8][0], self.points[id+8][1])
            self.traffic_lights[id].id = id

        #self.init_tl_table()


    def generate_pedestrian_traffic_lights(self):
        """Generazione dei 16 semafori pedonali alle coordinate giuste"""

        self.pedestrian_traffic_lights[33] = Traffic_Light(500, 650)
        self.pedestrian_traffic_lights[34] = Traffic_Light(640, 650)
        self.pedestrian_traffic_lights[35] = Traffic_Light(700, 590)
        self.pedestrian_traffic_lights[36] = Traffic_Light(700, 450)
        self.pedestrian_traffic_lights[37] = Traffic_Light(700, 444)
        self.pedestrian_traffic_lights[38] = Traffic_Light(700, 304)
        self.pedestrian_traffic_lights[39] = Traffic_Light(640, 220)
        self.pedestrian_traffic_lights[40] = Traffic_Light(500, 220)
        self.pedestrian_traffic_lights[41] = Traffic_Light(494, 220)
        self.pedestrian_traffic_lights[42] = Traffic_Light(354, 220)
        self.pedestrian_traffic_lights[43] = Traffic_Light(270, 304)
        self.pedestrian_traffic_lights[44] = Traffic_Light(270, 444)
        self.pedestrian_traffic_lights[45] = Traffic_Light(270, 450)
        self.pedestrian_traffic_lights[46] = Traffic_Light(270, 590)
        self.pedestrian_traffic_lights[47] = Traffic_Light(354, 650)
        self.pedestrian_traffic_lights[48] = Traffic_Light(494, 650)


    def update_spawn_interval(self):
        """Aggiorna l'intervallo di spawn e il periodo della giornata"""

        if 0 <= self.hour < 7:
            self.spawn_interval = 50000

        elif 7 <= self.hour < 10:
            self.spawn_interval = 3000
        
        elif 10 <= self.hour < 13:
            self.spawn_interval = 5000
        
        elif 13 <= self.hour < 17:
            self.spawn_interval = 8000
       
        elif 17 <= self.hour < 21:
            self.spawn_interval = 4000
       
        else:
            self.spawn_interval = 30000


    def update_day_of_time(self):
        """Aggiorna il momento della giornata e la palette dei colori"""

        if 0 < self.hour < 6 or 21 <= self.hour < 24:
            self.day_of_time = 'Night'
       
        elif 6 <= self.hour < 12:
            self.day_of_time = 'Morning'
       
        elif 12 <= self.hour < 17:
            self.day_of_time = 'Afternoon'
       
        elif 17 <= self.hour < 21:
            self.day_of_time = 'Evening'
       
        self.update_color_palette()


    def update_current_time(self, dt):
        """Aggiorna i millisecondi di clock dell'incrocio, scalando in base al time lapse"""

        self.current_time_ms += dt
        if self.hour == 24:
            self.day += 1
        self.hour = int((self.current_time_ms // 3600000) % 24)
        self.minutes = int((self.current_time_ms // 60000) % 60)
        self.seconds = int((self.current_time_ms // 1000) % 60)
        self.time_string = f"Time - {self.hour:02}:{self.minutes:02}:{self.seconds:02}"


    def generate_lane(self):
        """Generazione random di un ingresso di un veicolo"""

        # Filtra corsie in base a True / False
        lista_true = [k for k, v in self.lanes_dict.items() if v[0]]

        # Divide in SX e DX
        sx_list = [k for k in lista_true if self.lanes_dict[k][2] == 'SX']
        dx_list = [k for k in lista_true if self.lanes_dict[k][2] == 'DX']
        lista_sx_dx = [sx_list, dx_list]
        prob = [0.4, 0.6]

        # Genera indice casuale con probabilità personalizzate e recupera la lista corrispondente
        index = np.random.choice([0, 1], p=prob)
        lista_sx_dx_random = lista_sx_dx[index]

        # Divide in Orizzontale e Verticale
        hor_list = [x for x in lista_sx_dx_random if self.lanes_dict[x][1] == 'Orizzontale']
        vert_list = [x for x in lista_sx_dx_random if self.lanes_dict[x][1] == 'Verticale']
        prob = [0.4, 0.6]

        hor_vert_list = [hor_list, vert_list]
        index = np.random.choice([0, 1], p=prob)
        hor_vert_list_random = hor_vert_list[index]

        # Controllo in base alle corsie disponibili
        if len(hor_vert_list_random) == 0:
            random_lane = None
        elif len(hor_vert_list_random) == 1:
            random_lane = hor_vert_list_random[0]
        elif len(hor_vert_list_random) == 2:
            random_lane = random.choice(hor_vert_list_random)
        
        return random_lane


    def generate_points(self):
        """Generazione dei punti seguendo l'algoritmo"""

        self.points = points_algorithm(self.width, self.height, self.road)


    def generate_plate(self):
        """Generazione di una targa random per il veicolo"""

        plate = random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])

        for i in range(6):
            if i < 1 or i > 3:
                plate += random.choice(string.ascii_uppercase)
            else:
                plate += str(random.randint(0,9))

        return plate


    def draw_sidewalk(self, center_x, center_y, lane_width, road_width, height, width):
        """Disegna i marciapiedi"""
       
        pygame.draw.rect(screen, self.colors['Sidewalk'], (center_x - lane_width - 20, 0, road_width + 40, height))
        pygame.draw.rect(screen, self.colors['Sidewalk'], (0, center_y - lane_width - 20, width, road_width + 40))


    def draw_road(self, center_x, center_y, lane_width, road_width, width, height):
        """Disegna la strada e lo spartitraffico"""
       
        # Strada
        pygame.draw.rect(screen, self.colors['Road'], (center_x - lane_width, 0, road_width, height))
        pygame.draw.rect(screen, self.colors['Road'], (0, center_y - lane_width, width, road_width))

        # Spartitraffico verticale
        pygame.draw.line(screen, self.colors['Lane_Divider'], (center_x, 0), (center_x, center_y - lane_width), 10)
        pygame.draw.line(screen, self.colors['Lane_Divider'], (center_x, center_y + lane_width), (center_x, height), 10)

        # Spartitraffico orizzontale
        pygame.draw.line(screen, self.colors['Lane_Divider'], (0, center_y), (center_x - lane_width, center_y), 10)
        pygame.draw.line(screen, self.colors['Lane_Divider'], (center_x + lane_width, center_y), (width, center_y), 10)


    def draw_lane_lines(self, center_x, center_y, lane_width, half_lane, width, height):
        """Disegna linee tratteggiate delle corsie"""

        for y in range(0, center_y - lane_width-40, 40):  # parte superiore
            pygame.draw.line(screen, self.colors['Lane_Lines'], (center_x - half_lane, y), (center_x - half_lane, y + 20), 3)
            pygame.draw.line(screen, self.colors['Lane_Lines'], (center_x + half_lane, y), (center_x + half_lane, y + 20), 3)
        for y in range(center_y + lane_width+40, height, 40):  # parte inferiore
            pygame.draw.line(screen, self.colors['Lane_Lines'], (center_x - half_lane, y), (center_x - half_lane, y + 20), 3)
            pygame.draw.line(screen, self.colors['Lane_Lines'], (center_x + half_lane, y), (center_x + half_lane, y + 20), 3)

        for x in range(0, center_x - lane_width-40, 40):  # parte sinistra
            pygame.draw.line(screen, self.colors['Lane_Lines'], (x, center_y - half_lane), (x + 20, center_y - half_lane), 3)
            pygame.draw.line(screen, self.colors['Lane_Lines'], (x, center_y + half_lane), (x + 20, center_y + half_lane), 3)
        for x in range(center_x + lane_width+40, width, 40):  # parte destra
            pygame.draw.line(screen, self.colors['Lane_Lines'], (x, center_y - half_lane), (x + 20, center_y - half_lane), 3)
            pygame.draw.line(screen, self.colors['Lane_Lines'], (x, center_y + half_lane), (x + 20, center_y + half_lane), 3)


    def draw_traffic_lights(self, center_x, center_y, lane_width, half_lane):
        """Disegna i semafori nonchè le linee di stop"""

        pygame.draw.line(screen, intersection.traffic_lights[1].color, (center_x + half_lane, center_y + lane_width),
                        (center_x, center_y + lane_width), 5)  # Semaforo 1 - Punto 9
        pygame.draw.line(screen, intersection.traffic_lights[2].color, (center_x + lane_width, center_y + lane_width),
                        (center_x + half_lane, center_y + lane_width), 5) # Semaforo 2 - Punto 10
        pygame.draw.line(screen, intersection.traffic_lights[3].color, (center_x + lane_width, center_y - half_lane),
                        (center_x + lane_width, center_y), 5) # Semaforo 3 - Punto 11
        pygame.draw.line(screen, intersection.traffic_lights[4].color, (center_x + lane_width, center_y - lane_width),
                        (center_x + lane_width, center_y - half_lane), 5)  # Semaforo 4 - Punto 12
        pygame.draw.line(screen, intersection.traffic_lights[5].color, (center_x, center_y - lane_width),
                        (center_x - half_lane, center_y - lane_width), 5) # Semaforo 5 - Punto 13
        pygame.draw.line(screen, intersection.traffic_lights[6].color, (center_x - half_lane, center_y - lane_width),
                        (center_x - lane_width, center_y - lane_width), 5) # Semaforo 6 - Punto 14
        pygame.draw.line(screen, intersection.traffic_lights[7].color, (center_x - lane_width, center_y),
                        (center_x - lane_width, center_y + half_lane), 5)  # Semaforo 7 - Punto 15
        pygame.draw.line(screen, intersection.traffic_lights[8].color, (center_x - lane_width, center_y + half_lane),
                        (center_x - lane_width, center_y + lane_width), 5) # Semaforo 8 - Punto 16


    def draw_pedestrian_traffic_lights(self, center_x, center_y, lane_width, half_lane):

        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[33].color, (504, 650), (504, 680), 6) # Seamforo pedoni 33
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[34].color, (644, 650), (644, 680), 6) # Seamforo pedoni 34
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[35].color, (700, 594), (730, 594), 6) # Seamforo pedoni 35
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[36].color, (700, 454), (730, 454), 6) # Seamforo pedoni 36
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[37].color, (700, 447), (730, 447), 6) # Seamforo pedoni 37
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[38].color, (700, 304), (730, 304), 6) # Seamforo pedoni 38
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[39].color, (644, 220), (644, 250), 6) # Seamforo pedoni 39
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[40].color, (504, 220), (504, 250), 6) # Seamforo pedoni 40
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[41].color, (497, 220), (497, 250), 6) # Seamforo pedoni 41
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[42].color, (354, 220), (354, 250), 6) # Seamforo pedoni 42
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[43].color, (270, 304), (300, 304), 6) # Seamforo pedoni 43
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[44].color, (270, 447), (300, 447), 6) # Seamforo pedoni 44
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[45].color, (270, 454), (300, 454), 6) # Seamforo pedoni 45
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[46].color, (270, 594), (300, 594), 6) # Seamforo pedoni 46
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[47].color, (354, 650), (354, 680), 6) # Seamforo pedoni 47
        pygame.draw.line(screen, intersection.pedestrian_traffic_lights[48].color, (497, 650), (497, 680), 6) # Seamforo pedoni 48


    def draw_stop_text(self, center_x, center_y, lane_width):
        """Disegna i testi STOP"""

        font = pygame.font.Font(None, 40)
        stop_text = font.render("STOP", True, self.colors['Lane_Lines'])

        stop_text_sx = pygame.transform.rotate(stop_text.copy(), -90)  # Sinistra
        stop_text_dx = pygame.transform.rotate(stop_text.copy(),90)  # Destra
        stop_text_top = pygame.transform.rotate(stop_text.copy(), 180) # Alto
        stop_text_bottom = pygame.transform.rotate(stop_text.copy(),0)  # Basso

        screen.blit(stop_text_sx, (center_x - lane_width - 40, center_y + 30))
        screen.blit(stop_text_dx, (center_x + lane_width + 10, center_y - 110))
        screen.blit(stop_text_top, (center_x - 100, center_y - lane_width - 40))
        screen.blit(stop_text_bottom, (center_x + 40, center_y + lane_width + 10))


    def draw_interface(self, width, height, road_width, tl, dt):
        """Disegna l'interfaccia grafica"""
       
        center_x = width // 2
        center_y = height // 2
        lane_width = road_width // 2
        half_lane = lane_width // 2

        screen.fill(self.colors['Grass'])

        self.draw_sidewalk(center_x, center_y, lane_width, road_width, height, width)
        self.draw_road(center_x, center_y, lane_width, road_width, width, height)
        self.draw_lane_lines(center_x, center_y, lane_width, half_lane, width, height)
        self.draw_traffic_lights(center_x, center_y, lane_width, half_lane)
        self.draw_pedestrian_traffic_lights(center_x, center_y, lane_width, half_lane)
        self.draw_stop_text(center_x, center_y, lane_width)
        self.draw_progress_timer(half_lane, dt, width, height, road_width)
        self.draw_timelapse_buttons()


    def round_image(self, image, radius):
        """Applica angoli arrotondati a un'immagine"""

        size = image.get_size()
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, *size), border_radius=radius)

        rounded = pygame.Surface(size, pygame.SRCALPHA)
        rounded.blit(image, (0, 0))
        rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return rounded


    def draw_timelapse_buttons(self):
        """Disegna i bottoni di pausa, timelapse e grafico con bordi arrotondati"""

        self.pause_rect = pygame.Rect(100, 100, 80, 80)
        self.ff_rect = pygame.Rect(200, 100, 80, 80)
        self.graphics_rect = pygame.Rect(20, 110, 60, 60)

        pause_img = pygame.image.load('./img/pause.png')
        ff_img = pygame.image.load('img/fast_forward.png')
        graphics_img = pygame.image.load('img/Graphics.jpg')

        pause_img = pygame.transform.scale(pause_img, (80, 80))
        ff_img = pygame.transform.scale(ff_img, (80, 80))
        graphics_img = pygame.transform.scale(graphics_img, (60, 60))

        graphics_img = self.round_image(graphics_img, radius=10)

        pause_rect = pause_img.get_rect(topleft=(self.pause_rect.x, self.pause_rect.y))
        ff_rect = ff_img.get_rect(topleft=(self.ff_rect.x, self.ff_rect.y))
        graphics_rect = graphics_img.get_rect(topleft=(self.graphics_rect.x, self.graphics_rect.y))

        screen.blit(pause_img, pause_rect)
        screen.blit(ff_img, ff_rect)
        screen.blit(graphics_img, graphics_rect)


    def draw_green_vertical_progress_bar(self, index_1, index_2, distance_height, half_lane, quarter_lane, dt):
        """Disegna la progress bar verde verticale"""
       
        GREEN = (0, 255, 0, 110)

        self.green_timer += dt
        green_fraction = 1 - (self.green_timer / self.green_time)

        scaled_height = distance_height * green_fraction
        if scaled_height < 0: scaled_height = 0

        low_surface = pygame.Surface((half_lane, scaled_height), pygame.SRCALPHA)
        high_surface = pygame.Surface((half_lane, scaled_height), pygame.SRCALPHA)

        pygame.draw.rect(low_surface, GREEN, (0, 0, half_lane, scaled_height))
        pygame.draw.rect(high_surface, GREEN, (0, 0, half_lane, scaled_height))

        screen.blit(low_surface, (self.points[index_1+8][0] - quarter_lane, self.points[index_1+8][1]))
        screen.blit(high_surface, (self.points[index_2+8][0] - quarter_lane, distance_height - scaled_height))


    def draw_yellow_vertical_progress_bar(self, index_1, index_2, distance_height, half_lane, quarter_lane, dt):
        """Disegna la progress bar gialla verticale"""
       
        YELLOW = (255, 255, 0, 110)
       
        self.yellow_timer += dt
        yellow_fraction = 1 - (self.yellow_timer / (self.yellow_time - self.green_time))

        scaled_height_yellow = distance_height * yellow_fraction
        if scaled_height_yellow < 0: scaled_height_yellow = 0

        low_surface = pygame.Surface((half_lane, scaled_height_yellow), pygame.SRCALPHA)
        high_surface = pygame.Surface((half_lane, scaled_height_yellow), pygame.SRCALPHA)

        pygame.draw.rect(low_surface, YELLOW, (0, 0, half_lane, scaled_height_yellow))
        pygame.draw.rect(high_surface, YELLOW, (0, 0, half_lane, scaled_height_yellow))

        screen.blit(low_surface, (self.points[index_1+8][0] - quarter_lane, self.points[index_1+8][1]))
        screen.blit(high_surface, (self.points[index_2+8][0] - quarter_lane, distance_height - scaled_height_yellow))


    def draw_green_horizontal_progress_bar(self, index_1, index_2, distance_width, half_lane, quarter_lane, dt):
        """Disegna la progress bar verde orizzontale"""

        GREEN = (0, 255, 0, 110)

        self.green_timer += dt
        green_fraction = 1 - (self.green_timer / self.green_time)

        scaled_width = distance_width * green_fraction
        if scaled_width < 0: scaled_width = 0

        left_surface = pygame.Surface((scaled_width, half_lane), pygame.SRCALPHA)
        right_surface = pygame.Surface((scaled_width, half_lane), pygame.SRCALPHA)

        pygame.draw.rect(left_surface, GREEN, (0, 0, scaled_width, half_lane))
        pygame.draw.rect(right_surface, GREEN, (0, 0, scaled_width, half_lane))

        screen.blit(left_surface, (self.points[index_1+8][0], self.points[index_1+8][1] - quarter_lane))
        screen.blit(right_surface, (distance_width - scaled_width, self.points[index_2+8][1] - quarter_lane))


    def draw_yellow_horizontal_progress_bar(self, index_1, index_2, distance_width, half_lane, quarter_lane, dt):
        """Disegna la progress bar gialla orizzontale"""

        YELLOW = (255, 255, 0, 110)

        self.yellow_timer += dt
        yellow_fraction = 1 - (self.yellow_timer / (self.yellow_time - self.green_time))

        scaled_width_yellow = distance_width * yellow_fraction
        if scaled_width_yellow < 0: scaled_width_yellow = 0

        left_surface = pygame.Surface((scaled_width_yellow, half_lane), pygame.SRCALPHA)
        right_surface = pygame.Surface((scaled_width_yellow, half_lane), pygame.SRCALPHA)

        pygame.draw.rect(left_surface, YELLOW, (0, 0, scaled_width_yellow, half_lane))
        pygame.draw.rect(right_surface, YELLOW, (0, 0, scaled_width_yellow, half_lane))

        screen.blit(left_surface, (self.points[index_1+8][0], self.points[index_1+8][1] - quarter_lane))
        screen.blit(right_surface, (distance_width - scaled_width_yellow, self.points[index_2+8][1] - quarter_lane))


    def draw_progress_timer(self, half_lane, dt, width, height, road):
        """Disegno della progress bar in corsia"""

        quarter_lane = half_lane // 2
        distance_height_traffic_light = height // 2 - road // 2 # Distanza in altezza da origine a semaforo
        distance_width_traffic_light = width // 2 - road // 2 # Distanza in larghezza da origine a semaforo

        couple_reference = self.couples[self.couples_index]
        case = 0 if self.couples_index % 2 == 0 else 1
        index_1, index_2 = couple_reference

        state_1 = self.traffic_lights[couple_reference[0]].state

        if case == 0:
            # Caso verticale
            if state_1 == 'GREEN':
                self.draw_green_vertical_progress_bar(index_1, index_2, distance_height_traffic_light, half_lane, quarter_lane, dt)
            elif state_1 == 'YELLOW':
                self.draw_yellow_vertical_progress_bar(index_1, index_2, distance_height_traffic_light, half_lane, quarter_lane, dt)
        else:
            # Caso orizzontale
            if state_1 == 'GREEN':
                self.draw_green_horizontal_progress_bar(index_1, index_2, distance_width_traffic_light, half_lane, quarter_lane, dt)
            elif state_1 == 'YELLOW':
                self.draw_yellow_horizontal_progress_bar(index_1, index_2, distance_width_traffic_light, half_lane, quarter_lane, dt)


    def get_scaled_speed(self, random_lane):
        """Ritorna la velocità scalata in base al traffico nella corsia"""

        min_distance = self.min_distance_dict[random_lane]
        if min_distance > 400:
            min_distance = 400
        return (min_distance - 100) * 0.1


    def instance_vehicle(self, type, plate, random_lane, car_image):
        """Usa un costruttore diverso in base al tipo random"""

        scaled_speed = self.get_scaled_speed(random_lane)

        if type == 'Car':
            return Car(plate, random_lane, scaled_speed, self.points, self.current_time_ms, car_image, intersection.road, self.day)
        elif type == 'Bus':
            return Bus(plate, random_lane, scaled_speed, self.points, self.current_time_ms, car_image, intersection.road, self.day)
        elif type == 'Truck':
            return Truck(plate, random_lane, scaled_speed, self.points, self.current_time_ms, car_image, intersection.road, self.day)
        else:
            return Moto(plate, random_lane, scaled_speed, self.points, self.current_time_ms, car_image, intersection.road, self.day)


    def generate_random_vehicle_values(self):
        """Genera corsia di partenza, tipo, immagine e targa del veicolo"""

        random_lane = self.generate_lane()
        vehicle_prob = [0.7, 0.1, 0.05, 0.15]
        random_type = np.random.choice(list(vehicle_type_dict.keys()), p=vehicle_prob)
        car_image = pygame.image.load(np.random.choice(vehicle_type_dict[random_type]))
        plate = self.generate_plate()

        return random_lane, random_type, car_image, plate


    def spawn_vehicle(self):
        """Gestisce lo spawn dei veicoli in base all'intervallo"""

        if (self.current_time_ms - self.last_spawn_time) > self.spawn_interval:

            random_lane, random_type, car_image, plate = self.generate_random_vehicle_values()
           
            if random_lane != None:
                new_vehicle = self.instance_vehicle(random_type, plate, random_lane, car_image)
                self.car_group.add(new_vehicle)
           
            self.last_spawn_time = self.current_time_ms


    def draw_fov_linear(self, car):
        """Disegna il FOV in traiettorie lineari"""

        if 0 <= car.fov_direction < math.pi/2:
            car.fov_rect = car.fov_surface.get_rect(midleft=(car.x, car.y))
        elif math.pi/2 <= car.fov_direction < math.pi:
            car.fov_rect = car.fov_surface.get_rect(midbottom=(car.x, car.y))
        elif math.pi <= car.fov_direction < math.pi * 3 / 2:
            car.fov_rect = car.fov_surface.get_rect(midright=(car.x, car.y))
        else:
            car.fov_rect = car.fov_surface.get_rect(midtop=(car.x, car.y))


    def draw_fov(self, car):
        """Disegna il FOV di ogni veicolo"""

        if car.target != 3 or car.direction == 'FW':
            self.draw_fov_linear(car)

        elif car.direction != 'FW':
            offset_x = car.rect.height / 2
            offset_y = car.rect.width / 2

            angle = car.fov_direction % (2 * math.pi)

            if 0 <= angle < math.pi / 2:
                car.fov_rect = car.rotated_fov_surface.get_rect(midbottom=(
                    car.x - math.cos(car.fov_direction) * 0.5 * offset_x,
                    car.y + math.sin(car.fov_direction) * 2 * offset_y))

            elif math.pi / 2 <= angle < math.pi:
                car.fov_rect = car.rotated_fov_surface.get_rect(bottomright=(
                    car.x - math.cos(car.fov_direction) * 0.5 * offset_x,
                    car.y - math.sin(car.fov_direction) * offset_y))

            elif math.pi <= angle < math.pi * 3 / 2:
                car.fov_rect = car.rotated_fov_surface.get_rect(midright=(
                    car.x - math.cos(car.fov_direction) * 2 * offset_x,
                    car.y + math.sin(car.fov_direction) * 0.5 * offset_y))

            else:
                car.fov_rect = car.rotated_fov_surface.get_rect(bottomleft=(
                    car.x + math.cos(car.fov_direction) * offset_x,
                    car.y + math.sin(car.fov_direction) * 0.5 * offset_y))


    def check_collisions(self, car, dt, scaled_dt):
        """Controllo collisioni e gestione visione dei veicoli"""

        def check_behind(car, enemy_car):
            """Controlla se la macchina si trova davanti ad un'altra"""
            if car != enemy_car:
                if car.direction == 'DX':
                    if 0 <= car.fov_direction < math.pi/2:
                        return car.x > enemy_car.x
                    elif math.pi/2 <= car.fov_direction < math.pi:
                        return car.y < enemy_car.y
                    elif math.pi <= car.fov_direction < 3/2 * math.pi:
                        return car.x < enemy_car.x
                    else:
                        return car.y > enemy_car.y
                elif car.direction == 'SX':
                    if 0 < car.fov_direction <= math.pi/2:
                        return car.x > enemy_car.x
                    elif math.pi/2 < car.fov_direction <= math.pi:
                        return car.y < enemy_car.y
                    elif math.pi < car.fov_direction <= 3/2 * math.pi:
                        return car.x < enemy_car.x
                    else:
                        return car.y > enemy_car.y
       
        collided_semaphore = False
        collided_vehicle = False
        # Controllo collisione con il semaforo
        if car.fov_rect.collidepoint(car.reference_traffic_light) and car.target < 3:
            collided_semaphore = True
            lane_traffic_light = self.traffic_lights[car.source_index]
            remaining_yellow_time = abs(self.yellow_time - self.traffic_lights_timer)
            if lane_traffic_light.state != 'GREEN':
                car.update_car_state(traffic_light=lane_traffic_light,
                                    yellow_remaining_time=remaining_yellow_time,
                                    enemy_car_coords=None,
                                    enemy_speed=None,
                                    enemy_length=None,
                                    enemy_source_index=None,
                                    dt=dt, scaled_dt=scaled_dt)
            elif lane_traffic_light.state == 'GREEN':
                for enemy_car in self.car_group:
                    if enemy_car != car and car.fov_rect.colliderect(enemy_car.rect) and enemy_car.source_index == car.source_index and not check_behind(car, enemy_car):
                        collided_vehicle = True
                        enemy_car_coords = (enemy_car.x, enemy_car.y)
                        enemy_speed = enemy_car.speed
                        enemy_length = enemy_car.rect.height if 1 <= enemy_car.source_index <= 2 or 5 <= enemy_car.source_index <= 6 else enemy_car.rect.width
                        car.update_car_state(traffic_light=None,
                                            yellow_remaining_time=None,
                                            enemy_car_coords=enemy_car_coords,
                                            enemy_speed=enemy_speed,
                                            enemy_length=enemy_length,
                                            enemy_source_index=enemy_car.source_index,
                                            dt=dt, scaled_dt=scaled_dt)
                    else:
                        car.update_car_state(traffic_light=lane_traffic_light,
                                    yellow_remaining_time=remaining_yellow_time,
                                    enemy_car_coords=None,
                                    enemy_speed=None,
                                    enemy_length=None,
                                    enemy_source_index=None,
                                    dt=dt, scaled_dt=scaled_dt)


        # Controllo collisioni con altri veicoli
        for enemy_car in self.car_group:
            if enemy_car != car and car.fov_rect.colliderect(enemy_car.rect) and enemy_car.source_index == car.source_index and not check_behind(car, enemy_car):
                collided_vehicle = True
                enemy_car_coords = (enemy_car.x, enemy_car.y)
                enemy_speed = enemy_car.speed
                enemy_length = enemy_car.rect.height if 1 <= enemy_car.source_index <= 2 or 5 <= enemy_car.source_index <= 6 else enemy_car.rect.width
                car.update_car_state(traffic_light=None,
                                    yellow_remaining_time=None,
                                    enemy_car_coords=enemy_car_coords,
                                    enemy_speed=enemy_speed,
                                    enemy_length=enemy_length,
                                    enemy_source_index=enemy_car.source_index,
                                    dt=dt, scaled_dt=scaled_dt)

        # Gestione evento incidente
        for enemy_car in self.car_group:
            if enemy_car != car:
                if car.rect.colliderect(enemy_car.rect):
                    if car.source_index == enemy_car.source_index and car.target < 3 and enemy_car.target < 3:
                        car.crash_case(enemy_car, scaled_dt)
       
        # Display degli incidenti
        for enemy_car in self.car_group:
            if enemy_car != car:
                if car.plate not in self.crashed_plates and enemy_car.plate not in self.crashed_plates and car.crashed and enemy_car.crashed and car.target < 3 and enemy_car.target < 3:
                    self.crashed_plates.append(car.plate)
                    self.crashed_plates.append(enemy_car.plate)
                    self.crash_counter += 1
                    print("Numero di incidenti: ", self.crash_counter)
                    print("Macchine incidentate: ", self.crashed_plates)

        if not collided_semaphore and not collided_vehicle:
            car.no_collision_case(scaled_dt)


    def draw_clock(self):
        """Disegna il testo dell'orologio in alto a destra"""

        font = pygame.font.Font(None, 38)
        text = font.render(str(self.time_string), True, (255, 255, 255))
        screen.blit(text, ((750, 60)))


    def update_main_clock(self, scaled_dt, dt):
        """Esegue l'aggiornamento dei veicoli e relativo FOV"""

        self.draw_clock()

        for car in self.car_group:

            car.update(scaled_dt, dt, self.traffic_lights[car.source_index])
            self.draw_fov(car)
            self.check_collisions(car, dt, scaled_dt)
       
        self.car_group.draw(screen)


    def fast_forward(self):
        """Gestisce il click sul bottone di fast forward"""

        if intersection.time_lapse == 1:
            intersection.time_lapse = 3
        elif intersection.time_lapse == 3:
            intersection.time_lapse = 1


    def pause(self):
        """Gestisce il click sul bottone di pausa"""

        if intersection.time_lapse == 1 or intersection.time_lapse == 3:
            intersection.time_lapse = 0.0000001
        elif intersection.time_lapse == 0.0000001:
            intersection.time_lapse = 1


    def generate_color_palette(self):
        """Genera la palette dei colori iniziale"""
       
        for i, key in enumerate(self.color_palette):

            self.color_palette[key] = {
                'Grass': self.grass_colors[i],
                'Sidewalk': self.sidewalk_colors[i],
                'Road': self.road_colors[i],
                'Lane_Divider': self.lane_divider_colors[i],
                'Lane_Lines': self.lane_lines_colors[i]
            }


    def update_color_palette(self):
        """Aggiorna la palette dei colori in base al tempo della giornata"""

        self.colors = self.color_palette[self.day_of_time]


    def update_available_lanes(self):
        """Aggiorna le corsie disponibili in base alla distanza"""

        def calculate_distance(target, car):
            dx = target[0] - car.x
            dy = target[1] - car.y
            return math.hypot(dx, dy)
       
        threshold = 100

        # Gestione della velocità in entrata in funzione del traffico in corsia
        for i in range(1, 9):
            min = 1000
            for car in self.car_group:
                if car.source_index == i and car.speed < 20:
                    distance = calculate_distance(self.points[i], car)
                    if distance < min:
                        min = distance
           
            self.min_distance_dict[i] = min

            if min < threshold:
                self.lanes_dict[i][0] = False
            else:
                self.lanes_dict[i][0] = True


    def grafana_redirect(self):
        """Link di redirect alla dashboard Grafana"""

        webbrowser.open("http://localhost:3000")

# Inizializzazione intersezione e interfaccia pygame
FPS = 60
intersection = Intersection(1000, 900, 280)

pygame.init()

change_time = int(input("Inserisci l'ora da cui iniziare la simulazione: "))
change_time_ms = change_time * 3_600_000

intersection.start_time = change_time_ms + pygame.time.get_ticks()
intersection.traffic_lights_timer = intersection.start_time
intersection.current_time_ms = intersection.start_time
intersection.generate_color_palette()
init_database()

intersection.start_cycle()

# Inizializzazione schermo
screen = pygame.display.set_mode((intersection.width, intersection.height))
pygame.display.set_caption("Simulazione Traffico")

# Definizione dizionario immagini
car_images = ['./img/car.png', 'img/car_black.png', 'img/car_yellow.png', 'img/car_green.png', 'img/car_blue.png']
bus_images = ['img/bus.png']
truck_images = ['img/truck.png']
moto_images = ['img/motorbike.png']
vehicle_type_dict = {
    'Car': car_images,
    'Bus': bus_images,
    'Truck': truck_images,
    'Moto': moto_images
}

# Main Loop
running = True
while running:

    # Gestione del clock
    dt = intersection.clock.tick(FPS)
    scaled_dt = dt * intersection.time_lapse

    intersection.update_spawn_interval()
    intersection.update_day_of_time()

    screen.fill(intersection.colors['Grass'])

    # Funzioni di aggiornamento della grafica dell'interfaccia
    intersection.draw_interface(intersection.width, intersection.height, intersection.road, intersection.time_lapse, scaled_dt)
    intersection.update_current_time(scaled_dt)
    intersection.update_timer(scaled_dt)
    intersection.update_traffic_lights_state()
    intersection.update_traffic_lights_color()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Gestione eventi di click sui pulsanti
        if event.type == pygame.MOUSEBUTTONDOWN:
            if intersection.pause_rect.collidepoint(event.pos):
                intersection.pause()
            if intersection.ff_rect.collidepoint(event.pos):
                intersection.fast_forward()
            if intersection.graphics_rect.collidepoint(event.pos):
                intersection.grafana_redirect()

    # Funzioni di aggiornamento delle funzionalità dell'interfaccia
    intersection.update_available_lanes()
    intersection.spawn_vehicle()
    intersection.update_main_clock(scaled_dt, dt)
    pygame.display.flip()

pygame.quit()
