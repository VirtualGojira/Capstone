import netsquid as ns
import numpy as np
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.components.models.delaymodels import FixedDelayModel
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

def create_network():
    network = Network("BB84 Network")
    
    # Create nodes with quantum memories
    alice = Node(name="Alice", qmemory=ns.components.QuantumMemory("AliceMemory", num_positions=1))
    bob = Node(name="Bob", qmemory=ns.components.QuantumMemory("BobMemory", num_positions=1))
    
    # Add ports for communication
    alice.add_ports(["qout", "cout"])
    bob.add_ports(["qin", "cin"])
    
    # Quantum channel with no delay
    q_channel = QuantumChannel("QuantumChannel", delay_model=FixedDelayModel(delay=0))
    alice.ports["qout"].connect(q_channel.ports["send"])
    bob.ports["qin"].connect(q_channel.ports["recv"])
    
    # Classical channel with no delay
    c_channel = ClassicalChannel("ClassicalChannel", delay_model=FixedDelayModel(delay=0))
    alice.ports["cout"].connect(c_channel.ports["send"])
    bob.ports["cin"].connect(c_channel.ports["recv"])
    
    network.add_nodes([alice, bob])
    return network

class AliceProtocol(Protocol):
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bits = np.random.randint(2, size=num_bits)  # Random bits
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)  # Random bases
        self.sent = 0
        # print("Base, bit: ", self.bases, self.bits)

    def run(self):
        for i in range(self.num_bits):
            qubit = qapi.create_qubits(1)  # Create a qubit
            # print("Alice ", i, " th qubit before operation")
            # print(qubit[0].qstate.qrepr)
            # Encode the qubit based on bit and basis
            if self.bits[i] == 1:
                qapi.operate(qubit, ns.X)
            if self.bases[i] == 'X':
                qapi.operate(qubit, ns.H)
            # Send the qubit to Bob
            # print("Alice ", i, " th qubit after operation")
            # print(qubit[0].qstate.qrepr)
            self.node.ports["qout"].tx_output(Message(qubit))
            self.sent += 1
            yield self.await_timer(1)  # Simulate delay between sends
        
        # Send bases to Bob after all qubits are sent
        self.node.ports["cout"].tx_output(Message(self.bases.tolist()))

class BobProtocol(Protocol):
    def __init__(self, node, num_bits):
        super().__init__()
        self.node = node
        self.num_bits = num_bits
        self.bases = np.random.choice(['Z', 'X'], size=num_bits)  # Random bases
        self.measurements = []
        self.received = 0
        self.alice_bases = None

    def run(self):
        # Receive and measure qubits
        while self.received < self.num_bits:
            yield self.await_port_input(self.node.ports["qin"])
            message = self.node.ports["qin"].rx_input()
            if message is None:
                continue
            qubit = message.items[0]
            # Measure in Bob's basis
            if self.bases[self.received] == 'X':
                qapi.operate(qubit, ns.H)
            result, _ = qapi.measure(qubit)
            self.measurements.append(result)
            self.received += 1
        
        # Receive Alice's bases and sift the key
        yield self.await_port_input(self.node.ports["cin"])
        message = self.node.ports["cin"].rx_input()
        self.alice_bases = np.array(message.items[0])
        # Determine matching bases
        match_indices = np.where(self.bases == self.alice_bases)[0]
        sifted_key = [self.measurements[i] for i in match_indices]

def run_bb84(num_bits):
    ns.sim_reset()
    network = create_network()
    alice = network.nodes["Alice"]
    bob = network.nodes["Bob"]
    
    alice_protocol = AliceProtocol(alice, num_bits)
    bob_protocol = BobProtocol(bob, num_bits)
    
    alice_protocol.start()
    bob_protocol.start()
    
    stats = ns.sim_run()
    print(stats)
    
    # Retrieve results
    match_indices = np.where(alice_protocol.bases == bob_protocol.bases)[0]
    sifted_alice = [alice_protocol.bits[i] for i in match_indices]
    sifted_bob = [bob_protocol.measurements[i] for i in match_indices]
    
    print("Alice's sifted key:", sifted_alice)
    print("Bob's sifted key:  ", sifted_bob)
    print("Keys match:", sifted_alice == sifted_bob)
    print("Key Length:", len(sifted_alice))

# Example usage
run_bb84(128)