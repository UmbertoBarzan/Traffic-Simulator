# Traffic Simulator

This project is a pygame-based traffic intersection simulator connected to a MySQL backend and visualised through Grafana dashboards. Vehicles enter and exit an intersection with configurable traffic-light logic, collision handling, and time-of-day changes that affect spawn rates and the colour palette.

## Features
- 2D intersection rendered with `pygame`, featuring vehicle sprites, pedestrian crossings, and traffic-light cycles.
- Dynamic vehicle spawning with multiple vehicle types and congestion-aware lane availability.
- Time scaling controls: toggle pause and fast-forward to inspect the simulation flow.
- MySQL database for persisting per-vehicle and per-traffic-light metrics, with dockerised services for MySQL, phpMyAdmin, and Grafana dashboards.

## Requirements
- Python 3.10+
- Docker and Docker Compose (for the database and dashboard stack)
- Python packages: `pygame`, `numpy`, `mysql-connector-python`

## Quick Start
1. (Optional) Create and activate a Python virtual environment.
2. Install the Python dependencies:
   ```bash
   pip install pygame numpy mysql-connector-python
   ```
3. Start the database and dashboard services:
   ```bash
   docker compose up -d
   ```
   - MySQL: `localhost:3306` (user `user`, password `userpassword`)
   - phpMyAdmin UI: `http://localhost:8081`
   - Grafana UI: `http://localhost:3000` (admin/admin)
4. Launch the simulator:
   ```bash
   python main.py
   ```
5. Enter the hour (0-23) from which the simulation should start when prompted. The pygame window shows the intersection, current simulated time, traffic lights, and vehicle activity.

## Controls
- Click the pause button to freeze/resume time.
- Click the fast-forward button to toggle an accelerated time scale.
- Click the dashboard icon to open the Grafana dashboard in your browser.

## Data & Dashboards
The script initialises the `simulation_db` schema and writes traffic metrics while the simulation runs. Grafana dashboards are provisioned automatically from `grafana_provisioning/` and can be customised to visualise the collected data.

## Stopping Services
When you finish experimenting, stop the docker services:
```bash
docker compose down
```
