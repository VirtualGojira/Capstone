import subprocess
import time
start_time = time.time()

def run_alice_server():
    print("Starting Alice (Server)...")
    server_process = subprocess.Popen(["python", "alicekem.py"])
    # Give the server some time to start
    time.sleep(2)
    return server_process

def run_bob_client():
    print("Starting Bob (Client)...")
    client_process = subprocess.run(["python", "bobkem.py"])
    return client_process

# Run the Alice server
server_process = run_alice_server()
# Run the Bob client
run_bob_client()
# Wait for the server process to complete
server_process.terminate()
server_process.wait()
print("Alice (Server) terminated.")

end_time = time.time()
time_taken_ms = (end_time - start_time) * 1000
print(f"Time taken: {time_taken_ms} ms")