# Network-topology-with-Mininet
Creating a simple network topology using network emulator Mininet and testing this with ONOS network controller. 
The project consisted of two parts:
I - Designing a network against the backdrop of Europe consisting of 10 switches, exploring network emulation using Mininet, and investigating traffic characteristics using the iperf generator (impact of parameters on traffic flow using TCP/UDP protocols and during mixed sessions).
II - Extending the network and writing a client application enabling the determination of the most optimal path for the desired connection after sending a request to the ONOS REST API and practical network control using the ONOS network controller.

Code works properly only with having MININET running and having correctly connection to ONOS. 

# Repository contents:
links2.json - appropriately modified connections necessary to conduct data transmission in the following relations: Prague - Hamburg, Prague - Thessaloniki, Prague - Bergen, and Prague - Liverpool.
path_application.py - a client application that, based on the desired parameter (latency or throughput), determines the most optimal path using the Dijkstra's algorithm.

readyLinks.json - a file to which, after determining the best path, the application gathers relevant information and saves it (formatted according to template.json) for optimization purposes. It is continuously deleted to optimize memory usage.

template.json - a template for connections between cities, including the source host ID, destination host IP address, and outgoing connection port.

topoData.json - information about nodes and links in the network.

topology.png - visualization of the planned network.


# Other
The project created as part of the course on "Sieci i chmury teleinformatyczne" WUT 2023
