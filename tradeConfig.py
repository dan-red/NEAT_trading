import math
import cPickle as pickle

# When using NEAT you must import the following
from neat import config, population, chromosome, genome, visualize
from neat.nn import nn_pure as nn

# When using NEAT you must create a configuration file to set the
# parameters of the evolution
config.load('xor_config')

chromosome.node_gene_type = genome.NodeGene

INPUTS = [[0, 0], [0, 1], [1, 0], [1, 1]]
OUTPUTS = [0, 1, 1, 0]

def eval_fitness(population):
    """
    Create a fitness function that returns higher values for better
    solutions.  For this task, we first calculate the sum-squared
    error of a network on the XOR task.  Good networks will have
    low error, so the fitness is 1 - sqrt(avgError).
    """
    for chromo in population:
        brain = nn.create_ffphenotype(chromo)

        error = 0.0
        for i, inputs in enumerate(INPUTS):
            brain.flush() 
            output = brain.sactivate(inputs)
            error += (output[0] - OUTPUTS[i])**2
        chromo.fitness = 1 - math.sqrt(error/len(OUTPUTS))

# Tell NEAT that we want to use the above function to evaluate fitness
population.Population.evaluate = eval_fitness

# Create a population (the size is defined in the configuration file)
pop = population.Population()

# Run NEAT's genetic algorithm for at most 30 epochs
# It will stop if fitness surpasses the max_fitness_threshold in config file
pop.epoch(30, report=True, save_best=True)

# Plots the evolution of the best/average fitness
visualize.plot_stats(pop.stats)

# Visualizes speciation
visualize.plot_species(pop.species_log)

