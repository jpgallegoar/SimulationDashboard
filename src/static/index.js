const apiBaseURL = 'http://localhost:4000';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('createSimulationForm').onsubmit = function(event) {
        event.preventDefault();
        const name = document.getElementById('simName').value;
        const machineId = document.getElementById('machineSelect').value;
        createSimulation(name, machineId);
    };

    document.getElementById('createMachineForm').onsubmit = function(event) {
        event.preventDefault();
        const name = document.getElementById('machineName').value;
        createMachine(name);
    };

    document.getElementById('filterStatus').addEventListener('change', loadSimulations);
    document.getElementById('orderBy').addEventListener('change', loadSimulations);
    document.getElementById('orderDirection').addEventListener('change', loadSimulations);

    loadMachines();
    loadSimulations();
});

window.onpageshow = function(event) {
    if (event.persisted) {
        window.location.reload();
    }
};

function loadMachines() {
    console.log('Loading machines...');
    fetch(`${apiBaseURL}/machines`)
        .then(response => response.json())
        .then(machines => {
            const machineSelect = document.getElementById('machineSelect');
            machineSelect.innerHTML = '<option value="none">None</option>';
            machines.forEach(machine => {
                if (machine.availability) {
                    const option = document.createElement('option');
                    option.value = machine.id;
                    option.textContent = machine.name;
                    machineSelect.appendChild(option);
                }
            });
        })
        .catch(error => console.error('Error loading machines:', error));
}

function loadSimulations() {
    console.log('Loading sims...');
    const status = document.getElementById('filterStatus').value;
    const orderBy = document.getElementById('orderBy').value;
    const orderDirection = document.getElementById('orderDirection').value;
    const simulationsList = document.getElementById('simulationsList');
    simulationsList.innerHTML = '';

    fetch(`${apiBaseURL}/simulations?status=${status}&order_by=${orderBy}&order_direction=${orderDirection}`)
        .then(response => response.json())
        .then(simulations => {
            simulations.forEach(simulation => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <a href="/simulation/${simulation.id}">Name: ${simulation.name}, Machine: ${simulation.machine_name}, Status: ${simulation.status}</a>
                    <button onclick="deleteSimulation(${simulation.id})">Delete</button>
                `;
                simulationsList.appendChild(li);
            });
        })
        .catch(error => console.error('Error loading simulations:', error));
}

function createSimulation(name, machineId) {
    let status = machineId === "none" ? "pending" : "running";
    machineId = machineId === "none" ? null : machineId;
    
    fetch(`${apiBaseURL}/simulations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, machine_id: machineId, status }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        loadMachines();
        loadSimulations();
        document.getElementById('createSimulationForm').reset();
    })
    .catch(error => alert('Error: ' + error.message));
}

function createMachine(name) {
    fetch(`${apiBaseURL}/machines`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        loadMachines();
        document.getElementById('createMachineForm').reset();
    })
    .catch(error => alert('Error: ' + error.message));
}

function deleteSimulation(simulationId) {
    fetch(`${apiBaseURL}/simulations/${simulationId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        loadSimulations();
        loadMachines();
    })
    .catch(error => alert('Error: ' + error.message));
}
