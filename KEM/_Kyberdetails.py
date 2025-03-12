import oqs

# Initialize Kyber512 Key Encapsulation Mechanism (KEM)
kem = oqs.KeyEncapsulation("Kyber512")

# Generate key pair (Public Key & Secret Key)
public_key = kem.generate_keypair()
secret_key = kem.export_secret_key()

# Encapsulate: Generate Ciphertext & Shared Secret for encryption
ciphertext, shared_secret_enc = kem.encap_secret(public_key)

# Decapsulate: Recover Shared Secret from Ciphertext
shared_secret_dec = kem.decap_secret(ciphertext)

# Verify if shared secrets match
key_exchange_status = "Key Exchange Successful" if shared_secret_enc == shared_secret_dec else "Key Exchange Failed"

# Write output to a text file
with open("_kyber512_output.txt", "w") as file:
    file.write("=== Kyber512 Key Encapsulation ===\n")
    file.write(f"Public Key (PK): {public_key.hex()}\n")
    file.write(f"Secret Key (SK): {secret_key.hex()}\n")
    file.write(f"Ciphertext (CT): {ciphertext.hex()}\n")
    file.write(f"Shared Secret (Alice): {shared_secret_enc.hex()}\n")
    file.write(f"Shared Secret (Bob): {shared_secret_dec.hex()}\n")
    file.write(f"Status: {key_exchange_status}\n")

# Free resources
kem.free()
