import pytest
import requests
import psycopg2

# Base URL for the Flask application
BASE_URL = "http://flask_app:4000"
# Database connection URL
DB_URL = 'postgresql://postgres:postgres@flask_db:5432/postgres'

def execute_sql(sql, db_url=DB_URL, fetch=False):
    """ Helper function to execute SQL commands """
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            if fetch:
                result = cur.fetchall()
                return result
            conn.commit()

def test_get_simulations():
    """ Test to fetch simulations """
    # Setup data for this test
    setup_sql = "INSERT INTO simulations (name, status) VALUES ('Test Simulation 1', 'pending') RETURNING id;"
    sim_id = execute_sql(setup_sql, fetch=True)[0][0]

    # Perform the test
    response = requests.get(f"{BASE_URL}/simulations")
    assert response.status_code == 200
    simulations = response.json()
    assert len(simulations) > 0
    assert any(sim['name'] == 'Test Simulation 1' for sim in simulations)

    # Teardown data after test
    teardown_sql = f"DELETE FROM simulations WHERE id = {sim_id};"
    execute_sql(teardown_sql)

def test_create_simulation():
    """ Test to create a new simulation """
    # Perform the test
    data = {"name": "Test Simulation 3"}
    response = requests.post(f"{BASE_URL}/simulations", json=data)
    assert response.status_code == 201
    assert response.json()['message'] == 'Simulation created'

    # Validate insertion
    response = requests.get(f"{BASE_URL}/simulations")
    simulations = response.json()
    assert any(sim['name'] == 'Test Simulation 3' for sim in simulations)

    # Teardown data after test
    teardown_sql = "DELETE FROM simulations WHERE name = 'Test Simulation 3';"
    execute_sql(teardown_sql)

def test_update_simulation_status():
    """ Test to update the status of a simulation """
    # Setup data for this test
    setup_sql = "INSERT INTO simulations (name, status) VALUES ('Test Simulation 4', 'pending') RETURNING id;"
    sim_id = execute_sql(setup_sql, fetch=True)[0][0]

    # Perform the test
    data = {"status": "running"}
    response = requests.patch(f"{BASE_URL}/simulations/{sim_id}", json=data)
    assert response.status_code == 200
    assert response.json()['message'] == 'Simulation updated successfully'

    response = requests.get(f"{BASE_URL}/simulations/{sim_id}")
    simulation = response.json()
    assert simulation['status'] == 'running'

    # Teardown data after test
    teardown_sql = f"DELETE FROM simulations WHERE id = {sim_id};"
    execute_sql(teardown_sql)

def test_delete_simulation():
    """ Test to delete a simulation """
    # Setup data for this test
    setup_sql = "INSERT INTO simulations (name, status) VALUES ('Test Simulation 5', 'pending') RETURNING id;"
    sim_id = execute_sql(setup_sql, fetch=True)[0][0]

    # Perform the test
    response = requests.delete(f"{BASE_URL}/simulations/{sim_id}")
    assert response.status_code == 200
    assert response.json()['message'] == 'Simulation deleted successfully'

    # Validate deletion
    response = requests.get(f"{BASE_URL}/simulations/{sim_id}")
    assert response.status_code == 404
    assert response.json()['message'] == 'Simulation not found'

    # No need for teardown SQL as the simulation was deleted in the test

def test_get_machines():
    """ Test to get machines """
    # No specific setup required as this reads existing data

    # Perform the test
    response = requests.get(f"{BASE_URL}/machines")
    assert response.status_code == 200
    machines = response.json()
    assert len(machines) > 0
    assert any(machine['name'] == 'Machine A' for machine in machines)  # This assumes 'Test Machine A' exists

def test_create_machine():
    """ Test to create a new machine """
    # Perform the test
    data = {"name": "Test Machine C"}
    response = requests.post(f"{BASE_URL}/machines", json=data)
    assert response.status_code == 201
    assert response.json()['message'] == 'Machine created successfully'

    # Validate insertion
    response = requests.get(f"{BASE_URL}/machines")
    machines = response.json()
    assert any(machine['name'] == 'Test Machine C' for machine in machines)

    # Teardown data after test
    teardown_sql = "DELETE FROM machines WHERE name = 'Test Machine C';"
    execute_sql(teardown_sql)
