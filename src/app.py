from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import psycopg2
import psycopg2.extras
import os
import time
import threading
from threading import Thread
import logging

app = Flask(__name__, static_folder='static', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'postgresql://postgres:postgres@flask_db:5432/postgres')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

background_tasks = {}
client_counts = {}

def get_db_connection():
    return psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])

def query_db(query, args=(), one=False):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, args)
                rv = cur.fetchall()
                return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"Database query error: {e}")
        return []

def modify_db(query, args=()):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, args)
                conn.commit()
    except Exception as e:
        print(f"Database modification error: {e}")

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/simulation/<int:id>')
def simulation_detail_page(id):
    return send_from_directory(app.static_folder, 'simulation/simulation_details.html')

@app.route('/simulations', methods=['GET'])
def get_simulations():
    status = request.args.get('status')
    order_by = request.args.get('order_by', 'creation_date')
    order_direction = request.args.get('order_direction', 'DESC')

    query = """
        SELECT s.*, COALESCE(m.name, 'No Machine Assigned') as machine_name 
        FROM simulations s
        LEFT JOIN machines m ON s.machine_id = m.id
    """
    conditions = []

    if status:
        conditions.append(f"s.status = '{status}'")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if order_by:
        query += f" ORDER BY s.{order_by} {order_direction}"

    simulations = query_db(query)
    return jsonify([dict(simulation) for simulation in simulations])


@app.route('/simulations/<int:id>', methods=['GET'])
def get_simulation(id):
    query = """
        SELECT s.*, m.name as machine_name 
        FROM simulations s
        LEFT JOIN machines m ON s.machine_id = m.id
        WHERE s.id = %s
    """
    simulation = query_db(query, [id], one=True)
    if simulation:
        return jsonify(simulation)
    else:
        return jsonify({'message': 'Simulation not found'}), 404

@app.route('/simulations/<int:id>', methods=['PATCH'])
def update_simulation(id):
    data = request.get_json()
    new_status = data.get('status')
    new_machine_id = data.get('machine_id')

    if new_status and new_status not in ['pending', 'running', 'finished']:
        return jsonify({'message': 'Invalid status provided'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if new_machine_id:
                    machine = query_db("SELECT * FROM machines WHERE id = %s", [new_machine_id], one=True)
                    if not machine or not machine['availability']:
                        return jsonify({'message': 'Machine not available'}), 400
                    cur.execute("UPDATE machines SET availability = FALSE WHERE id = %s", [new_machine_id])
                    cur.execute("UPDATE simulations SET machine_id = %s, status = 'running' WHERE id = %s", (new_machine_id, id))
                elif new_status == 'finished':
                    cur.execute("UPDATE machines SET availability = TRUE WHERE id = (SELECT machine_id FROM simulations WHERE id = %s)", [id])
                    cur.execute("UPDATE simulations SET status = %s, machine_id = NULL WHERE id = %s", (new_status, id))
                elif new_status:
                    cur.execute("UPDATE simulations SET status = %s WHERE id = %s", (new_status, id))
                conn.commit()
    except Exception as e:
        return jsonify({'message': f'Error updating simulation: {e}'}), 500

    return jsonify({'message': 'Simulation updated successfully'}), 200

@app.route('/simulations/<int:id>', methods=['DELETE'])
def delete_simulation(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Update machine availability if the simulation is running
                cur.execute("UPDATE machines SET availability = TRUE WHERE id = (SELECT machine_id FROM simulations WHERE id = %s AND status = 'running')", [id])
                # Delete convergence data associated with the simulation
                cur.execute("DELETE FROM convergence_data WHERE simulation_id = %s", [id])
                # Delete the simulation
                cur.execute("DELETE FROM simulations WHERE id = %s", [id])
                conn.commit()
    except Exception as e:
        return jsonify({'message': f'Error deleting simulation: {e}'}), 500

    return jsonify({'message': 'Simulation and associated convergence data deleted successfully'}), 200


@app.route('/machines', methods=['GET'])
def get_machines():
    machines = query_db("SELECT * FROM machines")
    return jsonify([dict(machine) for machine in machines])

@app.route('/machines', methods=['POST'])
def create_machine():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Invalid input data'}), 400
    
    machine_name = data['name']

    try:
        modify_db("INSERT INTO machines (name, availability) VALUES (%s, TRUE)", (machine_name,))
        return jsonify({'message': 'Machine created successfully'}), 201
    except Exception as e:
        return jsonify({'message': f'Error creating machine: {e}'}), 500


@app.route('/simulations', methods=['POST'])
def create_simulation():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Invalid input data'}), 400
    
    machine_id = data.get('machine_id')
    status = "pending" if machine_id is None else "running"

    if machine_id:
        machine = query_db("SELECT * FROM machines WHERE id = %s", [machine_id], one=True)
        if not machine or not machine['availability']:
            return jsonify({'message': 'Machine not available'}), 400
        modify_db("UPDATE machines SET availability = FALSE WHERE id = %s", [machine_id])

    modify_db("INSERT INTO simulations (name, machine_id, status) VALUES (%s, %s, %s)", (data['name'], machine_id, status))
    return jsonify({'message': 'Simulation created'}), 201

@app.route('/simulations/<int:id>/convergence', methods=['GET'])
def get_convergence_data(id):
    query = """
        SELECT seconds, loss 
        FROM convergence_data
        WHERE simulation_id = %s
        ORDER BY seconds
    """
    convergence_data = query_db(query, [id])
    return jsonify(convergence_data)

last_sent_data = {}

def send_updates(sim_id):
    logging.info(f"Starting thread for simulation {sim_id}")
    while client_counts[sim_id] > 0:
        time.sleep(5)
        convergence_data = query_db("""
            SELECT seconds, loss FROM convergence_data 
            WHERE simulation_id = %s 
            ORDER BY seconds DESC LIMIT 1
        """, [sim_id], one=True)
        
        if convergence_data:
            last_data = last_sent_data.get(sim_id)
            if not last_data or (convergence_data['seconds'] != last_data['seconds'] or convergence_data['loss'] != last_data['loss']):
                logging.info(f"Sent update for simulation {sim_id}")
                socketio.emit('update', {'data': convergence_data}, room=sim_id)
                last_sent_data[sim_id] = convergence_data
    logging.info(f"Terminating thread for simulation {sim_id} as no clients are connected")
    background_tasks.pop(sim_id, None)

@socketio.on('join')
def on_join(data):
    sim_id = data['simulation_id']
    join_room(sim_id)
    client_counts[sim_id] = client_counts.get(sim_id, 0) + 1
    logging.info(f"Client joined room for simulation {sim_id}, total clients: {client_counts[sim_id]}")
    
    if sim_id not in background_tasks or not background_tasks[sim_id].is_alive():
        thread = threading.Thread(target=send_updates, args=(sim_id,))
        thread.start()
        background_tasks[sim_id] = thread

@socketio.on('leave')
def on_leave(data):
    sim_id = data['simulation_id']
    leave_room(sim_id)
    if sim_id in client_counts:
        client_counts[sim_id] -= 1
        logging.info(f"Client left room for simulation {sim_id}, remaining clients: {client_counts[sim_id]}")
        if client_counts[sim_id] <= 0:
            if sim_id in background_tasks:
                background_tasks[sim_id].join()

if __name__ == '__main__':
    socketio.run(app, debug=True)
