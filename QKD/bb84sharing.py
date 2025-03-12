import subprocess
import time

def run_alice_server():
    print("Starting Alice (Server)...")
    server_process = subprocess.Popen(["python", "bb84alice.py"])
    # Give the server some time to start
    time.sleep(2)
    return server_process

def run_bob_client():
    print("Starting Bob (Client)...")
    client_process = subprocess.run(["python", "bb84bob.py"])
    return client_process

# Run the Alice server
server_process = run_alice_server()
# Run the Bob client
run_bob_client()
# Wait for the server process to complete
server_process.terminate()
server_process.wait()
print("Alice (Server) terminated.")