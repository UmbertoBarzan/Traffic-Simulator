def calcola_punti(width, height, road):
    """Calcolo dei 32 punti che rappresentano ingressi, semafori, uscite intermedie e uscite.
    Ritorna un dizionario che ha come chiave un indice da 1 a 32 e come valore le coordinate x e y dei punti"""

    #List comprehension per i valori in mezzo alle corsie
    intermedi_x = [x for x in range(width//2 - road*3//8, width//2 + road*3//8 + 1, road//4)]
    intermedi_y = [y for y in range(height//2 - road*3//8, height//2 + road*3//8 + 1, road//4)]

    #Calcolo dei valori corrispondenti ai bordi delle strade
    limiti_x, limiti_y = [[width//2 - road//2, width//2 + road//2],[height//2 - road//2, height//2 + road//2]]

    #Definizione delle sequenze per iterare e un dizionario che divide in ottetti i punti
    sequenza_x_1, sequenza_y_1 = [[2, 3, 1, 0],[1, 0, 2, 3]] # Z 0 & 1
    sequenza_x_2, sequenza_y_2 = [[0, 1, 3, 2],[3, 2, 0, 1]] # Z 2 & 3
    sequenza_x_3, sequenza_y_3 = [[width, 0],[height, 0]] # Z 0 & 3
    sequenza_x_4, sequenza_y_4 = [[limiti_x[1], limiti_x[0]],[limiti_y[1],limiti_y[0]]] # Z 1 & 2
    sequenze = {
        0: [sequenza_x_1, sequenza_y_1, sequenza_x_3, sequenza_y_3],
        1: [sequenza_x_1, sequenza_y_1, sequenza_x_4, sequenza_y_4],
        2: [sequenza_x_2, sequenza_y_2, sequenza_x_4, sequenza_y_4],
        3: [sequenza_x_2, sequenza_y_2, sequenza_x_3, sequenza_y_3]
    }

    #Definizione di contatori e dizionario finale
    index = 1
    punti = {}
    z, k, conta_2_x, conta_2_y, conta_4_x, conta_4_y = [0, 0, 0, 0, 0, 0]

    #Algoritmo per generare x e y nel dizionario
    for z in range(4):
        conta_2_x, conta_2_y, conta_4_x, conta_4_y = [0, 0, 0, 0]
        sequenza4x, sequenza4y, sequenza2x, sequenza2y = sequenze[z]
        for k in range(4):
            if k % 2 == 0:
                punti[index] = [intermedi_x[sequenza4x[conta_4_x]], sequenza2y[conta_2_y]]
                punti[index + 1] = [intermedi_x[sequenza4x[conta_4_x + 1]], sequenza2y[conta_2_y]]
                conta_4_x += 2
                conta_2_y += 1
            else:
                punti[index] = [sequenza2x[conta_2_x], intermedi_y[sequenza4y[conta_4_y]]]
                punti[index + 1] = [sequenza2x[conta_2_x], intermedi_y[sequenza4y[conta_4_y + 1]]]
                conta_2_x += 1
                conta_4_y += 2
            index += 2

    return punti
