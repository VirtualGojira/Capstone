import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi


class MockKyber:
    def __init__(self):
        self.private_key = "dummy_private_key"
        self.public_key = "dummy_public_key"
    
    def encrypt(self, plaintext, public_key):
        return plaintext
    
    def decrypt(self, ciphertext, private_key):
        return ciphertext

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
    
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    # Convert distance from meters to kilometers for model parameters
    distance_km = DISTANCE / 1000  # Convert meters to kilometers
    
    # Quantum channel setup with corrected distance and loss model
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_delay_model = FibreDelayModel(length=distance_km, 
                                    c=SPEED_LIGHT_VACUUM, 
                                    ref_index=FIBRE_REFRACTIVE_INDEX)
    q_channel.models["delay_model"] = q_delay_model
    
    # Calculate loss probability from dB/km
    attenuation_db_per_km = FIBRE_ATTENUATION_DB_PERKM
    loss_probability_per_km = 1 - 10 ** (-attenuation_db_per_km / 10)
    q_loss_model = FibreLossModel(p_loss_init=0, 
                                  p_loss_length=loss_probability_per_km)
    q_channel.models["quantum_loss_model"] = q_loss_model

    # Classical channel setup with corrected distance
    c_channel = ClassicalChannel(name="ClassicalChannel", length=DISTANCE)
    c_delay_model = FibreDelayModel(length=distance_km,
                                    c=SPEED_LIGHT_VACUUM,
                                    ref_index=FIBRE_REFRACTIVE_INDEX)
    c_channel.models["delay_model"] = c_delay_model

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
        bases_bytes = bases_to_bytes(self.bases)
        ciphertext = self.kem.encrypt(bases_bytes, self.bob_public_key)
        self.node.ports["cout"].tx_output(Message(ciphertext))
        
        for i in range(self.num_bits):
            qubit = qapi.create_qubits(1)
            if self.bits[i] == 1:
                qapi.operate(qubit, ns.X)
            if self.bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            self.node.ports["qout"].tx_output(Message(qubit))
            yield self.await_timer(10)

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
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        bases_bytes = self.kem.decrypt(message.items[0], self.bob_private_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        
        start_time = ns.sim_time()
        while len(self.measurements) < self.num_bits and ns.sim_time() - start_time < 1e7:
            expr = yield self.await_port_input(self.node.ports["qin"]) | self.await_timer(1e7)
            if expr.first_term.value:
                message = self.node.ports["qin"].rx_input()
                if message is None or len(message.items) == 0:
                    continue
                qubit = message.items[0]
                if self.alice_bases[len(self.measurements)] == 'X':
                    qapi.operate(qubit, ns.H)
                result, _ = qapi.measure(qubit)
                self.measurements.append(result)
            else:
                break

def run_bb84_kem(num_bits):
    ns.sim_reset()
    network = create_network()

    kem = MockKyber()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits, kem.public_key)
    bob_protocol = BobProtocol(bob, num_bits, kem.private_key)
    
    alice_protocol.start()
    bob_protocol.start()

    stats = ns.sim_run(end_time=2e8)  
    print(stats)
    print("Alice's bits:", alice_protocol.bits.tolist())
    print("Bob's measurements:", bob_protocol.measurements)
    print("Key match:", alice_protocol.bits.tolist() == bob_protocol.measurements)
    print(f"Alice sent: {len(alice_protocol.bits)} bits")
    print(f"Bob received: {len(bob_protocol.measurements)} bits")
    if len(bob_protocol.measurements) > 0:
        match = alice_protocol.bits[:len(bob_protocol.measurements)].tolist() == bob_protocol.measurements
        if not alice_protocol.bits.tolist() == bob_protocol.measurements:
            print(f"Partial key match: {match}")
    else:
        print("Key exchange failed - no qubits received")

    if (alice_protocol.bits.tolist() == bob_protocol.measurements):
        return True

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
        print(f"Success rate: {count} in {trails} runs")
        arr.append(f"{count} in {big_trails}")
    print(arr)

# Corrected parameters
DISTANCE = 1  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000000  # meters per second (corrected from km/s to m/s)
FIBRE_ATTENUATION_DB_PERKM = 0.14  # dB per kilometer

survey()