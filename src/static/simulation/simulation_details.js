const apiBaseURL = 'http://localhost:4000';
let socket = null;
let convergenceChart = null;
let simulationId = null;

document.addEventListener('DOMContentLoaded', function() {
    const pathArray = window.location.pathname.split('/');
    simulationId = pathArray[pathArray.length - 1];

    loadSimulationDetails(simulationId, true);
    fetchConvergenceDataAndUpdateGraph(simulationId);

    window.onunload = function() {
        if (socket) {
            socket.emit('leave', {simulation_id: simulationId.toString()});
        }
    };
});

function initializeSocketListeners() {
    if (!socket) {
        socket = io.connect(apiBaseURL);
    }
    socket.removeAllListeners();

    socket.on('connect', function() {
        console.log('Socket connected.');
        socket.emit('join', {simulation_id: simulationId.toString()});
    });

    socket.on('update', function(data) {
        if (data && data.data) {
            const newTime = data.data.seconds;
            const newLoss = data.data.loss;
            updateConvergenceGraphLive(newTime, newLoss);
            loadSimulationDetails(simulationId);
        }
    });
}

function updateConvergenceGraphLive(newTime, newLoss) {
    if (convergenceChart) {
        convergenceChart.data.labels.push(newTime);
        convergenceChart.data.datasets.forEach((dataset) => {
            dataset.data.push(newLoss);
        });
        convergenceChart.update();
    }
}

function loadSimulationDetails(simulationId, initializeSocket = false) {
    fetch(`${apiBaseURL}/simulations/${simulationId}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('detailsContainer');
            container.innerHTML = `
                <p id="simName">Name: ${data.name}</p>
                <p id="creationDate">Creation Date: ${data.creation_date}</p>
                <p id="updateDate">Update Date: ${data.update_date}</p>
                <p id="machineName">Machine: ${data.machine_name}</p>
                <p id="simStatus">Status: ${data.status}</p>
                <p id="simEpochs">Epochs: ${data.epochs}</p>
                <p id="finalLoss">Final Loss: ${data.final_loss}</p>
                <p id="totalSeconds">Total Seconds: ${data.total_seconds}</p>
            `;
            updateManagementControls(data.status, simulationId);
            if (initializeSocket && data.status === 'running') {
                initializeSocketListeners();
            }
        })
        .catch(error => console.error('Failed to load simulation details:', error));
}

function updateManagementControls(status, simulationId) {
    const managementControls = document.getElementById('managementControls');
    managementControls.innerHTML = '';

    if (status === 'pending' || status === 'finished') {
        managementControls.innerHTML = `
            <select id="machineSelect"></select>
            <button onclick="runSimulationOnMachine(${simulationId})">Run on Machine</button>
        `;
        loadAvailableMachines();
    } else if (status === 'running') {
        managementControls.innerHTML = `<button onclick="endSimulation(${simulationId})">End Simulation</button>`;
    }
}

function loadAvailableMachines() {
    fetch(`${apiBaseURL}/machines`)
        .then(response => response.json())
        .then(machines => {
            const machineSelect = document.getElementById('machineSelect');
            machineSelect.innerHTML = '';
            machines.forEach(machine => {
                if (machine.availability) {
                    const option = document.createElement('option');
                    option.value = machine.id;
                    option.textContent = machine.name;
                    machineSelect.appendChild(option);
                }
            });
        })
        .catch(error => console.error('Error loading available machines:', error));
}

function runSimulationOnMachine(simulationId) {
    const machineId = document.getElementById('machineSelect').value;
    assignMachineToSimulation(simulationId, machineId);
}

function endSimulation(simulationId) {
    updateSimulationStatus(simulationId, 'finished');
    if (socket) {
        console.log('Socket disconnected.');
        socket.emit('leave', {simulation_id: simulationId.toString()});
    }
}

function updateSimulationStatus(simulationId, newStatus) {
    const payload = { status: newStatus };

    fetch(`${apiBaseURL}/simulations/${simulationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(response => response.json())
      .then(data => {
          loadSimulationDetails(simulationId, true);
      })
      .catch(error => alert('Error updating status: ' + error.message));
}

function assignMachineToSimulation(simulationId, machineId) {
    const payload = { machine_id: machineId };

    fetch(`${apiBaseURL}/simulations/${simulationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(response => response.json())
      .then(data => {
          loadSimulationDetails(simulationId, true);
      })
      .catch(error => alert('Error assigning machine: ' + error.message));
      socket.emit('join', {simulation_id: simulationId.toString()});
}

function fetchConvergenceDataAndUpdateGraph(simulationId) {
    fetch(`${apiBaseURL}/simulations/${simulationId}/convergence`)
        .then(response => response.json())
        .then(data => {
            updateConvergenceGraph(data);
        })
        .catch(error => console.error('Failed to load convergence data:', error));
}

function updateConvergenceGraph(data) {
    const ctx = document.getElementById('convergenceGraph').getContext('2d');
    const labels = data.map(d => d.seconds);
    const lossValues = data.map(d => d.loss);

    if (convergenceChart) {
        convergenceChart.destroy();
    }

    convergenceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Loss',
                data: lossValues,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Loss'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}
