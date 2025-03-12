import random
import oqs

# Simulate E91 protocol
def create_entangled_pair():
    return (random.choice([0, 1]), random.choice([0, 1]))

def measure_in_basis(qubit, basis):
    if basis == 'X':
        qubit = qubit ^ random.choice([0, 1])
    elif basis == 'Y':
        qubit = qubit ^ random.choice([0, 1])
    return qubit

def e91_protocol():
    entangled_pair = create_entangled_pair()
    alice_qubit, bob_qubit = entangled_pair

    alice_basis = random.choice(['Z', 'X', 'Y'])
    bob_basis = random.choice(['Z', 'X', 'Y'])

    alice_result = measure_in_basis(alice_qubit, alice_basis)
    bob_result = measure_in_basis(bob_qubit, bob_basis)

    if alice_basis == bob_basis:
        shared_key = alice_result
    else:
        shared_key = None

    return alice_basis, bob_basis, alice_result, bob_result, shared_key

def send_key_e91(ciphertext):
    sent_bits = []
    received_bits = []
    
    for bit in ciphertext:
        alice_basis, bob_basis, alice_result, bob_result, shared_key = e91_protocol()
        if shared_key is not None:
            sent_bits.append(bit)
            received_bits.append(bit if alice_result == bob_result else None)
    
    received_bits = [bit for bit in received_bits if bit is not None]
    
    return sent_bits, received_bits

def key_encapsulation():
    algo = "Kyber512"
    alice = oqs.KeyEncapsulation(algo)
    alice_public_key = alice.generate_keypair()
    bob = oqs.KeyEncapsulation(algo)
    ciphertext, shared_key_bob = bob.encap_secret(alice_public_key)
    return alice, bob, ciphertext, shared_key_bob

def key_decapsulation(alice, received_ciphertext):
    shared_key_alice = alice.decap_secret(received_ciphertext)
    return shared_key_alice

def reconcile_keys(sent_bits, received_bits):
    # Simple error correction: parity check
    if len(received_bits) < len(sent_bits):
        extra_bits = len(sent_bits) - len(received_bits)
        received_bits.extend([0] * extra_bits)
    elif len(received_bits) > len(sent_bits):
        received_bits = received_bits[:len(sent_bits)]
    
    reconciled_bits = []
    for s_bit, r_bit in zip(sent_bits, received_bits):
        if s_bit == r_bit:
            reconciled_bits.append(s_bit)
        else:
            reconciled_bits.append(0)  # Correct the bit (simple example)
    
    return bytes(reconciled_bits)

def main():
    alice, bob, ciphertext, shared_key_bob = key_encapsulation()
    print(f"Original ciphertext: {ciphertext}")

    sent_bits, received_bits = send_key_e91(ciphertext)
    print(f"Sent bits: {sent_bits}")
    print(f"Received bits: {received_bits}")

    reconciled_bits = reconcile_keys(sent_bits, received_bits)
    received_ciphertext = bytes(reconciled_bits)
    print(f"Reconciled ciphertext: {received_ciphertext}")

    shared_key_alice = key_decapsulation(alice, received_ciphertext)
    print(f"Alice's shared key: {shared_key_alice}")
    print(f"Bob's shared key: {shared_key_bob}")
    print("Shared keys match:", shared_key_alice == shared_key_bob)

if __name__ == "__main__":
    main()
