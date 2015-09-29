#!/usr/bin/env python
"""
Usage:
    salt-state-graph <inputfile> <outputfile>

A tool that ingests the YAML representing the Salt (show)lowstate (or
show_low_sls) for a single minion and produces a program written in DOT.

The tool is useful for visualising the dependency graph of a Salt states.

"""
from pydot import Dot, Node, Edge, Cluster, Subgraph
import yaml
import sys
import collections

def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)

_nocluster = {
    'generic.common.tags',
    'generic.common.fixes.tags',
}


def generate_nodes(graph, state_obj):
    global _nocluster
    clusters = {}
    nodes = {}
    namemap = collections.defaultdict(set)
    for state in state_obj:
        node_name = '{0}.{1}'.format(state.get('state'), state.get('__id__'))
        if 'name' in state:
            # map_name, to 
            map_name = '{0}.{1}'.format(state.get('state'), state['name'])
            namemap[map_name].add(node_name)
        if node_name in nodes:
            nodes[node_name].set_label('{0}\n{1}'.format(nodes[node_name].get_label(), state.get('name')))
            #sys.stderr.write('ERROR: {0}: node declared multiple time\n'.format(node_name))
            continue
        nodes[node_name] = Node(node_name)
        nodes[node_name].set_label('{0}.{1}'.format(state.get('state'), state.get('__id__')))
        nodes[node_name].set_label('{0}\n{1}'.format(nodes[node_name].get_label(), state.get('name')))
        cluster_name = state['__sls__'].replace('.', '__').replace('-', '_dash_')
        if state['__sls__'] in _nocluster:
            tagname = state['__sls__']
            if tagname.endswith('.tags'):
                tagname = tagname[:-5]
#            nodes[node_name].set_label('TAG: {0}\n{1}'.format(
#                tagname,
#                nodes[node_name].get_label()
#                ))
            nodes[node_name].set_shape('diamond')
            nodes[node_name].set_color('#55bb55')
            nodes[node_name].set_style('filled')
            # nodes[node_name].set_image('taupe.jpg')
        if cluster_name not in clusters:
            if state['__sls__'] in _nocluster:
                clusters[cluster_name] = graph
            else:
                clusters[cluster_name] = Cluster(cluster_name)
                clusters[cluster_name].set_label(state['__sls__'])
                graph.add_subgraph(clusters[cluster_name])
        clusters[cluster_name].add_node(nodes[node_name])
    retnamemap = {}
    for name in namemap:
        if 1 != len(namemap[name]):
            #sys.stderr.write('WARNING: {}: multiple mapping, so map ignored:\n - {}\n'.format(name, '\n - '.join(namemap[name])))
            pass
        else:
            retnamemap[name] = next(iter(namemap[name]))
    return nodes, retnamemap


def targets_name(targets, nodes, nodemap):
    if targets is None:
        return
    assert(isinstance(targets, list))
    for target in targets:
        assert(isinstance(target, dict))
        assert(len(target) == 1)
        state, name = target.items()[0]
        targetname = '{0}.{1}'.format(state, name)
        if targetname in nodes:
            yield targetname
            continue
        if targetname in nodemap:
            yield nodemap[targetname]
            continue
        sys.stderr.write('ERROR: {0}: node not found\n'.format(targetname))


def generate_links(graph, state_obj, nodes, nodemap):
    rules = {
        'require': {'color': '#0000ff'},
        'require_in': {'color': '#9090ff', 'reverse': True, 'style': 'dashed', },
        'watch': {'color': '#ff0000'},
        'watch_in': {'color': '#ff9090', 'reverse': True, 'style': 'dashed', },
    }
    seen = set()
    for state in state_obj:
        node_name = '{0}.{1}'.format(state.get('state'), state.get('__id__'))
        if node_name in seen:
            continue
        seen.add(node_name)
        for edge_type, ruleset in rules.items():
            for target in targets_name(state.get(edge_type), nodes, nodemap):
                src, dst = node_name, target
                if ruleset.get('reverse'):
                    src, dst = dst, src
                edge = Edge(dst, src, color=ruleset['color'])
                if 'style' in ruleset:
                    edge.set_style(ruleset.get('style'))
                graph.add_edge(edge)


def main(infilename, outfilename):
    state_obj = yaml.load(open(infilename))
    assert(isinstance(state_obj, dict))
    assert(len(state_obj) == 1)
    state_obj = state_obj.values()[0]
    assert(isinstance(state_obj, list))
    graph = Dot("states", graph_type='digraph')

    # First, create all graph nodes
    nodes, nodemap = generate_nodes(graph, state_obj)
    # Then, generate our links
    generate_links(graph, state_obj, nodes, nodemap)
    graph.write(outfilename)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
    main(*sys.argv[1:])
