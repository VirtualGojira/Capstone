import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models.delaymodels import FixedDelayModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

SPEED_OF_LIGHT_WATER = 2e8  # m/s (approx 2/3 of vacuum speed)
QUANTUM_DISTANCE = 100e3  # 100 km
CLASSICAL_DISTANCE = 100e3  # 100 km

# Mock KEM implementation for demonstration
class MockKyber:
    def __init__(self):
        self.private_key = "dummy_private_key"
        self.public_key = "dummy_public_key"
    
    def encrypt(self, plaintext, public_key):
        return plaintext  # Simulated encryption
    
    def decrypt(self, ciphertext, private_key):
        return ciphertext  # Simulated decryption

# Helper functions for basis conversion
def bases_to_bytes(bases):
    bits = [0 if b == 'Z' else 1 for b in bases]
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte |= bits[i + j] << (7 - j)
        byte_array.append(byte)
    return bytes(byte_array)

def bytes_to_bases(byte_stream, num_bits):
    bits = []
    for byte in byte_stream:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
            if len(bits) == num_bits:
                break
        if len(bits) == num_bits:
            break
    return ['Z' if bit == 0 else 'X' for bit in bits]

def create_network():
    network = Network("Underwater BB84-KEM Network")
    
    # Calculate propagation delays
    quantum_delay = QUANTUM_DISTANCE / SPEED_OF_LIGHT_WATER
    classical_delay = CLASSICAL_DISTANCE / SPEED_OF_LIGHT_WATER
    
    # Create nodes with quantum memories
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    # Add ports for communication
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    # Create underwater channels with realistic delays
    q_channel = QuantumChannel(
        name="QuantumChannel",
        delay=quantum_delay,
        models={"delay_model": FixedDelayModel(delay=quantum_delay)}
    )
    
    c_channel = ClassicalChannel(
        name="ClassicalChannel",
        delay=classical_delay,
        models={"delay_model": FixedDelayModel(delay=classical_delay)}
    )
    
    # Connect ports
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    alice.ports["cout"].connect(c_channel.ports["send"])
    bob.ports["cin"].connect(c_channel.ports["recv"])
    
    network.add_nodes([alice, bob])
    return network

class AliceProtocol(Protocol):
    def __init__(self, node, num_bits, bob_public_key):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bits = np.random.randint(2, size=num_bits)
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.bob_public_key = bob_public_key
        self.kem = MockKyber()

    def run(self):
        # Convert bases to bytes and encrypt
        bases_bytes = bases_to_bytes(self.bases)
        ciphertext = self.kem.encrypt(bases_bytes, self.bob_public_key)
        self.node.ports["cout"].tx_output(Message(ciphertext))
        
        # Send encoded qubits
        for i in range(self.num_bits):
            qubit = qapi.create_qubits(1)
            if self.bits[i] == 1:
                qapi.operate(qubit, ns.X)
            if self.bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            self.node.ports["qout"].tx_output(Message(qubit))
            yield self.await_timer(1)

class BobProtocol(Protocol):
    def __init__(self, node, num_bits, bob_private_key):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bob_private_key = bob_private_key
        self.measurements = []
        self.kem = MockKyber()
        self.alice_bases = None

    def run(self):
        # Receive and decrypt bases
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        bases_bytes = self.kem.decrypt(message.items[0], self.bob_private_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        
        # Measure qubits using Alice's bases
        while len(self.measurements) < self.num_bits:
            yield self.await_port_input(self.node.ports["qin"])
            message = self.node.ports["qin"].rx_input()
            if message is None:
                continue
            qubit = message.items[0]
            if self.alice_bases[len(self.measurements)] == 'X':
                qapi.operate(qubit, ns.H)
            result, _ = qapi.measure(qubit)
            self.measurements.append(result)

def run_bb84_kem(num_bits):
    ns.sim_reset()
    network = create_network()

    # Display channel parameters
    print(f"Underwater Channel Parameters:")
    print(f"Quantum Fiber: {QUANTUM_DISTANCE/1e3} km, Delay: {QUANTUM_DISTANCE/SPEED_OF_LIGHT_WATER*1e3:.2f} ms")
    print(f"Classical Fiber: {CLASSICAL_DISTANCE/1e3} km, Delay: {CLASSICAL_DISTANCE/SPEED_OF_LIGHT_WATER*1e3:.2f} ms")

    # Generate KEM keys
    kem = MockKyber()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits, kem.public_key)
    bob_protocol = BobProtocol(bob, num_bits, kem.private_key)
    
    alice_protocol.start()
    bob_protocol.start()

    # Calculate required simulation time (qubits + classical exchange)
    total_delay = (QUANTUM_DISTANCE/SPEED_OF_LIGHT_WATER) * 1e9  # Convert to ns
    simulation_time = num_bits * total_delay + 1e6  # Add buffer
    
    stats = ns.sim_run(end_time=simulation_time)
    print(stats)
    
    # Verify results
    print("Alice's bits:", alice_protocol.bits.tolist())
    print("Bob's measurements:", bob_protocol.measurements)
    print("Key match:", alice_protocol.bits.tolist() == bob_protocol.measurements)
    print("Key Length:", len(bob_protocol.measurements))

run_bb84_kem(20)