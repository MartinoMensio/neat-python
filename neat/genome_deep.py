"""Extension for DeepNEAT"""

import sys
from random import choice

from neat import genome
from neat.aggregations import AggregationFunctionSet
from neat.config import ConfigParameter, write_pretty_params
from neat.genes_deep import DefaultConnectionGene_deep, DefaultNodeGene_deep
from neat.graphs import creates_cycle
from neat.six_util import iteritems, iterkeys
import neat.templates as templates

class DefaultGenomeConfig_deep(genome.DefaultGenomeConfig):
    allowed_connectivity = ['unconnected', 'full_nodirect', 'full', 'full_direct', 'predefined'] # TODO check these values

    def __init__(self, params):
        # Create full set of available activation functions.
        #self.activation_defs = ActivationFunctionSet()
        # ditto for aggregation functions - name difference for backward compatibility
        self.aggregation_function_defs = AggregationFunctionSet()
        self.aggregation_defs = self.aggregation_function_defs

        self._params = [# ConfigParameter('num_inputs', int), the inputs is always only one: the words
                        # ConfigParameter('num_outputs', int), the outputs are always three: AD, AI, AC
                        # ConfigParameter('num_hidden', int), # not required in predefined initial_connection, because the number of hidden units may change, defined in the templates
                        ConfigParameter('feed_forward', bool),
                        ConfigParameter('compatibility_disjoint_coefficient', float),
                        ConfigParameter('compatibility_weight_coefficient', float),
                        ConfigParameter('conn_add_prob', float),
                        ConfigParameter('conn_delete_prob', float),
                        ConfigParameter('node_add_prob', float),
                        ConfigParameter('node_delete_prob', float),
                        ConfigParameter('single_structural_mutation', bool, False),
                        ConfigParameter('structural_mutation_surer', str, 'default'),
                        ConfigParameter('initial_connection', str, 'unconnected'),
                        ConfigParameter('templates', str)]

        # Gather configuration data from the gene classes.
        self.node_gene_type = params['node_gene_type']
        print(self.node_gene_type.__dict__)
        #exit(1)
        self._params += self.node_gene_type.get_config_params()
        self.connection_gene_type = params['connection_gene_type']
        self._params += self.connection_gene_type.get_config_params()

        # Use the configuration data to interpret the supplied parameters.
        for p in self._params:
            setattr(self, p.name, p.interpret(params))

        # By convention, input pins have negative keys, and the output
        # pins have keys 0,1,...
        self.input_keys = ['in']
        self.output_keys = set()
        # self.output_keys = ['out.intent', 'out.boundaries', 'out.arguments'] # read from config

        # Verify that initial connection type is valid.

        assert self.initial_connection in self.allowed_connectivity

        # Verify structural_mutation_surer is valid.
        # pylint: disable=access-member-before-definition
        if self.structural_mutation_surer.lower() in ['1','yes','true','on']:
            self.structural_mutation_surer = 'true'
        elif self.structural_mutation_surer.lower() in ['0','no','false','off']:
            self.structural_mutation_surer = 'false'
        elif self.structural_mutation_surer.lower() == 'default':
            self.structural_mutation_surer = 'default'
        else:
            error_string = "Invalid structural_mutation_surer {!r}".format(
                self.structural_mutation_surer)
            raise RuntimeError(error_string)

        self.node_indexer = None

    def save(self, f):
        
        f.write('initial_connection      = {0}\n'.format(self.initial_connection))

        assert self.initial_connection in self.allowed_connectivity

        write_pretty_params(f, self, [p for p in self._params
                                      if not 'initial_connection' in p.name])

class DefaultGenome_deep(genome.DefaultGenome):
    @classmethod
    def parse_config(cls, param_dict):
        param_dict['node_gene_type'] = DefaultNodeGene_deep
        param_dict['connection_gene_type'] = DefaultConnectionGene_deep
        #param_dict['templates'] = param_dict['templates'].split()
        print(param_dict)
        print('HELLO')
        #exit(1)
        return DefaultGenomeConfig_deep(param_dict)

    def configure_new(self, config, genome_key):
        # deep note: removed partial and other connections
        """Configure a new genome based on the given configuration. The parameter `genome_key` identifies the genome"""

        available_templates = config.templates.split()
        print(available_templates)
        print(len(available_templates))
        #exit(1)
        # choose a template
        template_chosen_idx = genome_key % len(available_templates)
        template_to_build = available_templates[template_chosen_idx]
        print(template_to_build)
        nodes, connections = templates.parse(template_to_build, 'chosen.png')
        print(nodes, connections)
        for node in nodes:
            # set the type of node, predetermined by initial configurations
            config.type_of_layer_default = node.split('.')[0]
            self.nodes[node] = self.create_node(config, node)
            if 'out' in node:
                config.output_keys.add(node)
        # now restore the random node type choice for next nodes
        config.type_of_layer_default = 'random'
        for connection in connections:
            self.add_connection(config, connection.src.get_block_id(), connection.dst.get_block_id(), True)

        # Create node genes for the output pins.
        # for node_key in config.output_keys:
        #    self.nodes[node_key] = self.create_node(config, node_key)
        #self.output_keys = ['_'.join(k.split('_')[1:]) for k, v in config.items() if 'template' in k]
        #node_key = config.get_new_node_key(self.nodes)
        #assert node_key not in self.nodes
        # TODO create a node of type output
        #node = self.create_node(config, node_key)
        #self.nodes[node_key] = node
        # TODO parse template and get edges and nodes
        """
        # Add hidden nodes if requested.
        if config.num_hidden > 0:
            for i in range(config.num_hidden):
                node_key = config.get_new_node_key(self.nodes)
                assert node_key not in self.nodes
                node = self.create_node(config, node_key)
                self.nodes[node_key] = node
        """

        # Add connections based on initial connectivity type.
    
        # TODO add the possibility to have a digraph with inputs and outputs, properly

        if 'full' in config.initial_connection:
            if config.initial_connection == 'full_nodirect':
                self.connect_full_nodirect(config)
            elif config.initial_connection == 'full_direct':
                self.connect_full_direct(config)
            else:
                """
                if config.num_hidden > 0:
                    print(
                        "Warning: initial_connection = full with hidden nodes will not do direct input-output connections;",
                        "\tif this is desired, set initial_connection = full_nodirect;",
                        "\tif not, set initial_connection = full_direct",
                        sep='\n', file=sys.stderr)
                """
                self.connect_full_nodirect(config)
    
    def mutate_add_node(self, config):
        # deep note: removed weight
        if not self.connections:
            if config.check_structural_mutation_surer():
                self.mutate_add_connection(config)
            return

        # Choose a random connection to split
        conn_to_split = choice(list(self.connections.values()))
        #new_node_id = 'you_must_assign_me.{}'.format(config.get_new_node_key(self.nodes))
        ng, new_node_id = self.create_node_b(config)
        self.nodes[new_node_id] = ng

        # Disable this connection and create two new connections joining its nodes via
        # the given node.  The new node+connections have roughly the same behavior as
        # the original connection (depending on the activation function of the new node).
        conn_to_split.enabled = False

        i, o = conn_to_split.key
        self.add_connection(config, i, new_node_id, True)
        self.add_connection(config, new_node_id, o, True)

    def mutate_delete_node(self, config):
        # Do nothing if there are no non-output nodes.
        available_nodes = [k for k in iterkeys(self.nodes) if k not in config.output_keys]
        if not available_nodes:
            return -1

        del_key = choice(available_nodes)

        connections_to_delete = set()
        for k, v in iteritems(self.connections):
            if del_key in v.key:
                connections_to_delete.add(v.key)

        for key in connections_to_delete:
            del self.connections[key]

        del self.nodes[del_key]

        return del_key

    def add_connection(self, config, input_key, output_key, enabled):
        # deep note: removed weight
        # TODO: Add further validation of this connection addition? Like check that input and outputs can be connected, in shape or similar
        #assert isinstance(input_key, int)
        #assert isinstance(output_key, int)
        #assert output_key >= 0
        assert isinstance(enabled, bool)
        key = (input_key, output_key)
        connection = config.connection_gene_type(key)
        connection.init_attributes(config)
        connection.enabled = enabled
        self.connections[key] = connection

    def mutate_add_connection(self, config):
        """
        Attempt to add a new connection.
        Restrictions:
        - TODO add restrictions
        , the only restriction being that the output
        node cannot be one of the network input pins.
        """
        possible_outputs = list(self.nodes.keys())
        out_node = choice(possible_outputs)

        possible_inputs = possible_outputs + config.input_keys
        in_node = choice(possible_inputs)

        # Don't duplicate connections.
        key = (in_node, out_node)
        if key in self.connections:
            # TODO: Should this be using mutation to/from rates? Hairy to configure...
            if config.check_structural_mutation_surer():
                self.connections[key].enabled = True
            return

        # Don't allow connections between two output nodes
        if in_node in config.output_keys and out_node in config.output_keys:
            return

        # No need to check for connections between input nodes:
        # they cannot be the output end of a connection (see above).

        # For feed-forward networks, avoid creating cycles.
        if config.feed_forward and creates_cycle(list(self.connections.keys()), key):
            return

        cg = self.create_connection(config, in_node, out_node)
        self.connections[cg.key] = cg

    
    def create_node_b(self, config):
        node_id = 'tmp'
        node = config.node_gene_type(node_id)
        node.init_attributes(config)
        print(node)
        #node.type = node_id.split('.')[0]
        key = config.get_new_node_key(self.nodes)
        full_node_key = '{}.{}'.format(node.type_of_layer, key)
        node.key = full_node_key
        print(node)
        print(node.key)
        #exit(1)
        return node, full_node_key