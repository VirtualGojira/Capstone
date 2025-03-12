import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi


###########################
# Dummy KEM Implementation
###########################
class MockKyber:
    def __init__(self):
        self.private_key = "dummy_private_key"
        self.public_key = "dummy_public_key"
    
    def encrypt(self, plaintext, public_key):
        return plaintext
    
    def decrypt(self, ciphertext, private_key):
        return ciphertext

#################################
# Helper Functions for Bases
#################################
def bases_to_bytes(bases):
    return bytes([int(''.join(['1' if b == 'X' else '0' for b in bases[i:i+8]]).ljust(8, '0')[:8], 2)
                  for i in range(0, len(bases), 8)])

def bytes_to_bases(byte_stream, num_bits):
    return ['X' if (byte >> (7 - i)) & 1 else 'Z'
            for byte in byte_stream for i in range(8)][:num_bits]

#######################
# Network Construction
#######################
def create_network():
    network = Network("Underwater BB84-KEM Network")
    
    # Add extra ports for bidirectional classical communication.
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob   = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    # Alice: qout (send qubits), cout (send classical), cin (receive classical)
    alice.add_ports(["qout", "cout", "cin"])
    # Bob: qin (receive qubits), cin (receive classical), cout (send classical)
    bob.add_ports(["qin", "cin", "cout"])
    
    # Distance conversion (meters to kilometers) for delay models
    distance_km = DISTANCE / 1000  # DISTANCE is in meters
    
    # Set up the quantum channel.
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_delay_model = FibreDelayModel(length=distance_km, 
                                    c=SPEED_LIGHT_VACUUM, 
                                    ref_index=FIBRE_REFRACTIVE_INDEX)
    q_channel.models["delay_model"] = q_delay_model
    
    # Compute loss probability from attenuation (per km)
    loss_probability_per_km = 1 - 10 ** (-FIBRE_ATTENUATION_DB_PERKM / 10)
    q_loss_model = FibreLossModel(p_loss_init=0, 
                                  p_loss_length=loss_probability_per_km)
    q_channel.models["quantum_loss_model"] = q_loss_model
    
    # Set up a classical channel from Alice to Bob.
    c_channel_A2B = ClassicalChannel(name="CChannel_Alice_to_Bob", length=DISTANCE)
    c_delay_model_A2B = FibreDelayModel(length=distance_km,
                                        c=SPEED_LIGHT_VACUUM,
                                        ref_index=FIBRE_REFRACTIVE_INDEX)
    c_channel_A2B.models["delay_model"] = c_delay_model_A2B
    
    # And a classical channel from Bob to Alice for retransmission requests.
    c_channel_B2A = ClassicalChannel(name="CChannel_Bob_to_Alice", length=DISTANCE)
    c_delay_model_B2A = FibreDelayModel(length=distance_km,
                                        c=SPEED_LIGHT_VACUUM,
                                        ref_index=FIBRE_REFRACTIVE_INDEX)
    c_channel_B2A.models["delay_model"] = c_delay_model_B2A

    # Connect the channels:
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    
    alice.ports["cout"].connect(c_channel_A2B.ports["send"])
    bob.ports["cin"].connect(c_channel_A2B.ports["recv"])
    
    bob.ports["cout"].connect(c_channel_B2A.ports["send"])
    alice.ports["cin"].connect(c_channel_B2A.ports["recv"])
    
    network.add_nodes([alice, bob])
    return network

#################################
# Alice Protocol with Tagging & Retransmission
#################################
class AliceProtocol(Protocol):
    def __init__(self, node, num_bits, bob_public_key):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        # Generate random bits and bases.
        self.bits = np.random.randint(2, size=num_bits)
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.bob_public_key = bob_public_key
        self.kem = MockKyber()
    
    def run(self):
        # First, send classical basis information.
        bases_bytes = bases_to_bytes(self.bases)
        ciphertext = self.kem.encrypt(bases_bytes, self.bob_public_key)
        self.node.ports["cout"].tx_output(Message(ciphertext))
        
        # Phase 1: send each qubit with its index attached in meta.
        for i in range(self.num_bits):
            qubit = qapi.create_qubits(1)
            if self.bits[i] == 1:
                qapi.operate(qubit, ns.X)
            if self.bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            # Send the qubit (directly) with meta data.
            self.node.ports["qout"].tx_output(
                Message(qubit, meta={"index": i}, preserve_meta=True)
            )
            yield self.await_timer(10)
        
        # Wait for a retransmission request.
        evt = yield self.await_port_input(self.node.ports["cin"]) | self.await_timer(1e7)
        if evt.first_term.value:
            msg = self.node.ports["cin"].rx_input()
            if isinstance(msg.items, list) and isinstance(msg.items[0], list):
                missing_indices = msg.items[0]
                print("Alice: Received retransmission request for indices:", missing_indices)
                # Resend missing qubits.
                for i in missing_indices:
                    qubit = qapi.create_qubits(1)
                    if self.bits[i] == 1:
                        qapi.operate(qubit, ns.X)
                    if self.bases[i] == 'X':
                        qapi.operate(qubit, ns.H)
                    self.node.ports["qout"].tx_output(
                        Message(qubit, meta={"index": i}, preserve_meta=True)
                    )
                    yield self.await_timer(10)
        else:
            print("Alice: No retransmission request received.")

#################################
# Bob Protocol with Tagging & Retransmission
#################################
class BobProtocol(Protocol):
    def __init__(self, node, num_bits, bob_private_key):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bob_private_key = bob_private_key
        self.kem = MockKyber()
        self.alice_bases = None
        # Dictionary to store received qubits: key=index, value=qubit.
        self.received_qubits = {}
    
    def run(self):
        # Phase 0: Receive classical basis information.
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        bases_bytes = self.kem.decrypt(message.items, self.bob_private_key)
        self.alice_bases = bytes_to_bases(bases_bytes, self.num_bits)
        
        # Phase 1: Receive qubits.
        collection_time = 1e7  # ns
        start_time = ns.sim_time()
        while ns.sim_time() - start_time < collection_time:
            evt = yield self.await_port_input(self.node.ports["qin"]) | self.await_timer(1e6)
            if evt.first_term.value:
                msg = self.node.ports["qin"].rx_input()
                if msg is None:
                    continue
                qubit = msg.items  # msg.items is the qubit
                index = msg.meta.get("index", None)
                if index is None:
                    print("Bob: Warning, no index provided in message; skipping.")
                    continue
                if index not in self.received_qubits:
                    self.received_qubits[index] = qubit
            else:
                break
        
        # Identify missing indices.
        missing = [i for i in range(self.num_bits) if i not in self.received_qubits]
        if missing:
            print("Bob: Missing indices detected:", missing)
            self.node.ports["cout"].tx_output(Message(missing))
            # Wait for retransmitted qubits.
            retrans_time = 1e7  # ns
            start_time = ns.sim_time()
            while ns.sim_time() - start_time < retrans_time:
                evt = yield self.await_port_input(self.node.ports["qin"]) | self.await_timer(1e6)
                if evt.first_term.value:
                    msg = self.node.ports["qin"].rx_input()
                    if msg is None:
                        continue
                    qubit = msg.items
                    index = msg.meta.get("index", None)
                    if index is None:
                        print("Bob: Warning, no index provided in retransmitted message; skipping.")
                        continue
                    if index not in self.received_qubits:
                        self.received_qubits[index] = qubit
                else:
                    break
        
        missing = [i for i in range(self.num_bits) if i not in self.received_qubits]
        if missing:
            print("Bob: After retransmission, still missing indices:", missing)
        
        # Finally, measure the qubits in order.
        measurements = [None] * self.num_bits
        for i in range(self.num_bits):
            if i in self.received_qubits:
                qubit = self.received_qubits[i]
                if self.alice_bases[i] == 'X':
                    qapi.operate(qubit, ns.H)
                result, _ = qapi.measure(qubit)
                measurements[i] = result
            else:
                measurements[i] = None
        print("Bob's final measurements:", measurements)
        self.measurements = measurements

#################################
# Running the Simulation
#################################
def run_bb84_kem(num_bits):
    ns.sim_reset()
    network = create_network()

    kem = MockKyber()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits, kem.public_key)
    bob_protocol   = BobProtocol(bob, num_bits, kem.private_key)
    
    alice_protocol.start()
    bob_protocol.start()
    
    stats = ns.sim_run(end_time=2e8)
    print(stats)
    print("Alice's bits:             ", alice_protocol.bits.tolist())
    print("Bob's measurements:       ", bob_protocol.measurements)
    key_match = alice_protocol.bits.tolist() == bob_protocol.measurements
    print("Key match:", key_match)
    print(f"Alice sent: {len(alice_protocol.bits)} bits")
    print(f"Bob received: {sum(1 for m in bob_protocol.measurements if m is not None)} bits")
    return key_match

def survey():
    arr = []
    big_trials = 1
    while big_trials < 1000:
        big_trials *= 10
        trials = big_trials
        count = 0
        for i in range(trials):
            if run_bb84_kem(20):
                count += 1
        print(f"Success rate: {count} in {trials} runs")
        arr.append(f"{count} in {big_trials}")
    print(arr)

########################
# Simulation Parameters
########################
DISTANCE = 1  # meters
FIBRE_REFRACTIVE_INDEX = 1.2
SPEED_LIGHT_VACUUM = 300000000  # meters per second
FIBRE_ATTENUATION_DB_PERKM = 0.14  # dB per kilometer

survey()
