import numpy as np

def create_quantum_state():
    # Create a random bit (0 or 1)
    return np.random.randint(0, 2)

def measure_in_basis(state, basis):
    if basis == 'X':  # Measure in X basis
        return state
    elif basis == 'Z':  # Measure in Z basis
        return 1 - state

def e91_protocol(num_bits):
    alice_states = [create_quantum_state() for _ in range(num_bits)]
    alice_bases = [np.random.choice(['X', 'Z']) for _ in range(num_bits)]
    bob_bases = [np.random.choice(['X', 'Z']) for _ in range(num_bits)]
    bob_measurements = [measure_in_basis(state, basis) for state, basis in zip(alice_states, bob_bases)]

    return alice_states, alice_bases, bob_bases, bob_measurements

# Example usage
num_bits = 10
alice_states, alice_bases, bob_bases, bob_measurements = e91_protocol(num_bits)

print("Alice's states: ", alice_states)
print("Alice's bases: ", alice_bases)
print("Bob's bases: ", bob_bases)
print("Bob's measurements: ", bob_measurements)
