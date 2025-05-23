import socket
import oqs

def key_encapsulation():
    algo = "sntrup761"  ####
    alice = oqs.KeyEncapsulation(algo)
    alice_public_key = alice.generate_keypair()
    return alice, alice_public_key

def key_decapsulation(alice, received_ciphertext):
    shared_key_alice = alice.decap_secret(received_ciphertext)
    return shared_key_alice

def alice_server():
    alice, alice_public_key = key_encapsulation()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen()

    print("Server listening on port 65432...")
    conn, addr = server_socket.accept()
    with conn:
        print(f"Connected by {addr}")
        # Send Alice's public key to Bob
        conn.sendall(alice_public_key)
        # Receive the ciphertext from Bob
        received_ciphertext = conn.recv(1152)

        # Decapsulate the ciphertext to get the shared key
        shared_key_alice = key_decapsulation(alice, received_ciphertext)
        print(f"Alice's shared key: {shared_key_alice.hex()}")

if __name__ == "__main__":
    alice_server()
