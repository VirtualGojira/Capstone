import random
from qiskit import QuantumCircuit, Aer, execute
import time

num_runs = 100
execution_times = []

for _ in range(num_runs):
    start_time = time.time()
    # Step 1: Alice generates random secret bits and bases
    alice_bits = [random.getrandbits(1) for _ in range(500)]  # Alice's 500 secret bits (0 or 1)
    alice_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Alice's random bases ('Z' or 'X')

    # Step 2: Encoding Alice's qubits
    encoded_qubits = []
    for i in range(500):
        bit = alice_bits[i]
        base = alice_bases[i]

        qc = QuantumCircuit(1, 1)  # 1 qubit, 1 classical bit

        if base == 'Z':
            if bit == 1:
                qc.x(0)  # Apply X gate to flip the qubit to state |1> if bit is 1
        else:  # base == 'X'
            if bit == 0:
                qc.h(0)  # Apply H gate to put the qubit in |+> state if bit is 0
            else:
                qc.x(0)
                qc.h(0)  # Apply X and H gates to transform to |-> state if bit is 1

        encoded_qubits.append(qc)

    # Step 3: Bob chooses random measurement bases
    bob_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Bob's random bases ('Z' or 'X')

    # Step 4: Bob measures Alice's qubits
    bob_bits = []
    backend = Aer.get_backend('qasm_simulator')  # Using the QASM simulator to simulate measurements

    for i in range(500):
        qc = encoded_qubits[i]
        base = bob_bases[i]

        if base == 'Z':
            qc.measure(0, 0)  # Measure in the Z basis (no gate needed)
        else:  # base == 'X'
            qc.h(0)  # Apply H gate to change from Z basis to X basis
            qc.measure(0, 0)

        job = execute(qc, backend, shots=1)
        result = job.result()
        counts = result.get_counts()
        measured_bit = int(list(counts.keys())[0], 2)
        bob_bits.append(measured_bit)

    # Step 6: Generating secret keys
    alice_key = [alice_bits[i] for i in range(500) if alice_bases[i] == bob_bases[i]]
    bob_key = [bob_bits[i] for i in range(500) if alice_bases[i] == bob_bases[i]]

    # Step 7: Key verification
    if alice_key == bob_key:
        pass  # Keys match (no need to print for performance testing)

    end_time = time.time()
    time_taken_ms = (end_time - start_time) * 1000
    execution_times.append(time_taken_ms)

# Calculate and print the average execution time
average_time_ms = sum(execution_times) / num_runs
print(f"Average time taken over {num_runs} runs: {average_time_ms:.2f} ms")

