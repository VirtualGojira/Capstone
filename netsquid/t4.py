import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

# Import liboqs for Kyber
import oqs

# Physical parameters
DISTANCE = 100  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000  # km/s (3e8 m/s)
FIBRE_ATTENUATION_DB_PERKM = 0.14
TIMEOUT = 10e10  # ns
MAX_RETRIES = 10

# Kyber implementation using liboqs-python
class Kyber:
    def __init__(self, algorithm="Kyber768"):
        """Initialize Kyber with specified algorithm variant.
        
        Args:
            algorithm (str): The Kyber variant to use. Options include 
                             "Kyber512", "Kyber768", "Kyber1024"
        """
        self.algorithm = algorithm
        self.private_key = None
        self.public_key = None
        self.kem = oqs.KeyEncapsulation(self.algorithm)
        
    def generate_keypair(self):
        """Generate a new Kyber keypair."""
        self.public_key = self.kem.generate_keypair()
        self.private_key = self.kem.export_secret_key()
        return self.public_key
    
    def encrypt(self, plaintext, public_key=None):
        """Encrypt plaintext using Kyber.
        
        Since Kyber is a KEM not an encryption scheme, we use it to encapsulate
        a symmetric key, which is then used with AES to encrypt the plaintext.
        
        Args:
            plaintext (bytes): The plaintext to encrypt
            public_key (bytes, optional): The recipient's public key
        
        Returns:
            tuple: (ciphertext, encapsulated_key)
        """
        if public_key is None:
            public_key = self.public_key
            
        # Create a temporary KEM for encryption
        temp_kem = oqs.KeyEncapsulation(self.algorithm)
        
        # Encapsulate a shared secret
        ciphertext, shared_secret = temp_kem.encap_secret(public_key)
        
        # Use the shared secret for symmetric encryption (simple XOR for demo)
        # In practice, use a proper symmetric cipher like AES
        key_bytes = shared_secret
        result = bytearray()
        for i, b in enumerate(plaintext):
            result.append(b ^ key_bytes[i % len(key_bytes)])
            
        return bytes(result), ciphertext
    
    def decrypt(self, ciphertext, encapsulated_key, private_key=None):
        """Decrypt ciphertext using Kyber.
        
        Args:
            ciphertext (bytes): The ciphertext to decrypt
            encapsulated_key (bytes): The encapsulated key from encryption
            private_key (bytes, optional): The private key
            
        Returns:
            bytes: The decrypted plaintext
        """
        if private_key is None:
            private_key = self.private_key
            
        # Create a new KEM instance for decryption
        decrypt_kem = oqs.KeyEncapsulation(self.algorithm)
        
        # Reconstruct key pair
        # Note: In liboqs, we need to create a new KEM with the keypair
        # Since there's no direct way to import just the secret key
        # For a real implementation, you'd need to store and transfer both keys
        
        # Decapsulate the shared secret
        # We use the original kem that has the key pair
        shared_secret = self.kem.decap_secret(encapsulated_key)
        
        # Use the shared secret for symmetric decryption (simple XOR for demo)
        key_bytes = shared_secret
        result = bytearray()
        for i, b in enumerate(ciphertext):
            result.append(b ^ key_bytes[i % len(key_bytes)])
            
        return bytes(result)

def bases_to_bytes(bases):
    return bytes([int(''.join(['1' if b == 'X' else '0' for b in bases[i:i+8]]).ljust(8, '0')[:8], 2) 
               for i in range(0, len(bases), 8)])

def bytes_to_bases(byte_stream, num_bits):
    return ['X' if (byte >> (7 - i)) & 1 else 'Z' 
           for byte in byte_stream for i in range(8)][:num_bits]

def create_network():
    network = Network("Underwater BB84-KEM Network")
    
    # Create nodes with complete port configuration
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    alice.add_ports(["qout", "cout", "cin"])
    bob.add_ports(["qin", "cin", "cout"])
    
    # Convert distance to kilometers
    distance_km = DISTANCE / 1000
    
    # Quantum channel configuration
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_delay_model = FibreDelayModel(length=distance_km, 
                                   c=SPEED_LIGHT_VACUUM, 
                                   ref_index=FIBRE_REFRACTIVE_INDEX)
    q_channel.models["delay_model"] = q_delay_model
    
    # Quantum loss model (3.2% loss per km converted to probability)
    loss_prob = 1 - 10 ** (-FIBRE_ATTENUATION_DB_PERKM / 10)
    q_channel.models["quantum_loss_model"] = FibreLossModel(p_loss_init=0, 
                                                          p_loss_length=loss_prob)

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
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.bob_public_key = bob_public_key
        self.kem = Kyber()
        self.max_retries = max_retries
        self.current_idx = 0

    def run(self):
        # Send encrypted bases
        bases_bytes = bases_to_bytes(self.bases)
        encrypted_bases, encap_key = self.kem.encrypt(bases_bytes, self.bob_public_key)
        # Send as two separate messages to avoid unpacking issues
        self.node.ports["cout"].tx_output(Message(encrypted_bases))
        self.node.ports["cout"].tx_output(Message(encap_key))
        
        # Send qubits with sequence numbers
        while self.current_idx < self.num_bits:
            attempts = 0
            acked = False
            while attempts < self.max_retries and not acked:
                # Send sequence number
                self.node.ports["cout"].tx_output(Message([self.current_idx]))
                
                # Send qubit
                qubit = qapi.create_qubits(1)
                if self.bits[self.current_idx] == 1:
                    qapi.operate(qubit, ns.X)
                if self.bases[self.current_idx] == 'X':
                    qapi.operate(qubit, ns.H)
                self.node.ports["qout"].tx_output(Message(qubit))
                
                # Wait for ACK
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
    def __init__(self, node, num_bits, bob_private_key, bob_kem):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bob_private_key = bob_private_key
        self.measurements = []
        self.kem = bob_kem  # Pass the initialized KEM object that has the keypair
        self.alice_bases = None
        self.expected_idx = 0

    def run(self):
        # Receive encrypted bases
        yield self.await_port_input(self.node.ports["cin"])
        encrypted_msg = self.node.ports["cin"].rx_input()
        encrypted_bases = encrypted_msg.items[0]
        
        # Receive encapsulated key
        yield self.await_port_input(self.node.ports["cin"])
        encap_msg = self.node.ports["cin"].rx_input()
        encap_key = encap_msg.items[0]
        
        # Decrypt the bases information
        bases_bytes = self.kem.decrypt(encrypted_bases, encap_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        
        # Receive qubits with sequence numbers
        while self.expected_idx < self.num_bits:
            # Get sequence number
            yield self.await_port_input(self.node.ports["cin"])
            idx_msg = self.node.ports["cin"].rx_input()
            seq_num = idx_msg.items[0]
            
            # Receive qubit
            yield self.await_port_input(self.node.ports["qin"])
            qubit_msg = self.node.ports["qin"].rx_input()
            qubit = qubit_msg.items[0]
            
            # Process if correct sequence number
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
    
    # Setup Kyber KEM with proper keypair generation
    bob_kem = Kyber()
    bob_public_key = bob_kem.generate_keypair()
    bob_private_key = bob_kem.private_key
    
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits, bob_public_key)
    bob_protocol = BobProtocol(bob, num_bits, bob_private_key, bob_kem)
    
    alice_protocol.start()
    bob_protocol.start()

    stat = ns.sim_run(end_time=10e100)
    print(stat)
    
    # Verify results
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
        count = 0  # Reset count for each batch
        for i in range(trails):
            if run_bb84_kem(20):
                count += 1
        arr.append(f"{count} in {big_trails}")
    print(arr)


run_bb84_kem(20)
#survey()