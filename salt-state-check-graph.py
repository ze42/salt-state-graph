#!/usr/bin/env python
"""
Usage:
    salt-state-check-graph <inputdotfile>

Check graph dependencies.

Error for any cycle.

For each subgraph (sls):
  - warn if it contains any source or sink.
  - display latest common ancestor
  - display first common descendant

"""

import pydot
import sys
import collections
import yaml


def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)


def get_nodes_info(graph):
    """
    Return a dict of nodes
    <node_name>
       - name (readable)
       - sg (subgraph name, readable)
       - up (direct ancestors - empty set)
       - down (direct descendants - empty set)
    """
    nodes = collections.defaultdict(lambda: {
        'name': None,
        'sg': None,
        'up': set(),
        'down': set(),
    })
    for node in graph.get_nodes():
        name = node.get_name()
        nodes[name]['name'] = name.strip('"')
    for sg in graph.get_subgraphs():
        sgname = sg.get_name().strip('"')
        if sgname.startswith('cluster_'):
            sgname = sgname[8:]
        sgname = sgname.replace('__', '.').replace('_dash_', '-')
        for node in sg.get_nodes():
            name = node.get_name()
            nodes[name]['name'] = name.strip('"')
            nodes[name]['sg'] = sgname
    return dict(nodes)


def load_links(graph, nodes):
    """
    Load edges from graph, and place them in ancestors/descendants in nodes
    """
    for edge in graph.get_edges():
        src = edge.get_source()
        dst = edge.get_destination()
        assert(src in nodes)
        assert(dst in nodes)
        nodes[src]['down'].add(dst)
        nodes[dst]['up'].add(src)


def get_node_lineage(nodes, name, direct, lineage):
    """
    Return ancestors for node <name>.
    Also cache result, and compute it for other ancestors.
    """
    if lineage not in nodes[name]:
        data = set()
        # Prevent cycle by storing it first
        nodes[name][lineage] = data
        for parent in nodes[name][direct]:
            data.add(parent)
            data.update(get_node_lineage(nodes, parent, direct, lineage))
        if name in data:
            print("ERROR: {0} has cyclic dependencies".format(name))
    return nodes[name][lineage]


def propagate_lineage(nodes):
    """
    Propagate up/down lineages

    Propage them from sources to sinks
    """
    for name in nodes:
        # Called just to populate lineages, both way
        get_node_lineage(nodes, name, 'up', 'ancestors')
        get_node_lineage(nodes, name, 'down', 'descendants')


def dump_nodes(nodes):
    """
    debug - dump nodes to stdout
    """
    for node in nodes.values():
        node['up'] = sorted(node['up'])
        node['down'] = sorted(node['down'])
        node['ancestors'] = sorted(node.get('ancestors', ()))
        node['descendants'] = sorted(node.get('descendants', ()))
    print(yaml.dump(nodes, default_flow_style=False))


def get_subgraphs(nodes):
    """
    group nodes by subgraphs
    """
    subs = collections.defaultdict(dict)
    for name, node in nodes.items():
        subs[node['sg']][name] = node
    return subs


def get_base_lineage(nodes, names, lineage):
    """
    return common base lineage.

    :param dict nodes: all existing nodes
    :param list names: list of considered nodes
    :param str lineage: direction to look
    """
    ret = set(names)
    for name in names:
        ret.difference_update(nodes[name][lineage])
    return ret

def get_lineage_status(allnodes, nodes, tags, lineage):
    """
    Get lineage status 

    Return:
      direct: list of nodes without anything in lineage
      tag: best tag common lineage (empty if not found)
      misc: best common lineage (empty if direct)
    """
    ret = {
        'direct': set(),
        'tags': [],
        'misc': [],
    }
    common = nodes.values()[0][lineage]
    for name, node in nodes.items():
        common.intersection_update(node[lineage])
        if not node[lineage]:
            ret['direct'].add(name)
    ret['misc'] = get_base_lineage(allnodes, common, lineage)
    ret['tags'] = get_base_lineage(allnodes, common & set(tags), lineage)
    return ret


def dump_graph_status(allnodes, graph, nodes, tags):
    """
    :param str graph: (sub)graph name
    :param dict nodes: subgraph nodes
    :param dict tags: tags nodes
    """
    up = get_lineage_status(allnodes, nodes, tags, 'ancestors')
    if up['direct']:
        for name in up['direct']:
            print("ERR: {0}: SOURCE: {1}".format(graph, nodes[name]['name']))
    else:
        if up['tags']:
            if len(up['tags']) > 1:
                print("ERR: {0}: multiple tag as source?!".format(graph))
            print("tag: {0}: require: {1}".format(graph, ', '.join((allnodes[x]['name'] for x in up['tags']))))
        elif up['misc']:
            print("any: {0}: require: {1}".format(graph, ', '.join((allnodes[x]['name'] for x in up['misc']))))
        else:
            print("ERR: {0}: no common source".format(graph))
    down = get_lineage_status(allnodes, nodes, tags, 'descendants')
    if down['direct']:
        for name in down['direct']:
            print("ERR: {0}: SINK: {1}".format(graph, nodes[name]['name']))
    else:
        if down['tags']:
            if len(down['tags']) > 1:
                print("ERR: {0}: multiple tag as sink?!".format(graph))
            print("tag: {0}: required by: {1}".format(graph, ', '.join((allnodes[x]['name'] for x in down['tags']))))
        elif down['misc']:
            print("any: {0}: required by: {1}".format(graph, ', '.join((allnodes[x]['name'] for x in down['misc']))))
        else:
            print("ERR: {0}: no common required by.".format(graph))


def dump_status(allnodes):
    """
    Dump status for each subgraphs
    """
    subgraphs = get_subgraphs(allnodes)
    tags = subgraphs[None]
    for name, node in tags.items():
        if not node['ancestors']:
            print("SOURCE: TAG/{0}".format(node['name']))
    for name, node in tags.items():
        if not node['descendants']:
            print("SINK  : TAG/{0}".format(node['name']))
    for sgname in sorted(subgraphs):
        if sgname is None:
            continue
        nodes = subgraphs[sgname]
        dump_graph_status(allnodes, sgname, nodes, tags)


def main(infilename):
    """
    Get all graph info, and then search for cycle, sources and sinks
    """
    graph = pydot.graph_from_dot_file(infilename)
    nodes = get_nodes_info(graph)
    load_links(graph, nodes)
    propagate_lineage(nodes)
    dump_status(nodes)
#    dump_nodes(nodes)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    main(*sys.argv[1:])
