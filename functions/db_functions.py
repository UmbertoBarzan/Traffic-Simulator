import mysql.connector

def init_database():
    
    # Connessione al DB
    conn = mysql.connector.connect(
        host="localhost",
        user="user",  
        password="userpassword",  
        database="simulation_db"
    )

    # Controllo della connessione
    if conn.is_connected():
        print("Connected to the MySQL server")
        cursor = conn.cursor()
        
        # Reset dei dati dei veicoli
        cursor.execute("TRUNCATE TABLE Vehicle")

        # Reset dei sensori di prossimità
        cursor.execute("UPDATE Traffic_Light SET n_vehicle = 0")

        conn.commit()
        cursor.close()
        conn.close()
    else:
        raise Exception("Connection to the MySQL database failed")
