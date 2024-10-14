# Simulation Dashboard Project Documentation

## Overview
This is a Flask-based application designed to manage and monitor simulations. It utilizes Docker for containerization and PostgreSQL for database management. The project is structured into various directories and files, each serving distinct purposes within the development environment.

## Backend Documentation

### Directory Structure
- `src/`: Contains the main application code.
  - `app.py`: Main Flask application file.
  - `populate_convergence_data.py`: Script for populating the database with convergence data.
  - `requirements.txt`: Lists the Python dependencies.
- `sql/`: Contains SQL scripts for database initialization.
  - `init.sql`: Initializes the database tables and indexes.
- `tests/`: Contains test files for the application.
  - `_test.py`: Pytest test cases for API endpoints.

### API Endpoints

- **GET /simulations**: Fetch all simulations, with optional filters for status and sorting parameters.
- **GET /simulations/{id}**: Retrieve detailed information about a specific simulation.
- **POST /simulations**: Create a new simulation.
- **PATCH /simulations/{id}**: Update the status or machine assignment of a simulation.
- **DELETE /simulations/{id}**: Delete a specific simulation and its associated data.
- **GET /machines**: List all machines.
- **POST /machines**: Add a new machine to the database.

### Example Uses

#### Fetch all simulations

**Request**
```http
GET /simulations
```

**Response**
```json
[
    {
        "id": 1,
        "name": "Simulation 1",
        "status": "pending",
        "creation_date": "2024-06-12T12:34:56",
        "machine_name": "Machine A"
    },
    {
        "id": 2,
        "name": "Simulation 2",
        "status": "running",
        "creation_date": "2024-06-13T14:23:12",
        "machine_name": "Machine B"
    }
]
```

#### Retrieve detailed information about a specific simulation

**Request**
```http
GET /simulations/1
```

**Response**
```json
{
    "id": 1,
    "name": "Simulation 1",
    "status": "pending",
    "creation_date": "2024-06-12T12:34:56",
    "machine_name": "Machine A"
}
```

#### Create a new simulation

**Request**
```http
POST /simulations
Content-Type: application/json

{
    "name": "New Simulation",
    "machine_id": 1
}
```

**Response**
```json
{
    "message": "Simulation created"
}
```

#### Update the status or machine assignment of a simulation

**Request**
```http
PATCH /simulations/1
Content-Type: application/json

{
    "status": "finished"
}
```

**Response**
```json
{
    "message": "Simulation updated successfully"
}
```

#### Delete a specific simulation and its associated data

**Request**
```http
DELETE /simulations/1
```

**Response**
```json
{
    "message": "Simulation and associated convergence data deleted successfully"
}
```

#### List all machines

**Request**
```http
GET /machines
```

**Response**
```json
[
    {
        "id": 1,
        "name": "Machine A",
        "availability": true
    },
    {
        "id": 2,
        "name": "Machine B",
        "availability": false
    }
]
```

#### Add a new machine to the database

**Request**
```http
POST /machines
Content-Type: application/json

{
    "name": "Machine C"
}
```

**Response**
```json
{
    "message": "Machine created successfully"
}
```



# Docker Setup and Running the Application

Docker simplifies the setup of the Simulation Dashboard by containerizing the application and its dependencies. Follow these steps to get the application up and running using Docker:

## Prerequisites

1. **Docker**: You must have Docker installed on your system. If you do not have Docker installed, visit the official Docker installation guide to install the latest version.
2. **Docker Compose**: Ensure Docker Compose is installed. It usually comes with Docker for Windows and Docker for Mac, but if you're using Linux, you might need to install it separately. Refer to the official Docker Compose installation guide.

## Steps to Run the Application

### Clone the Repository (if not already done):

Open a terminal and clone the project repository using Git.

```bash
git clone https://github.com/jpgallegoar/SimulationDashboard.git
cd SimulationDashboard
```

### Navigate to the Source Directory:

Change to the directory containing the Docker configuration files.

```bash
cd src
```

### Build and Start the Containers:

Use Docker Compose to build and start the containers. This command builds the images if they don't exist and starts the containers in detached mode.

```bash
docker-compose up --build -d
```

Here, the `--build` flag tells Docker to build the images before starting the containers, ensuring any changes to the Dockerfiles are included. The `-d` flag runs the containers in the background.

### Verify the Containers are Running:

Check the status of the containers to ensure they are running properly.

```bash
docker-compose ps
```

### Accessing the Application:

Once the containers are up and running, open a web browser and navigate to `http://localhost:4000` to access the Simulation Dashboard. This is the default port set in the Docker configuration, but you can change it in `docker-compose.yml` if necessary.

### Stopping the Containers:

When you're done, you can stop the Docker containers by running:

```bash
docker-compose down
```

## Additional Docker Commands

### View Logs:

If you need to check the logs for a container, use:

```bash
docker-compose logs flask_app
```


### Rebuild Containers:

To rebuild the containers after making changes to the Dockerfiles or associated files:

```bash
docker-compose up --build -d
```

### Cleaning Up:

To remove all containers, networks, and images created by Docker Compose:

```bash
docker-compose down --rmi all
```



## Frontend Documentation

### Usage Tutorial
1. **Accessing the Dashboard**:
   - Open a web browser and navigate to the URL where the application is hosted (typically `http://localhost:4000` for local setups).

2. **Creating a Machine**:
   - Three machines are automatically inserted into the database on setup ("Machine A", "Machine B" and "Machine C")
   - Navigate to the 'Create Machine' form on the main dashboard.
   - Enter a machine name and click 'Create Machine'.

3. **Creating a Simulation**:
   - Use the 'Create Simulation' form to specify the simulation name and assign a machine.
   - Click 'Create Simulation' to initialize the process.

4. **Viewing and Managing Simulations**:
   - Simulations can be filtered and sorted using the provided dropdown menus.
   - Each simulation has a detailed view where you can see specific metrics and manage its status or assigned machine.

5. **Interacting with Simulations**:
   - Detailed simulation views allow for real-time monitoring of simulation metrics via a convergence graph.
   - The graph will update in real-time as long as a simulation is running (every 10 seconds, a new convergence entry is created for each running simulation)
   - Management options vary based on simulation status

### Frontend Structure
- `static/`: Holds static files like HTML, CSS, and JavaScript.
  - `index.html`: Main entry point of the frontend.
  - `simulation_details.html`: Provides a detailed view for individual simulations.
  - `style.css`: CSS files for styling.
  - `index.js` and `simulation_details.js`: JavaScript files handling UI logic and API interaction.

## Additional Notes
- The application is designed to be modular and scalable, accommodating changes or extensions to its functionalities.
- Security practices (such as CORS and environment variable management) are implemented to safeguard the application data and operation.