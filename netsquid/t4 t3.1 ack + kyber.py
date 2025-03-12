import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi
from oqs import KeyEncapsulation

# Physical parameters
DISTANCE = 100  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000  # km/s (3e8 m/s)
FIBRE_ATTENUATION_DB_PERKM = 0.14
TIMEOUT = 10e10  # ns
MAX_RETRIES = 10

def bases_to_bytes(bases):
    return bytes([int(''.join(['1' if b == 'X' else '0' for b in bases[i:i+8]]).ljust(8, '0')[:8], 2) 
               for i in range(0, len(bases), 8)])

def bytes_to_bases(byte_stream, num_bits):
    return ['X' if (byte >> (7 - i)) & 1 else 'Z' 
           for byte in byte_stream for i in range(8)][:num_bits]

def create_network():
    network = Network("Underwater BB84-KEM Network")
    
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    alice.add_ports(["qout", "cout", "cin"])
    bob.add_ports(["qin", "cin", "cout"])
    
    distance_km = DISTANCE / 1000
    
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_delay_model = FibreDelayModel(length=distance_km, 
                                   c=SPEED_LIGHT_VACUUM, 
                                   ref_index=FIBRE_REFRACTIVE_INDEX)
    q_channel.models["delay_model"] = q_delay_model
    
    loss_prob = 1 - 10 ** (-FIBRE_ATTENUATION_DB_PERKM / 10)
    q_channel.models["quantum_loss_model"] = FibreLossModel(p_loss_init=0, 
                                                          p_loss_length=loss_prob)

    c_channel_ab = ClassicalChannel(name="Classical_AB", length=DISTANCE)
    c_channel_ba = ClassicalChannel(name="Classical_BA", length=DISTANCE)
    
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    
    alice.ports["cout"].connect(c_channel_ab.ports["send"])
    bob.ports["cin"].connect(c_channel_ab.ports["recv"])
    
    bob.ports["cout"].connect(c_channel_ba.ports["send"])
    alice.ports["cin"].connect(c_channel_ba.ports["recv"])

    network.add_nodes([alice, bob])
    return network

class AliceProtocol(Protocol):
    def __init__(self, node, num_bits, max_retries=MAX_RETRIES):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bits = np.random.randint(2, size=num_bits)
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.max_retries = max_retries
        self.current_idx = 0
        self.shared_secret = None
        self.kem = None

    def run(self):
        # Wait for public key from Bob
        yield self.await_port_input(self.node.ports["cin"])
        public_key_msg = self.node.ports["cin"].rx_input()
        public_key = public_key_msg.items[0]
        
        # Encapsulate shared secret
        self.kem = KeyEncapsulation("Kyber512")
        ciphertext, self.shared_secret = self.kem.encap_secret(public_key)
        
        # Send ciphertext to Bob
        self.node.ports["cout"].tx_output(Message([ciphertext]))
        
        # Encrypt and send bases
        bases_bytes = bases_to_bytes(self.bases)
        key = self.shared_secret[:len(bases_bytes)]
        encrypted_bases = bytes([b ^ k for b, k in zip(bases_bytes, key)])
        self.node.ports["cout"].tx_output(Message([encrypted_bases]))
        
        # Send qubits with sequence numbers
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
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.measurements = []
        self.alice_bases = None
        self.expected_idx = 0
        self.shared_secret = None
        self.kem = None

    def run(self):
        # Generate and send public key
        self.kem = KeyEncapsulation("Kyber512")
        public_key = self.kem.generate_keypair()
        self.node.ports["cout"].tx_output(Message([public_key]))
        
        # Receive ciphertext
        yield self.await_port_input(self.node.ports["cin"])
        ciphertext_msg = self.node.ports["cin"].rx_input()
        ciphertext = ciphertext_msg.items[0]
        self.shared_secret = self.kem.decap_secret(ciphertext)
        
        # Receive encrypted bases
        yield self.await_port_input(self.node.ports["cin"])
        encrypted_bases_msg = self.node.ports["cin"].rx_input()
        encrypted_bases = encrypted_bases_msg.items[0]
        
        # Decrypt bases
        bases_bytes = bytes([b ^ k for b, k in zip(encrypted_bases, self.shared_secret[:len(encrypted_bases)])])
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        
        # Receive qubits
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
    
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits)
    bob_protocol = BobProtocol(bob, num_bits)
    
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
    big_trials = 1
    while big_trials < 1000:
        big_trials *= 10
        trials = big_trials
        count = 0
        for _ in range(trials):
            if run_bb84_kem(20):
                count += 1
        arr.append(f"{count} in {big_trials}")
    print(arr)

# Execute the simulation
run_bb84_kem(20)
# survey()