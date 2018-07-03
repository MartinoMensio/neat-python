"""This module manages the parsing of templates written in the config section of deep NEAT"""
import re
import graphviz

class ConnectionPoint(object):
    def __init__(self, string):
        parts = string.split(':')
        if len(parts) > 1:
            rest, output_id = parts
        else:
            rest, output_id = parts[0], None
        parts = rest.split('.')
        if len(parts) > 1:
            type, instance_name = parts
        else:
            type, instance_name = parts[0], None
        self.type = type
        self.instance_name = instance_name
        self.output_id = output_id
    
    def __repr__(self):
        return '{}.{}:{}'.format(self.type, self.instance_name, self.output_id)

    def get_block_id(self):
        if self.instance_name:
            return '{}.{}'.format(self.type, self.instance_name)
        else:
            return self.type
class Connection(object):

    def __init__(self, src_str, dst_str):
        self.src = ConnectionPoint(src_str)
        self.dst = ConnectionPoint(dst_str)

    def __repr__(self):
        return '{}->{}'.format(self.src, self.dst)


def parse(config_string, draw_to=None):
    """from a config string returns a set of nodes and a set of connections"""
    config_string = re.sub(r'\s+', '', config_string)
    print('config_string', config_string)
    #exit(0)
    conns = config_string[1:-1].split('),(')
    connections_str = [tuple(c.split(',')) for c in conns]
    connections = [Connection(s[0], s[1]) for s in connections_str]
    # nodes ignore the specific output of the block, identified by :output_id
    nodes = set([c.src.get_block_id() for c in connections] + [c.dst.get_block_id() for c in connections])

    if draw_to:
        draw(connections, draw_to)

    return nodes, connections

def draw(connection_list, draw_to):
    graph = graphviz.Digraph('dot')
    for c in connection_list:
        print(c.dst.get_block_id(), c.src.get_block_id())
        graph.edge(c.src.get_block_id(), c.dst.get_block_id())
    graph.render(draw_to)


if __name__ == '__main__':

    #res = parse('(in,embeddings),(embeddings,encoder:seq),(encoder:seq,decoder.ac),(decoder.ac,out.ac)', 'temp0.png')
    #print(res)
    net = '''(in,embeddings),(embeddings,encoder),(encoder:seq,yang_att),(yang_att,dense),(dense,out.intent),(encoder:seq, decoder.bd),(decoder.bd,out.bd),(decoder.bd,decoder.ac),(decoder.ac,out.ac)'''
    res = parse(net, 'temp0.png')
    net_3_stages = '''(in,embeddings),(embeddings,encoder),(encoder:seq,yang_att),(yang_att,dense),(dense,out.intent),(encoder:seq, decoder.bd),(decoder.bd,out.bd),(encoder:seq,concat),(decoder.bd,concat),(concat,decoder.ac),(decoder.ac,out.ac)'''
    res = parse(net_3_stages, 'temp1.png')
    net = '''(in,embeddings),(embeddings,encoder),(encoder:single,dense),(dense,out.intent),(encoder:seq, decoder.bd),(decoder.bd,out.bd),(encoder:seq,concat),(decoder.bd,concat),(concat,decoder.ac),(decoder.ac,out.ac)'''
    res = parse(net, 'temp2.png')
    """"""