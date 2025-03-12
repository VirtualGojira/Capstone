import oqs

# Select the Kyber algorithm
kem = oqs.KeyEncapsulation("Kyber512")

# Generate key pair
public_key = kem.generate_keypair()
private_key = kem.export_secret_key()

print("Public Key:", public_key)
print()
print("Private Key:", private_key)
