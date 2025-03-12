import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models.delaymodels import FixedDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

DISTANCE = 1  # meters
LOSS_COEFF = 0.15
SPEED_OF_LIGHT_FACTOR = 0.83

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

# Custom Quantum Channel with programmable properties
class ProgrammableFibreDelayModel(ns.components.models.DelayModel):
    """Custom delay model allowing programmable speed factor."""
    def __init__(self, speed_of_light_factor=SPEED_OF_LIGHT_FACTOR):
        super().__init__()
        self.speed_of_light_factor = speed_of_light_factor

    def generate_delay(self, length, **kwargs):
        """Compute the delay for a given length."""
        return length / (3e8 * self.speed_of_light_factor)

def create_programmable_fibre_channel(name, length, loss_coeff=LOSS_COEFF, speed_of_light_factor=SPEED_OF_LIGHT_FACTOR):
    """Creates a QuantumChannel with programmable properties."""
    delay_model = ProgrammableFibreDelayModel(speed_of_light_factor)
    loss_model = FibreLossModel(p_loss_init=loss_coeff, p_loss_length=loss_coeff)
    channel = QuantumChannel(
        name=name,
        length=length,
        models={
            "delay_model": delay_model,
            "quantum_loss_model": loss_model,
        }
    )
    channel.delay_model = delay_model
    channel.loss_model = loss_model
    return channel

def create_network():
    network = Network("BB84-KEM Network")
    
    # Create nodes with quantum memories
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    # Add ports for communication
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    # Create programmable quantum channel
    q_channel = create_programmable_fibre_channel(
        name="QuantumChannel",
        length=DISTANCE,  # Initial length in meters
        loss_coeff=LOSS_COEFF, 
        speed_of_light_factor=SPEED_OF_LIGHT_FACTOR
    )
    
    # Create classical channel
    c_channel = ClassicalChannel(
        name="ClassicalChannel",
        delay=0,  # Numerical delay value
        models={"delay_model": FixedDelayModel(delay=0)}
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
        
        # Send each qubit twice
        for i in range(self.num_bits):
            for _ in range(2):  # Send each qubit twice
                qubit = qapi.create_qubits(1)
                if self.bits[i] == 1:
                    qapi.operate(qubit, ns.X)
                if self.bases[i] == 'X':
                    qapi.operate(qubit, ns.H)
                self.node.ports["qout"].tx_output(Message(qubit))
                yield self.await_timer(10)  # Add a small delay between qubits

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
        for i in range(self.num_bits):
            received_qubits = []
            for _ in range(2):  # Receive two copies of each qubit
                yield self.await_port_input(self.node.ports["qin"])
                message = self.node.ports["qin"].rx_input()
                if message is not None:
                    received_qubits.append(message.items[0])
            
            # Use the first received qubit (if any)
            if received_qubits:
                qubit = received_qubits[0]  # Use the first copy
                if self.alice_bases[i] == 'X':
                    qapi.operate(qubit, ns.H)
                result, _ = qapi.measure(qubit)
                self.measurements.append(result)
            else:
                # If both copies are lost, skip this qubit
                self.measurements.append(None)

def run_bb84_kem(num_bits):
    ns.sim_reset()
    network = create_network()
    
    # Generate KEM keys
    kem = MockKyber()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits, kem.public_key)
    bob_protocol = BobProtocol(bob, num_bits, kem.private_key)
    
    alice_protocol.start()
    bob_protocol.start()
    
    stats = ns.sim_run()
    print(stats)
    
    # Verify results
    print("Alice's bits:", alice_protocol.bits.tolist())
    print("Bob's measurements:", bob_protocol.measurements)
    print("Key match:", alice_protocol.bits.tolist() == [m for m in bob_protocol.measurements if m is not None])
    print("Key Length:", len([m for m in bob_protocol.measurements if m is not None]))

run_bb84_kem(20)