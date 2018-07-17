"""Extension for DeepNEAT"""
from neat import genes
from neat.attributes import FloatAttribute, BoolAttribute, StringAttribute

class DefaultNodeGene_deep(genes.DefaultNodeGene):
    _gene_attributes = [StringAttribute('type_of_layer', options='dense rnn_monodir rnn_bidir decoder decoder_att yang_att concat out in embeddings'),
                        #StringAttribute('num_of_nodes', options='512 1024 2048'), # maybe later
                        #StringAttribute('activation', options='relu sigmoid'),
                        #StringAttribute('num_filters_conv', options='8 16 32 64'),
                        #StringAttribute('kernel_size_conv', options='1 3 5 7'),
                        #StringAttribute('stride_conv', options='1 2'),
                        #StringAttribute('stride_pool', options='1 2'),
                        #StringAttribute('poolsize_pool', options='2 3'),
                        #StringAttribute('has_maxpool', options='true false')
                        #StringAttribute('hidden_size', options='16 32 64 128 256')]
                        # TODO discover why the option values get destroyed (options from last attribute overwrite other attributes)
    ]

    def distance(self, other, config):
        factors = {
            'type_of_layer': 10,
            'hidden_size': 2,
            'activation': 1
        }
        

        d = 0.0
        if self.type_of_layer != other.type_of_layer:
            d += factors['type_of_layer']
        else:
            if self.type_of_layer == 'recurrent':
                pass
                #d += (abs(float(self.hidden_size)-float(other.hidden_size))/128)*factors['hidden_size']
            # TODO consider other differences

        return d * config.compatibility_weight_coefficient
        
class DefaultConnectionGene_deep(genes.DefaultConnectionGene):
    _gene_attributes = [BoolAttribute('enabled')]

    def distance(self, other, config):
        d = 0.0
        if self.enabled != other.enabled:
            d += 1.0
        return d * config.compatibility_weight_coefficient