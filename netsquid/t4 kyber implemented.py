import netsquid as ns
import numpy as np
from oqs import KeyEncapsulation
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

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
    network = Network("BB84-Kyber Network")
    
    alice = Node("Alice", qmemory=ns.components.QuantumMemory("AliceMemory", 1))
    bob = Node("Bob", qmemory=ns.components.QuantumMemory("BobMemory", 1))
    
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    q_channel = QuantumChannel("QuantumChannel", delay=0)
    c_channel = ClassicalChannel("ClassicalChannel", delay=0)
    
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

    def run(self):
        # Kyber encapsulation
        kem = KeyEncapsulation('Kyber512')
        ciphertext, shared_secret = kem.encap_secret(self.bob_public_key)
        
        # Encrypt bases with shared secret
        basis_bytes = bases_to_bytes(self.bases)
        encrypted_bases = bytes([b ^ s for b, s in zip(basis_bytes, shared_secret)])
        
        # Send encrypted bases and ciphertext
        self.node.ports["cout"].tx_output(Message((ciphertext, encrypted_bases)))
        
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
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.measurements = []
        self.kem = KeyEncapsulation('Kyber512')
        self.public_key = self.kem.generate_keypair()
        self.private_key = self.kem.export_secret_key()

    def run(self):
        # Receive and process basis information
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        ciphertext, encrypted_bases = message.items[0]
        
        # Kyber decapsulation
        shared_secret = self.kem.decap_secret(ciphertext)
        
        # Decrypt bases
        basis_bytes = bytes([b ^ s for b, s in zip(encrypted_bases, shared_secret)])
        alice_bases = bytes_to_bases(basis_bytes, self.num_bits)
        
        # Measure qubits using Alice's bases
        for i in range(self.num_bits):
            yield self.await_port_input(self.node.ports["qin"])
            message = self.node.ports["qin"].rx_input()
            qubit = message.items[0]
            if alice_bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            result, _ = qapi.measure(qubit)
            self.measurements.append(result)

def run_bb84_kyber(num_bits):
    ns.sim_reset()
    network = create_network()
    
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    bob_protocol = BobProtocol(bob, num_bits)
    alice_protocol = AliceProtocol(alice, num_bits, bob_protocol.public_key)
    
    alice_protocol.start()
    bob_protocol.start()
    
    stats = ns.sim_run()
    print(stats)
    
    # Verify results
    print("Alice's bits:", alice_protocol.bits.tolist())
    print("Bob's measurements:", bob_protocol.measurements)
    print("Key match:", alice_protocol.bits.tolist() == bob_protocol.measurements)

# Example usage
run_bb84_kyber(32)