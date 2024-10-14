import time
import random
import psycopg2
import psycopg2.extras
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URI = os.getenv('DB_URL', 'postgresql://postgres:postgres@flask_db:5432/postgres')

def get_db_connection():
    return psycopg2.connect(DATABASE_URI)

def update_convergence_data():
    while True:
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Select running simulations
                    cur.execute("SELECT id, epochs, final_loss, total_seconds FROM simulations WHERE status = 'running'")
                    running_simulations = cur.fetchall()
                    for simulation in running_simulations:
                        sim_id = simulation['id']
                        # Get the latest convergence data
                        cur.execute("SELECT * FROM convergence_data WHERE simulation_id = %s ORDER BY seconds DESC LIMIT 1", (sim_id,))
                        last_entry = cur.fetchone()
                        new_seconds = 10 if not last_entry else last_entry['seconds'] + 10
                        
                        # Adjust loss
                        initial_loss = 1.0
                        if last_entry:
                            loss_reduction_factor = 0.05 * (0.9 ** simulation['epochs'])  # Decaying factor
                            new_loss = max(0, last_entry['loss'] - loss_reduction_factor + random.uniform(-0.005, 0.005))
                        else:
                            new_loss = initial_loss
                        
                        new_loss = round(new_loss, 3)

                        # Insert new convergence data
                        cur.execute("INSERT INTO convergence_data (simulation_id, seconds, loss) VALUES (%s, %s, %s)", (sim_id, new_seconds, new_loss))
                        
                        # Update simulation details
                        new_epochs = simulation['epochs'] + 1 if simulation['epochs'] else 1
                        new_final_loss = new_loss
                        new_total_seconds = new_seconds
                        cur.execute("""
                            UPDATE simulations SET 
                                update_date = NOW(), 
                                epochs = %s, 
                                final_loss = %s, 
                                total_seconds = %s 
                            WHERE id = %s
                        """, (new_epochs, new_final_loss, new_total_seconds, sim_id))
                        
                        conn.commit()
                        logging.info(f"Updated simulation {sim_id}: epochs={new_epochs}, final_loss={new_final_loss}, total_seconds={new_total_seconds}")
                        logging.info(f"Inserted convergence data for simulation {sim_id}: seconds={new_seconds}, loss={new_loss}")
        except Exception as e:
            logging.error(f"Error updating convergence data and simulation details: {e}")
        time.sleep(10)

if __name__ == '__main__':
    update_convergence_data()
