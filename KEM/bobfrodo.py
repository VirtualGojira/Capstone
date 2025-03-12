import socket
import oqs

def key_encapsulation_with_alice_public_key(alice_public_key):
    algo = "Kyber512"  ####
    bob = oqs.KeyEncapsulation(algo)
    ciphertext, shared_key_bob = bob.encap_secret(alice_public_key)
    return ciphertext, shared_key_bob

def bob_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))

    # Receive Alice's public key
    alice_public_key = client_socket.recv(1024)

    # Use Alice's public key to generate a shared key and ciphertext
    ciphertext, shared_key_bob = key_encapsulation_with_alice_public_key(alice_public_key)
    print(f"Bob's shared key: {shared_key_bob.hex()}")

    # Send the ciphertext to Alice
    client_socket.sendall(ciphertext)
    client_socket.close()

if __name__ == "__main__":
    bob_client()
