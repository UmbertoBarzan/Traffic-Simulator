CREATE TABLE IF NOT EXISTS Traffic_Light (
                    id INT PRIMARY KEY,
                    n_vehicle INT,
                    type VARCHAR(15));

CREATE TABLE IF NOT EXISTS Vehicle (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    plate VARCHAR(10),
                    source INT,
                    spawn_time TIME,
                    exit_time TIME,
                    wait_time INT,
                    avg_speed FLOAT,
                    type VARCHAR(30),
                    system_time INT,
                    spawn_datetime DATETIME,
                    exit_datetime DATETIME,
                    FOREIGN KEY (source) REFERENCES Traffic_Light(id));

UPDATE Traffic_Light SET n_vehicle=0;
TRUNCATE TABLE Vehicle;