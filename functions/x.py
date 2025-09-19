import numpy as np

values = {
    1: [True, "Verticale", "SX"],
    2: [True, "Verticale", "DX"],
    3: [False, "Orizzontale", "SX"],
    4: [True, "Orizzontale", "DX"],
    5: [True, "Verticale", "SX"],
    6: [True, "Verticale", "DX"],
    7: [True, "Orizzontale", "SX"],
    8: [True, "Orizzontale", "DX"]
}

# Filtra solo le chiavi con il primo valore True
lista_true = [k for k, v in values.items() if v[0]]

# Divide in SX e DX
sx_list = [k for k in lista_true if values[k][2] == 'SX']
dx_list = [k for k in lista_true if values[k][2] == 'DX']

lista_sx_dx = [sx_list, dx_list]  # Contiene le due liste
prob = [0.35, 0.65]  # Probabilità di scegliere sx_list o dx_list

# Scegli casualmente tra sx_list e dx_list
index = np.random.choice([0, 1], p=prob)
lista_sx_dx_random = lista_sx_dx[index]

hor_list = [x for x in lista_sx_dx_random if values[x][1] == 'Orizzontale']
vert_list = [x for x in lista_sx_dx_random if values[x][1] == 'Verticale']
prob = [0.55, 0.45]

hor_vert_list = [hor_list, vert_list]
index = np.random.choice([0, 1], p=prob)
hor_vert_list_random = hor_vert_list[index]
print(hor_vert_list_random)

if len(hor_vert_list_random) == 0:
    random_lane = None
elif len(hor_vert_list_random) == 1:
    random_lane = hor_vert_list_random[0]
elif len(hor_vert_list_random) == 2:
    random_lane = hor_vert_list_random[np.random.randint(0,1)]

print(random_lane)
