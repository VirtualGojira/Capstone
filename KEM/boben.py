import socket
import oqs
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def key_encapsulation_kyber(alice_public_key):
    algo = "Kyber512"
    bob_kyber = oqs.KeyEncapsulation(algo)
    shared_key_bob, ciphertext = bob_kyber.encap_secret(alice_public_key)
    return shared_key_bob, ciphertext

def frodo_decrypt(ciphertext, aes_key, nonce, tag):
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_message

def bob_client():
    # Set up the client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))

    # Step 1: Receive Alice's Kyber public key
    alice_public_key = client_socket.recv(1024)
    print(f"Received Alice's Kyber public key: {alice_public_key.hex()}")

    # Step 2: Encapsulate and send the Kyber ciphertext
    shared_key_bob, ciphertext = key_encapsulation_kyber(alice_public_key)
    print(f"Bob's shared key from Kyber: {shared_key_bob.hex()}")
    
    client_socket.sendall(ciphertext)
    print(f"Sent Kyber ciphertext to Alice: {ciphertext.hex()}")

    # Step 3: Receive the encrypted message from Alice
    encrypted_message = client_socket.recv(1024 + 12 + 16)
    ciphertext = encrypted_message[:len(encrypted_message) - 28]
    nonce = encrypted_message[-28:-16]
    tag = encrypted_message[-16:]

    # Step 4: Decrypt the message with the Kyber shared key
    aes_key = shared_key_bob[:16]  # Use part of the Kyber key as AES key
    decrypted_message = frodo_decrypt(ciphertext, aes_key, nonce, tag)
    print(f"Decrypted message from Alice: {decrypted_message.decode()}")

    client_socket.close()

if __name__ == "__main__":
    bob_client()
