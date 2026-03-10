import matplotlib.pyplot as plt
import networkx as nx

Graph = nx.DiGraph()

# Adds nodes (can be used as destinations)
Graph.add_nodes_from(["Uni", "House", "Shop", "Bus Stop"])

# Adds routes (distance to each point)
edge = [("Uni", "House", 20, 1), ("House", "Shop", 5, 1), ("Shop", "Bus Stop", 6, 1), ("Uni", "Bus Stop", 10, 1), ("Uni", "Shop", 12, 1)]

# add.edge("Point 1", "Point 2", "Travel time", "Number of vehicles route can hold", "How much traffic is using the route")
for u, v, travel_time, capacity in edge:
    Graph.add_edge(u, v, weight=travel_time, capacity=capacity, flow=0)

# plots a figure
def figures(graph, title):
    position = nx.spring_layout(graph)
    plt.figure(figsize=(8, 6))

    nx.draw_networkx_nodes(graph, position, node_size=500, node_color="red")
    nx.draw_networkx_labels(graph, position, font_size=10, font_color="black")
    nx.draw_networkx_edges(graph, position, width=2, edge_color="black")

    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, position, edge_labels=edge_labels)

    plt.title(title)
    plt.show()

figures(Graph, "Manchester")

