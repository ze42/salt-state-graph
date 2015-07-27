#!/usr/bin/env python
"""
Usage:
    salt-state-graph2 <inputfile> <outputfile>

A tool that ingests the YAML representing the Salt (show)lowstate (or
show_low_sls) for a single minion and produces a program written in DOT.

The tool is useful for visualising the dependency graph of a Salt states.

"""
from pydot import Dot, Node, Edge, Cluster, Subgraph
import yaml
import sys


def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)


def generate_nodes(graph, state_obj):
    clusters = {}
    nodes = {}
    for state in state_obj:
        node_name = '{0}.{1}'.format(state.get('state'), state.get('__id__'))
        if node_name in nodes:
            nodes[node_name].set_label('{0}\n{1}'.format(nodes[node_name].get_label(), state.get('name')))
            #sys.stderr.write('ERROR: {0}: node declared multiple time\n'.format(node_name))
            continue
        nodes[node_name] = Node(node_name)
        nodes[node_name].set_label('{0}.{1}'.format(state.get('state'), state.get('__id__')))
        nodes[node_name].set_label('{0}\n{1}'.format(nodes[node_name].get_label(), state.get('name')))
        cluster_name = state['__sls__'].replace('.', '__')
        if cluster_name not in clusters:
            clusters[cluster_name] = Cluster(cluster_name)
            clusters[cluster_name].set_label(state['__sls__'])
            graph.add_subgraph(clusters[cluster_name])
        clusters[cluster_name].add_node(nodes[node_name])
    return nodes


def targets_name(targets, nodes):
    if targets is None:
        return
    assert(isinstance(targets, list))
    for target in targets:
        assert(isinstance(target, dict))
        assert(len(target) == 1)
        state, name = target.items()[0]
        targetname = '{0}.{1}'.format(state, name)
        if targetname not in nodes:
            sys.stderr.write('ERROR: {0}: node not found\n'.format(targetname))
            continue
        yield targetname


def generate_links(graph, state_obj, nodes):
    rules = {
        'require': {'color': 'blue'},
        'require_in': {'color': 'blue', 'reverse': True},
        'watch': {'color': 'red'},
        'watch_in': {'color': 'red', 'reverse': True},
    }
    seen = set()
    for state in state_obj:
        node_name = '{0}.{1}'.format(state.get('state'), state.get('__id__'))
        if node_name in seen:
            continue
        seen.add(node_name)
        for edge_type, ruleset in rules.items():
            for target in targets_name(state.get(edge_type), nodes):
                src, dst = node_name, target
                if ruleset.get('reverse'):
                    src, dst = dst, src
                graph.add_edge(Edge(dst, src, color=ruleset['color']))


def main(infilename, outfilename):
    state_obj = yaml.load(open(infilename))
    assert(isinstance(state_obj, dict))
    assert(len(state_obj) == 1)
    state_obj = state_obj.values()[0]
    assert(isinstance(state_obj, list))
    graph = Dot("states", graph_type='digraph')

    # First, create all graph nodes
    nodes = generate_nodes(graph, state_obj)
    # Then, generate our links
    generate_links(graph, state_obj, nodes)
    graph.write(outfilename)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
    main(*sys.argv[1:])
