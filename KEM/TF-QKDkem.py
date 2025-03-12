import random
import oqs

def generate_phase_randomized_state():
    return random.uniform(0, 2 * 3.14159)  # Random phase between 0 and 2π

def charlie_measurement(state1, state2):
    measurement_result = (state1 + state2) % (2 * 3.14159)  # Simplified measurement
    return measurement_result

def tf_qkd_protocol():
    # Step 1: Alice and Bob generate phase-randomized states
    alice_state = generate_phase_randomized_state()
    bob_state = generate_phase_randomized_state()

    # Step 2: They send these states to Charlie
    # Step 3: Charlie performs measurements and announces results
    charlie_result = charlie_measurement(alice_state, bob_state)
    charlie_announcement = random.choice([0, 1])  # Simplified announcement (0 or 1)

    # Step 4: Alice and Bob generate a shared key based on the announcement
    alice_key_bit = 1 if (alice_state % 2 < 1) else 0
    bob_key_bit = 1 if (bob_state % 2 < 1) else 0

    # They adjust their keys based on Charlie's announcement
    if charlie_announcement == 0:
        alice_key_bit = 1 - alice_key_bit
        bob_key_bit = 1 - bob_key_bit

    return alice_key_bit, bob_key_bit

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

def send_key_tf_qkd(ciphertext):
    sent_bits = []
    received_bits = []
    
    for bit in ciphertext:
        alice_key_bit, bob_key_bit = tf_qkd_protocol()
        sent_bits.append(bit)
        received_bits.append(bit if alice_key_bit == bob_key_bit else None)
    
    received_bits = [bit for bit in received_bits if bit is not None]
    
    return sent_bits, received_bits

def main():
    alice, bob, ciphertext, shared_key_bob = key_encapsulation()
    print(f"Original ciphertext: {ciphertext}")

    sent_bits, received_bits = send_key_tf_qkd(ciphertext)
    print(f"Sent bits: {sent_bits}")
    print(f"Received bits: {received_bits}")

    received_ciphertext = bytes(received_bits)
    print(f"Received ciphertext: {received_ciphertext}")

    if len(received_ciphertext) == len(ciphertext):
        shared_key_alice = key_decapsulation(alice, received_ciphertext)
        print(f"Alice's shared key: {shared_key_alice}")
        print(f"Bob's shared key: {shared_key_bob}")
        print("Shared keys match:", shared_key_alice == shared_key_bob)
    else:
        print("Failed to receive full ciphertext. Retry needed.")

if __name__ == "__main__":
    main()
