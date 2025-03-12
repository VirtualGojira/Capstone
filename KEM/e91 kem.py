import random
import oqs

# Function to simulate E91 protocol
def create_entangled_pair():
    # Simulate the creation of an entangled pair
    return (random.choice([0, 1]), random.choice([0, 1]))

def measure_in_basis(qubit, basis):
    # Simulate measurement in the chosen basis
    if basis == 'X':
        qubit = qubit ^ random.choice([0, 1])
    elif basis == 'Y':
        qubit = qubit ^ random.choice([0, 1])
    return qubit

def e91_protocol():
    # Create entangled pairs
    entangled_pair = create_entangled_pair()
    alice_qubit, bob_qubit = entangled_pair

    # Randomly choose bases for Alice and Bob
    alice_basis = random.choice(['Z', 'X', 'Y'])
    bob_basis = random.choice(['Z', 'X', 'Y'])

    # Measure qubits in chosen bases
    alice_result = measure_in_basis(alice_qubit, alice_basis)
    bob_result = measure_in_basis(bob_qubit, bob_basis)

    # Check if bases matched and use results for key generation
    if alice_basis == bob_basis:
        shared_key = alice_result
    else:
        shared_key = None  # Discard if bases didn't match

    return alice_basis, bob_basis, alice_result, bob_result, shared_key

# Function to send encapsulated key bit by bit using E91
def send_key_e91(ciphertext):
    sent_bits = []
    received_bits = []
    
    for bit in ciphertext:
        alice_basis, bob_basis, alice_result, bob_result, shared_key = e91_protocol()
        if shared_key is not None:
            sent_bits.append(bit)
            received_bits.append(bit if alice_result == bob_result else None)
    
    # Filter out None values where bases didn't match
    received_bits = [bit for bit in received_bits if bit is not None]
    
    return sent_bits, received_bits

# Kyber KEM part
def key_encapsulation():
    # Initialize the Kyber algorithm
    algo = "Kyber512"

    # Generate key pair for Alice
    alice = oqs.KeyEncapsulation(algo)
    alice_public_key = alice.generate_keypair()

    # Bob generates a shared key and ciphertext using Alice's public key
    bob = oqs.KeyEncapsulation(algo)
    ciphertext, shared_key_bob = bob.encap_secret(alice_public_key)

    return alice, bob, ciphertext, shared_key_bob

def key_decapsulation(alice, bob, received_ciphertext):
    # Alice decapsulates the ciphertext to get the shared key
    shared_key_alice = alice.decap_secret(received_ciphertext)
    
    return shared_key_alice

# Main function
def main():
    # Generate and encapsulate key using Kyber KEM
    alice, bob, ciphertext, shared_key_bob = key_encapsulation()
    print(f"Original ciphertext: {ciphertext}")

    # Simulate sending the encapsulated key bit by bit using E91
    sent_bits, received_bits = send_key_e91(ciphertext)
    received_ciphertext = bytes(received_bits)
    print(f"Received ciphertext: {received_ciphertext}")

    # Bob decapsulates the received ciphertext to get the shared key
    shared_key_alice = key_decapsulation(alice, bob, received_ciphertext)

    # Assert that the keys are equal
    print(f"Alice's shared key: {shared_key_alice}")
    print(f"Bob's shared key: {shared_key_bob}")
    print("Shared keys match:", shared_key_alice == shared_key_bob)

# Run the main function
if __name__ == "__main__":
    main()
