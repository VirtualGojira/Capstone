import netsquid as ns
import numpy as np
import matplotlib.pyplot as plt
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models.delaymodels import FibreDelayModel
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

# Parameters (fixed)
SPEED_LIGHT_VACUUM = 300000  # km/s
FIBRE_ATTENUATION_DB_PERKM = 0.14
FIBRE_REFRACTIVE_INDEX = 1.2
DISTANCE = 100  # km
ENDTIME = 1e10  # ns

def create_network():
    network = Network("BB84 Network")
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    q_channel = QuantumChannel(name="QuantumChannel", length=DISTANCE)
    q_channel.models["delay_model"] = FibreDelayModel(length=DISTANCE, c=SPEED_LIGHT_VACUUM, ref_index=FIBRE_REFRACTIVE_INDEX)
    loss_prob = 1 - 10 ** (-FIBRE_ATTENUATION_DB_PERKM / 10)
    q_channel.models["quantum_loss_model"] = FibreLossModel(p_loss_init=0, p_loss_length=loss_prob)
    
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    
    c_channel = ClassicalChannel("ClassicalChannel", length=DISTANCE)
    alice.ports["cout"].connect(c_channel.ports["send"])
    bob.ports["cin"].connect(c_channel.ports["recv"])
    
    network.add_nodes([alice, bob])
    return network

class AliceProtocol(Protocol):
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bits = np.random.randint(2, size=num_bits)
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.sent = 0

    def run(self):
        for i in range(self.num_bits):
            qubit = qapi.create_qubits(1)
            if self.bits[i] == 1:
                qapi.operate(qubit, ns.X)
            if self.bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            self.node.ports["qout"].tx_output(Message(qubit))
            self.sent += 1
            yield self.await_timer(1)
        # Send the chosen bases over the classical channel.
        self.node.ports["cout"].tx_output(Message(self.bases.tolist()))

class BobProtocol(Protocol):
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)
        self.measurements = []
        self.received_indices = []
        self.received = 0
        self.alice_bases = None

    def run(self):
        while self.received < self.num_bits:
            yield self.await_port_input(self.node.ports["qin"])
            message = self.node.ports["qin"].rx_input()
            if message is None:
                continue
            qubit = message.items[0]
            if self.bases[self.received] == 'X':
                qapi.operate(qubit, ns.H)
            result, _ = qapi.measure(qubit)
            self.measurements.append(result)
            self.received_indices.append(self.received)
            self.received += 1
        # Receive Alice's bases via the classical channel.
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        self.alice_bases = np.array(message.items[0])

def run_bb84(num_bits):
    ns.sim_reset()
    network = create_network()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits)
    bob_protocol = BobProtocol(bob, num_bits)
    
    alice_protocol.start()
    bob_protocol.start()
    
    ns.sim_run(end_time=ENDTIME)

    # Identify indices where both used the same basis.
    match_indices = np.where(alice_protocol.bases == bob_protocol.bases)[0]
    valid_match_indices = [i for i in match_indices if i in bob_protocol.received_indices]

    sifted_alice = [alice_protocol.bits[i] for i in valid_match_indices]
    sifted_bob = [bob_protocol.measurements[bob_protocol.received_indices.index(i)] for i in valid_match_indices]
    
    key_match = sifted_alice == sifted_bob
    return key_match, len(sifted_alice)

def avg_runs(bit_sizes, num_runs=100):
    avg_key_lengths = []
    for n_bits in bit_sizes:
        total_key_length = 0
        match_count = 0
        for _ in range(num_runs):
            key_match, key_length = run_bb84(n_bits)
            total_key_length += key_length
            if key_match:
                match_count += 1
        avg_key_length = total_key_length / num_runs
        avg_key_lengths.append(avg_key_length)
        print(f"For {n_bits} bits: Keys matched in {match_count} out of {num_runs} runs, Average key length: {avg_key_length}")
    return avg_key_lengths

# Define the different bit sizes to simulate.
bit_sizes = [2, 4, 8, 16, 32, 64, 128, 256]

# Run the simulations and collect the average key lengths.
avg_key_lengths = avg_runs(bit_sizes)

# Calculate the percentage (key length / total bits) * 100 for each variant.
avg_percentages = [(avg_length / n_bits) * 100 for avg_length, n_bits in zip(avg_key_lengths, bit_sizes)]

# Create categorical labels for the variants.
variant_labels = [f"{n_bits} bits" for n_bits in bit_sizes]

# Plot the results as a bar graph with linear y-scale.
plt.figure(figsize=(10, 6))
plt.bar(variant_labels, avg_percentages, color='skyblue', edgecolor='black')
plt.xlabel("Variants (Number of bits sent)")
plt.ylabel("Key Generation Efficiency (%)")
plt.title("Percentage of Bits Remaining in Key vs. Variants of Number of Bits Sent in BB84 Protocol")
plt.grid(axis='y', linestyle="--", linewidth=0.5)
plt.savefig(f"naive_efficiency.eps", dpi=600, format='eps')
plt.show()
