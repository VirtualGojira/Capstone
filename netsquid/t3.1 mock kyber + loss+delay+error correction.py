import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

# A dummy KEM for encrypting the basis information (not a secure implementation)
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
    
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    c_channel = ClassicalChannel(name="ClassicalChannel", length=DISTANCE)

    q_channel.models["delay_model"] = FibreDelayModel(length=DISTANCE, 
                                                      c=SPEED_LIGHT_VACUUM, 
                                                      ref_index=FIBRE_REFRACTIVE_INDEX)
    c_channel.models["delay_model"] = FibreDelayModel(length=DISTANCE, 
                                                      c=SPEED_LIGHT_VACUUM, 
                                                      ref_index=FIBRE_REFRACTIVE_INDEX)

    q_channel.models["quantum_loss_model"] = FibreLossModel(p_loss_init=0, 
                                                            p_loss_length=FIBRE_ATTENUATION_DB_PERKM)
    
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    alice.ports["cout"].connect(c_channel.ports["send"])
    bob.ports["cin"].connect(c_channel.ports["recv"])
    
    network.add_nodes([alice, bob])
    return network

# --- Alice Protocol with three-qubit repetition code ---
class AliceProtocol(Protocol):
    def __init__(self, node, num_logical_bits, bob_public_key, repetition=3):
        """
        :param repetition: number of physical qubits per logical bit (here, 3)
        """
        super().__init__()
        self.node = node
        self.num_logical_bits = num_logical_bits
        self.repetition = repetition
        self.bits = np.random.randint(2, size=num_logical_bits)
        self.bases = np.random.choice(['Z', 'X'], size=num_logical_bits)
        self.bob_public_key = bob_public_key
        self.kem = MockKyber()

    def run(self):
        # First, send the classical basis information (one per logical bit)
        bases_bytes = bases_to_bytes(self.bases)
        ciphertext = self.kem.encrypt(bases_bytes, self.bob_public_key)
        self.node.ports["cout"].tx_output(Message(ciphertext))
        
        # For each logical bit, send 'repetition' physical qubits carrying the same information
        for i in range(self.num_logical_bits):
            for r in range(self.repetition):
                qubit = qapi.create_qubits(1)
                # Encode the bit: if bit is 1, apply an X gate
                if self.bits[i] == 1:
                    qapi.operate(qubit, ns.X)
                # Rotate into the proper basis: if basis is 'X', apply an H gate
                if self.bases[i] == 'X':
                    qapi.operate(qubit, ns.H)
                self.node.ports["qout"].tx_output(Message(qubit))
                # Wait a little between qubit transmissions
                yield self.await_timer(10)

# --- Bob Protocol with majority vote error correction ---
class BobProtocol(Protocol):
    def __init__(self, node, num_logical_bits, bob_private_key, repetition=3):
        """
        Bob will expect repetition * num_logical_bits physical qubits.
        He will group every 'repetition' qubits, measure them, and decide the logical bit
        by majority vote.
        """
        super().__init__()
        self.node = node
        self.num_logical_bits = num_logical_bits
        self.repetition = repetition
        self.bob_private_key = bob_private_key
        self.logical_measurements = []  # logical bits after error correction
        self.kem = MockKyber()
        self.alice_bases = None

    def majority_vote(self, results):
        # Majority vote: if at least half of the measurements are 1, output 1.
        return 1 if sum(results) >= (len(results) / 2.0) else 0

    def run(self):
        # Wait for the classical message containing the basis information.
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        bases_bytes = self.kem.decrypt(message.items[0], self.bob_private_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_logical_bits)
        
        total_physical_qubits = self.num_logical_bits * self.repetition
        received_qubits = []
        start_time = ns.sim_time()
        
        # Collect all physical qubits.
        while len(received_qubits) < total_physical_qubits and ns.sim_time() - start_time < 1e7:
            expr = yield self.await_port_input(self.node.ports["qin"]) | self.await_timer(1e7)
            if expr.first_term.value:
                message = self.node.ports["qin"].rx_input()
                if message is None or len(message.items) == 0:
                    continue
                qubit = message.items[0]
                received_qubits.append(qubit)
            else:
                break
        
        # Process each group of 'repetition' qubits
        for i in range(self.num_logical_bits):
            group = received_qubits[i * self.repetition:(i + 1) * self.repetition]
            group_results = []
            for qubit in group:
                # Use the basis information: if basis is X, apply an H gate before measurement.
                if self.alice_bases[i] == 'X':
                    qapi.operate(qubit, ns.H)
                result, _ = qapi.measure(qubit)
                group_results.append(result)
            # Use majority voting on the group to decide the logical bit.
            corrected_bit = self.majority_vote(group_results)
            self.logical_measurements.append(corrected_bit)

def run_bb84_kem(num_logical_bits, repetition=3):
    ns.sim_reset()
    network = create_network()

    print("DEBUG:")
    computed_delay = (DISTANCE * FIBRE_REFRACTIVE_INDEX) / SPEED_LIGHT_VACUUM
    print(f"Computed fiber delay for quantum channel: {computed_delay * 1e6:.2f} µs")
    print(f"Distance: {DISTANCE} m")

    kem = MockKyber()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_logical_bits, kem.public_key, repetition=repetition)
    bob_protocol = BobProtocol(bob, num_logical_bits, kem.private_key, repetition=repetition)
    
    alice_protocol.start()
    bob_protocol.start()

    stats = ns.sim_run(end_time=2e8)  
    print(stats)
    print("Alice's bits:            ", alice_protocol.bits.tolist())
    print("Bob's logical measurements:", bob_protocol.logical_measurements)
    print("Key match:", alice_protocol.bits.tolist() == bob_protocol.logical_measurements)
    print(f"Alice sent: {len(alice_protocol.bits)} logical bits (encoded into {len(alice_protocol.bits)*repetition} physical qubits)")
    print(f"Bob received: {len(bob_protocol.logical_measurements)} logical bits")
    if (alice_protocol.bits.tolist() == bob_protocol.logical_measurements):
        return True

def survey():
    arr = []
    big_trials = 1
    while big_trials < 1000:
        big_trials *= 10
        trials = big_trials
        count = 0  # Reset count for each batch
        for i in range(trials):
            if run_bb84_kem(20, repetition=3):
                count += 1
        print(f"Success rate: {count} in {trials} runs")
        arr.append(f"{count} in {big_trials}")
    print(arr)

# Simulation parameters
DISTANCE = 1  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000  # km/s
FIBRE_ATTENUATION_DB_PERKM = 0.14  # dB/km

survey()
