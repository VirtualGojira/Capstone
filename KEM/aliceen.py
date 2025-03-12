import socket
import oqs
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def key_encapsulation_kyber():
    algo = "Kyber512"
    alice_kyber = oqs.KeyEncapsulation(algo)
    alice_public_key = alice_kyber.generate_keypair()
    return alice_kyber, alice_public_key

def key_decapsulation_kyber(alice_kyber, received_ciphertext):
    shared_key_alice = alice_kyber.decap_secret(received_ciphertext)
    return shared_key_alice

def frodo_encrypt(message, aes_key):
    # AES-GCM encryption with the Frodo-based key
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message) + encryptor.finalize()
    return ciphertext, nonce, encryptor.tag

def alice_server():
    # Step 1: Perform key encapsulation with Kyber
    alice_kyber, alice_public_key = key_encapsulation_kyber()
    print(f"Alice's Kyber public key: {alice_public_key.hex()}")

    # Set up the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen()

    conn, addr = server_socket.accept()
    with conn:
        print(f"Connected by {addr}")
        
        # Send Alice's Kyber public key to Bob
        conn.sendall(alice_public_key)
        
        # Receive the Kyber ciphertext from Bob
        received_ciphertext = conn.recv(1024)
        print(f"Received Kyber ciphertext: {received_ciphertext.hex()}")

        # Step 2: Decapsulate to obtain the shared Kyber key
        shared_key_alice = key_decapsulation_kyber(alice_kyber, received_ciphertext)
        print(f"Alice's shared key from Kyber: {shared_key_alice.hex()}")

        # Step 3: Use the Kyber shared key to encrypt a message with FrodoKEM
        message = b"Hello, this is a secure message!"
        aes_key = shared_key_alice[:16]  # Use part of the Kyber key as AES key

        ciphertext, nonce, tag = frodo_encrypt(message, aes_key)

        # Send encrypted message, nonce, and tag to Bob
        conn.sendall(ciphertext + nonce + tag)
        print("Message encrypted and sent to Bob.")

if __name__ == "__main__":
    alice_server()
