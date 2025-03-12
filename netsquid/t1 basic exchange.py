import netsquid as ns
from netsquid.nodes import Node, Network
from netsquid.components.models import DelayModel
from netsquid.components import QuantumChannel
from netsquid.nodes import DirectConnection
from netsquid.protocols import NodeProtocol


class sampledelaymodel(DelayModel):
    def __init__(self, speed_of_light_fraction=0.5, standard_deviation=0.05):
        super().__init__()
        # (the speed of light is about 300,000 km/s)
        self.properties["speed"] = speed_of_light_fraction * 3e5
        self.properties["std"] = standard_deviation
        self.required_properties = ['length']  # in km

    def generate_delay(self, **kwargs):
        avg_speed = self.properties["speed"]
        std = self.properties["std"]
        # The 'rng' property contains a random number generator
        # We can use that to generate a random speed
        speed = self.properties["rng"].normal(avg_speed, avg_speed * std)
        delay = 1e9 * kwargs['length'] / speed  # in nanoseconds
        return delay
    

class basicprotocol(NodeProtocol):
    def __init__(self, node, observable, qubit=None):
        super().__init__(node)
        self.observable = observable
        self.qubit = qubit
        # Define matching pair of strings for pretty printing of basis states:
        self.basis = ["|0>", "|1>"] if observable == ns.Z else ["|+>", "|->"]

    def run(self):
        if self.qubit is not None:
            # Send (TX) qubit to the other node via port's output:
            self.node.ports["qubitIO"].tx_output(self.qubit)
        while True:
            # Wait (yield) until input has arrived on our port:
            yield self.await_port_input(self.node.ports["qubitIO"])
            # Receive (RX) qubit on the port's input:
            message = self.node.ports["qubitIO"].rx_input()
            qubit = message.items[0]
            meas, prob = ns.qubits.measure(qubit, observable=self.observable)
            print(f"{ns.sim_time():5.1f}: {self.node.name} measured "
                  f"{self.basis[meas]} with probability {prob:.2f}")
            # Send (TX) qubit to the other node via connection:
            self.node.ports["qubitIO"].tx_output(qubit)



Alice_node = Node(name="Alice")
Bob_node = Node(name="Bob")

distance = 1/1000 # default is km, henche this is 1m

delay_model = sampledelaymodel()

channel_atob = QuantumChannel(name="qchannel[Alice to Bob]",
                           length=distance,
                           models={"delay_model": delay_model})
channel_btoa = QuantumChannel(name="qchannel[Bob to Alice]",
                           length=distance,
                           models={"delay_model": delay_model})


connection = DirectConnection(name="conn[Alice|Bob]",
                              channel_AtoB=channel_atob,
                              channel_BtoA=channel_btoa)

Alice_node.connect_to(remote_node=Bob_node, connection=connection,
                     local_port_name="qubitIO", remote_port_name="qubitIO")

qubits = ns.qubits.create_qubits(1)
Alice_Protocol = basicprotocol(Alice_node, observable=ns.Z, qubit=qubits[0])
Bob_Protocol = basicprotocol(Bob_node, observable=ns.X)

Alice_Protocol.start()
Bob_Protocol.start()
run_stats = ns.sim_run(duration=30)
print(run_stats)