import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi
import oqs
import warnings
import random

# Suppress all warnings
warnings.filterwarnings('ignore')

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

# Physical parameters
DISTANCE = 100  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000  # km/s (3e8 m/s)
FIBRE_ATTENUATION_DB_PERKM = 0.14
TIMEOUT = 10e10  # ns
MAX_RETRIES = 10

class Kyber:
    def __init__(self, algorithm="Kyber768"):
        """Initialize Kyber with a persistent KEM instance."""
        self.algorithm = algorithm
        self.kem = oqs.KeyEncapsulation(self.algorithm)
        self.public_key = None
        self.private_key = None

    def generate_keypair(self):
        """Generate a key pair and store both public and private keys."""
        self.public_key = self.kem.generate_keypair()
        self.private_key = self.kem.export_secret_key()
        return self.public_key

    def encapsulate(self, public_key):
        """Encapsulate a shared secret using the provided public key."""
        ciphertext, shared_secret = self.kem.encap_secret(public_key)
        return ciphertext, shared_secret

    def decapsulate(self, ciphertext):
        """Decapsulate to recover the shared secret using the stored private key."""
        shared_secret = self.kem.decap_secret(ciphertext)
        return shared_secret

    def encrypt(self, plaintext, public_key):
        """Encrypt plaintext using the encapsulated shared secret.
        
        For demonstration, we use a simple XOR of the plaintext with the shared secret.
        """
        ciphertext, shared_secret = self.encapsulate(public_key)
        key_bytes = shared_secret
        encrypted = bytearray()
        for i, byte in enumerate(plaintext):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return bytes(encrypted), ciphertext

    def decrypt(self, ciphertext, encapsulated_key):
        """Decrypt ciphertext using the recovered shared secret from decapsulation."""
        shared_secret = self.decapsulate(encapsulated_key)
        key_bytes = shared_secret
        decrypted = bytearray()
        for i, byte in enumerate(ciphertext):
            decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return bytes(decrypted)

def bases_to_bytes(bases):
    """Convert a list of bases ('X' or 'Z') to bytes."""
    bit_string = ''.join('0' if base == 'X' else '1' for base in bases)
    # Pad bit_string to a multiple of 8 bits.
    bit_string = bit_string.ljust((len(bit_string) + 7) // 8 * 8, '0')
    return bytes(int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8))

def bytes_to_bases(byte_data, length):
    """Convert bytes back to a list of bases ('X' or 'Z')."""
    bit_string = ''.join(f"{byte:08b}" for byte in byte_data)[:length]
    return ['X' if bit == '0' else 'Z' for bit in bit_string]

def create_network():
    network = Network("Underwater BB84-KEM Network")
    
    # Create nodes with complete port configuration
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    alice.add_ports(["qout", "cout", "cin"])
    bob.add_ports(["qin", "cin", "cout"])
    
    # Quantum channel configuration
    distance_km = DISTANCE / 1000
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_channel.models["delay_model"] = FibreDelayModel(length=distance_km, 
                                                      c=SPEED_LIGHT_VACUUM, 
                                                      ref_index=FIBRE_REFRACTIVE_INDEX)
    loss_prob = 1 - 10 ** (-FIBRE_ATTENUATION_DB_PERKM / 10)
    q_channel.models["quantum_loss_model"] = FibreLossModel(p_loss_init=0, p_loss_length=loss_prob)

    # Classical channels (bidirectional)
    c_channel_ab = ClassicalChannel(name="Classical_AB", length=DISTANCE)
    c_channel_ba = ClassicalChannel(name="Classical_BA", length=DISTANCE)
    
    # Connect ports
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    alice.ports["cout"].connect(c_channel_ab.ports["send"])
    bob.ports["cin"].connect(c_channel_ab.ports["recv"])
    bob.ports["cout"].connect(c_channel_ba.ports["send"])
    alice.ports["cin"].connect(c_channel_ba.ports["recv"])

    network.add_nodes([alice, bob])
    return network

class AliceProtocol(Protocol):
    def __init__(self, node, num_bits, bob_public_key, max_retries=MAX_RETRIES):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bits = np.random.randint(2, size=num_bits)
        self.bases = [random.choice(['Z', 'X']) for _ in range(num_bits)]
        self.bob_public_key = bob_public_key
        # Alice uses her own ephemeral instance for encapsulation.
        self.max_retries = max_retries
        self.current_idx = 0

    def run(self):
        # Convert bases to bytes and encrypt them using an ephemeral Kyber instance.
        bases_bytes = bases_to_bytes(self.bases)
        temp_kem = Kyber()  # Ephemeral instance for encapsulation.
        encrypted_bases, encap_key = temp_kem.encrypt(bases_bytes, self.bob_public_key)
        # Send the encrypted bases and encapsulated key as two separate messages.
        self.node.ports["cout"].tx_output(Message(encrypted_bases))
        self.node.ports["cout"].tx_output(Message(encap_key))
        print(f"Alice bases: {self.bases}")
        print(f"Alice encrypted bases: {encrypted_bases}")
        
        # Send qubits with sequence numbers.
        while self.current_idx < self.num_bits:
            attempts = 0
            acked = False
            while attempts < self.max_retries and not acked:
                self.node.ports["cout"].tx_output(Message([self.current_idx]))
                qubit = qapi.create_qubits(1)
                if self.bits[self.current_idx] == 1:
                    qapi.operate(qubit, ns.X)
                if self.bases[self.current_idx] == 'X':
                    qapi.operate(qubit, ns.H)
                self.node.ports["qout"].tx_output(Message(qubit))
                expr = yield self.await_port_input(self.node.ports["cin"]) | self.await_timer(TIMEOUT)
                if expr.first_term.value:
                    msg = self.node.ports["cin"].rx_input()
                    if msg and msg.items[0] == self.current_idx:
                        acked = True
                attempts += 1
            
            if acked:
                self.current_idx += 1
            else:
                print(f"Failed to send qubit {self.current_idx} after {self.max_retries} attempts")
                break

class BobProtocol(Protocol):
    def __init__(self, node, num_bits, kem_instance):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.measurements = []
        # Bob uses his persistent Kyber instance with his key pair.
        self.kem = kem_instance
        self.alice_bases = None
        self.expected_idx = 0

    def run(self):
        # Receive the encrypted bases.
        yield self.await_port_input(self.node.ports["cin"])
        encrypted_msg = self.node.ports["cin"].rx_input()
        encrypted_bases = encrypted_msg.items[0]
        print(f"Bob received encrypted bases: {encrypted_bases}")
        
        yield self.await_port_input(self.node.ports["cin"])
        encap_msg = self.node.ports["cin"].rx_input()
        encap_key = encap_msg.items[0]
        
        # Decrypt the bases information using Bob's Kyber instance.
        bases_bytes = self.kem.decrypt(encrypted_bases, encap_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        print(f"Bob recovered Alice bases: {self.alice_bases}")
        
        # Receive qubits with sequence numbers.
        while self.expected_idx < self.num_bits:
            yield self.await_port_input(self.node.ports["cin"])
            idx_msg = self.node.ports["cin"].rx_input()
            seq_num = idx_msg.items[0]
            yield self.await_port_input(self.node.ports["qin"])
            qubit_msg = self.node.ports["qin"].rx_input()
            qubit = qubit_msg.items[0]
            if seq_num == self.expected_idx:
                if self.alice_bases[self.expected_idx] == 'X':
                    qapi.operate(qubit, ns.H)
                result, _ = qapi.measure(qubit)
                self.measurements.append(result)
                self.node.ports["cout"].tx_output(Message([self.expected_idx]))
                self.expected_idx += 1

def run_bb84_kem(num_bits):
    ns.sim_reset()
    network = create_network()
    
    # Bob creates his Kyber instance and generates his key pair.
    bob_kem = Kyber()
    bob_public_key = bob_kem.generate_keypair()
    
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    # Alice uses Bob's public key for encapsulation.
    alice_protocol = AliceProtocol(alice, num_bits, bob_public_key)
    bob_protocol = BobProtocol(bob, num_bits, kem_instance=bob_kem)
    
    alice_protocol.start()
    bob_protocol.start()
    
    stat = ns.sim_run(end_time=10e100)
    print(stat)
    
    success = alice_protocol.bits.tolist() == bob_protocol.measurements
    lost_bits = len(alice_protocol.bits) - len(bob_protocol.measurements)
    print(f"\nKey match: {success}")
    print(f"Alice sent: {len(alice_protocol.bits)} bits")
    print(f"Bob received: {len(bob_protocol.measurements)} bits")
    print(f"Lost bits: {lost_bits}")
    return success

def survey():
    arr = []
    big_trails = 1
    while big_trails < 1000:
        big_trails *= 10
        trails = big_trails
        count = 0
        for i in range(trails):
            if run_bb84_kem(20):
                count += 1
        arr.append(f"{count} in {big_trails}")
    print(arr)

run_bb84_kem(24)
#survey()
