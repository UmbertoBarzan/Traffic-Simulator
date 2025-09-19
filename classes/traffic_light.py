class Traffic_Light:
    def __init__(self, x, y):

        # Inizializzazione del semaforo
        self.state = 'RED'
        self.x = x
        self.y = y
        self.id = 1 
        self.proximity_sensor = 0

        # Gestione dei colori
        self.color_dict = {
            'RED': (255, 0, 0),
            'YELLOW': (255, 255, 0),
            'GREEN': (0, 255, 0)
        }
        self.color = self.color_dict[self.state]

    def update_color(self):
        """Aggiorna il colore in base allo stato"""

        self.color = self.color_dict[self.state]
