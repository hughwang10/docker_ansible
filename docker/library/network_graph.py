#!/usr/bin/python
"""
Can generate a network graph for only network_problem
variable from the Ansible
"""

import os
import matplotlib
import base64
matplotlib.use('Agg')

from time import strftime
import matplotlib.pyplot as plt


import networkx as nx

def main():
    """ Creating graph and drawing using matplotlib.pyplot"""
    module = AnsibleModule(
        argument_spec=dict(
            network=dict(required=True),
            dst=dict(required=True),
        )
    )
    network = module.params['network']


    bad_network_edge_list = []
    for item in network[0]["children"]:
        devices = item["text"].split(":")[1]
        device_in_link = devices.split("-->")
        link_condition = item['li_attr']['class']
        link = (device_in_link[0].strip(), device_in_link[1].strip(), link_condition)
        bad_network_edge_list.append(link)

    bad_link_output_file, bad_link_image = draw_graph(bad_network_edge_list, module.params['dst'], "Bad_links")

    low_throughput_edge_list = []
    for item in network[1]["children"]:
        devices = item["text"]
        device_in_link = devices.split("-->")
        link_throughput = item['children'][0]['text']
        throughput = str(link_throughput.split(":")[1])
        link = (device_in_link[0].strip(), device_in_link[1].strip(), throughput)
        low_throughput_edge_list.append(link)

    low_throughput_output_file, low_throughput_link_image = draw_graph(low_throughput_edge_list, module.params['dst'], "Low_throughput_links",
                                                                       True)

    result = {
        "Network"                      : module.params['network'],
        "bad_link_file_location"       : module.params['dst'],
        "bad_link_file_name"           : bad_link_output_file,
        "bad_link_image"               : bad_link_image,
        "low_throughput_file_location" : module.params['dst'],
        "low_throughput_file_name"     : low_throughput_output_file,
        "low_throughput_image"         : low_throughput_link_image,

    }
    module.exit_json(changed=False, results=result)


def draw_graph(graph, destination, filename, edge_labels=False, graph_layout='shell', node_size=50,
               node_color='blue', node_alpha=0.5, node_text_size=12, edge_color='green',
               edge_alpha=1.0, edge_tickness=1, edge_text_pos=0.3, text_font='sans-serif'):

    """
    Takes a list(edge_list) containing the bad links as tuple(edges)
    and saves a  layout of the graph in the current directory
    """

    nx_graph = nx.Graph()

    plt.clf()

    for edge in graph:
        nx_graph.add_edge(edge[0], edge[1])

    # find the position and draw the nodes
    graph_pos = nx.shell_layout(nx_graph)
    nx.draw_networkx_nodes(nx_graph, graph_pos, node_size=node_size,
                           alpha=node_alpha, node_color=node_color)

    # draw edges for bad_link graph
    if filename == "Bad_links":
        edge_warning = []
        edge_danger = []
        for edge in graph:
            if edge[2] == "text-warning":
                edge_warning.append((edge[0], edge[1]))
            elif edge[2] == "text-danger":
                edge_danger.append((edge[0], edge[1]))
        nx.draw_networkx_edges(nx_graph, graph_pos, edgelist=edge_warning, width=edge_tickness,
                               alpha=0.5, edge_color='r')
        nx.draw_networkx_edges(nx_graph, graph_pos, edgelist=edge_danger, width=edge_tickness,
                               alpha=edge_alpha, edge_color='r')
        plt.title("Bad links in MSP")

    # draw labels and edges for link_throughput graph
    if filename == "Low_throughput_links" and edge_labels == True:
        edge_labels = dict()
        for edge in graph:
            labels = edge[2]
            key = (edge[0], edge[1])
            edge_labels[key] = labels
        nx.draw_networkx_edges(nx_graph, graph_pos, width=edge_tickness,
                               alpha=0.8, edge_color='r')
        nx.draw_networkx_edge_labels(nx_graph, graph_pos, edge_labels=edge_labels)
        plt.title("Low throughput links in MSP")


    nx.draw_networkx_labels(nx_graph, graph_pos, font_size=node_text_size,
                            font_family=text_font)



    filename += (strftime("%y-%m-%d_%H:%M:%S") + ".png")
    file_destination = os.path.join(destination, filename)

    plt.savefig(file_destination, dpi=200, facecolor='w', edgecolor='w',orientation='portrait', papertype=None,
                format=None, transparent=False, bbox_inches=None, pad_inches=0.1)


    with open(file_destination, 'r') as current_file:
        image = base64.b64encode(current_file.read())

    return file_destination, image

from ansible.module_utils.basic import *
main()
