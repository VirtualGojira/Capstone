import oqs

# Define the Kyber algorithm
algo = "Kyber512"

# Generate key pair for Alice
alice = oqs.KeyEncapsulation(algo)
alice_public_key = alice.generate_keypair()

# Bob generates a shared key and ciphertext using Alice's public key
bob = oqs.KeyEncapsulation(algo)
ciphertext, shared_key_bob = bob.encap_secret(alice_public_key)

# Alice decapsulates the ciphertext to get the shared key
shared_key_alice = alice.decap_secret(ciphertext)

# Verify if the shared keys are identical
print(f"Alice's shared key: {shared_key_alice.hex()}")
print(f"Bob's shared key: {shared_key_bob.hex()}")
print("Shared keys match:", shared_key_alice == shared_key_bob)
