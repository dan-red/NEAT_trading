import sys
import math, random
import cPickle as pickle
from neat import config, population, chromosome, genome, visualize
from neat.nn import nn_pure as nn

config.load('xor_config')

chromosome.node_gene_type = genome.NodeGene

INPUTS = [[0, 0], [0, 1], [1, 0], [1, 1]]
OUTPUTS = [0, 1, 1, 0]

def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print "Usage: python evaluateXOR.py chromo_file"
        return

    chromo_file = argv[0]
    fp = open(chromo_file, "r")
    chromo = pickle.load(fp)
    fp.close()
    print chromo
    visualize.draw_net(chromo, "_"+ chromo_file)
    
    # Let's check if it's really solved the problem
    print '\nNetwork output:'
    brain = nn.create_ffphenotype(chromo)
    for i, inputs in enumerate(INPUTS):
        output = brain.sactivate(inputs) # serial activation
        print "%1.5f \t %1.5f" %(OUTPUTS[i], output[0])

main()
