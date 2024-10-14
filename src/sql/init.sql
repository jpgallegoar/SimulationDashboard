CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    availability BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE simulations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    creation_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    update_date TIMESTAMP WITHOUT TIME ZONE,
    epochs INT,
    status VARCHAR(50) DEFAULT 'pending',
    final_loss FLOAT,
    total_seconds INT,
    machine_id INT,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE TABLE convergence_data (
    simulation_id INT,
    seconds INT,
    loss FLOAT,
    PRIMARY KEY (simulation_id, seconds),
    FOREIGN KEY (simulation_id) REFERENCES simulations(id)
);

CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_creation_date ON simulations(creation_date);

INSERT INTO machines (name, availability) VALUES ('Machine A', TRUE);
INSERT INTO machines (name, availability) VALUES ('Machine B', TRUE);
INSERT INTO machines (name, availability) VALUES ('Machine C', TRUE);