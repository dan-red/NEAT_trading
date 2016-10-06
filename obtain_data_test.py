# neat stuff can be found at /usr/local/lib/python2.6/site-packages/neat

import csv
import requests
from HTMLParser import HTMLParser
import uuid
import urlparse
import time
import urllib2
import datetime
# from neat import config, population, chromosome, genome, visualize
import config, population, chromosome, genome, visualize
#from neat import chromosome, visualize
#import genome
#import config
#import population
from neat.nn import nn_pure as nn
import copy
import operator
import math
import cPickle as pickle
import json
import os

# GLOBAL VARIABLES
INPUTS = []
OUTPUTS = []
BEST_CHROMO = 0
BEST_CHROMO_FITNESS = 0

def main():
    global INPUTS
    global OUTPUTS
    company_dict = get_companies()
    company_dict, stock_data = get_stock_data(company_dict)
    print "len(stock_data):", len(stock_data)
    print len(company_dict)

    # ~~~NEAT STUFF~~~
    config.load('project_config')

    chromosome.node_gene_type = genome.NodeGene

    # test with just one company
    # now do it with 20 companies
    outfile = open('results.txt', 'w')
    results_dict = {}
    #for i in range(20):
    #    company = company_dict.keys()[i]
    i = 0
    for key in company_dict:
        i += 1
        company = key
        print "COMPANY:", company
        print "PROGRESS: " + str(i) + "/" + str(len(company_dict))
        evolve(company, stock_data, outfile, results_dict)
        INPUTS = []
        OUTPUTS = []
        BEST_CHROMO = 0
        BEST_CHROMO_FITNESS = 0
        if i == 1670:
            break
    outfile.close()

    for company in results_dict.keys():
        print company + ":   " + str(results_dict[company])

    
def evolve(company, stock_data, outfile, results_dict):
    global INPUTS
    global OUTPUTS
    # inputs (list of lists -- inner lists are ten-day stock price trends, which move forward
    # one day at a time in the outer list)
    
    # print "input len:", len(INPUTS)
    # print "output len:", len(OUTPUTS)
    #INPUTS = []
    #OUTPUTS = []
    data_list = []
    for key in stock_data[company]:
        if key == 'Date':
            continue
        new_data = stock_data[company][key]
        new_data['date'] = key
        data_list.append(new_data)

    data_list.sort(key=operator.itemgetter('date'))
    for i in range(4, len(data_list) - 1):
        data_to_add = []
        for j in range(i-4, i+1):
            data_to_add.append(float(data_list[j]['open']))
        INPUTS.append(data_to_add)

    
    #print INPUTS
    # outputs
    #OUTPUTS = []
    for i in range(5, len(data_list)):
        #OUTPUTS.append(float(data_list[i]['open']))
        
        if float(data_list[i]['open']) > float(data_list[i-1]['open']):
            OUTPUTS.append(1)
        else:
            OUTPUTS.append(0)

    #print OUTPUTS
    #return
    # NEAT
    if not os.path.isfile("company_chromos/best_chromo_99_%s" % company):
        print "we have to evolve this chromo"
        population.Population.evaluate = eval_fitness

        pop = population.Population(company)

        pop.epoch(100, report=True, save_best=True)

    # visualize.plot_stats(pop.stats)

    # visualize.plot_species(pop.species_log)

    # evaluate
    try:
        fp = open("company_chromos/best_chromo_99_%s" % company, "r")
    except IOError:
        print "we couldn't evolve this chromo, oh well"
        return
    chromo = pickle.load(fp)
    fp.close()
    #chromo = pickle.load(BEST_CHROMO)
    #chromo = BEST_CHROMO
    #print chromo
    #visualize.draw_net(chromo, "_" + "best_chromo_99")

    # Let's check if it's really solved the prolem
    #print '\nNetwork output:'
    brain = nn.create_ffphenotype(chromo)

    counter1 = 0
    counter2 = 0
    counter3 = 0
    counter4 = 0
    counter5 = 0
    counter6 = 0
    counter7 = 0
    counter8 = 0
    counter9 = 0
    counter10 = 0

    """
    for i, inputs in enumerate(INPUTS):
        output = brain.sactivate(inputs)
        counter6 += output[0]

    avg_value = counter6/len(INPUTS)
    """
    # care more about the "weighted median" which is unbiased
    output_list = []
    avg_counter = 0
    for i, inputs in enumerate(INPUTS):
        output = brain.sactivate(inputs)
        output_list.append(output[0])
    
    for value in OUTPUTS:
        if value == 0:
            counter6 += 1

    median_value = sorted(output_list)[counter6]
    avg_value = sorted(output_list)[len(output_list)/2]

    for i, inputs in enumerate(INPUTS):
        output = brain.sactivate(inputs)
        #print "%1.5f \t %1.5f" %(OUTPUTS[i], output[0])
        if OUTPUTS[i] == 1:
            counter3 += 1
        else:
            counter5 += 1
        if OUTPUTS[i] == 1 and output[0] > 0.5:
            counter1 += 1
        elif OUTPUTS[i] == 0 and output[0] < 0.5:
            counter4 += 1
        if OUTPUTS[i] == 1 and output[0] > median_value:
            counter7 += 1
        elif OUTPUTS[i] == 0 and output[0] < median_value:
            counter8 += 1
        if OUTPUTS[i] == 1 and output[0] > avg_value:
            counter9 += 1
        elif OUTPUTS[i] == 0 and output[0] < avg_value:
            counter10 += 1

        counter2 += 1

    outfile.write("\n--STATISTICS--\n\n")
    s = "COMPANY: %s\n" % company
    outfile.write(s)
    s = "len(INPUTS): %d\n" % len(INPUTS)
    outfile.write(s)
    s = "NUMBER OF 1'S: %d\n" % counter3
    outfile.write(s)
    s = "NUMBER OF 0'S: %d\n" % (counter2 - counter3)
    outfile.write(s)
    s = "1'S CORRECT: %d/%d (%.3f%%)\n" % (counter1, counter3, float(counter1)/counter3 * 100)
    outfile.write(s)
    s = "0's CORRECT: %d/%d (%.3f%%)\n" % (counter4, counter5, float(counter4)/counter5 * 100)
    outfile.write(s)
    s = "GOT %d OUT OF %d CORRECT OVERALL (%.3f%%)\n" % (counter1 + counter4, counter2, float(counter1 + counter4)/counter2 * 100)
    outfile.write(s)
    s = "NUMBER OF 1'S CORRECT WHEN COMPARED TO WEIGHTED MEDIAN: %d/%d (%.3f%%)\n" % (counter7, counter3, float(counter7)/counter3 * 100)
    outfile.write(s)
    s = "NUMBER OF 0'S CORRECT WHEN COMPARED TO WEIGHTED MEDIAN: %d/%d (%.3f%%)\n" % (counter8, counter5, float(counter8)/counter5 * 100)
    outfile.write(s)
    s = "NUMBER OF 1'S CORRECT WHEN COMPARED TO AVERAGE VALUE: %d/%d (%.3f%%)\n" % (counter9, counter3, float(counter9)/counter3 * 100)
    outfile.write(s)
    s = "NUMBER OF 0'S CORRECT WHEN COMPARED TO AVERAGE VALUE: %d/%d (%.3f%%)\n" % (counter10, counter5, float(counter10)/counter5 * 100)
    outfile.write(s)

    # create a dictionary with the "results" of the training
    # key: company symbol
    # value: {chromo file, stat (NO, ACTUAL, AVG, MEDIAN), % ones correct, % zeroes correct}
    # note that stat is a string, and no means at least one of 1's/0's was correct < 50% of the time

    results_dict[company] = {}
    # results_dict[company]["chromo"] = chromo
    
    if min(counter1, counter4) > min(counter7, counter8):
        if min(counter1, counter4) > min(counter9, counter10):
            if counter1 < counter3/2 or counter4 < counter5/2:
                stat = "NO"
            else:
                stat = "ACTUAL"
                ones = float(counter1)/counter3 * 100
                zeroes = float(counter4)/counter5 * 100
        else:
            if counter9 < counter3/2 or counter10 < counter5/2:
                stat = "NO"
            else:
                stat = "AVERAGE"
                ones = float(counter9)/counter3 * 100
                zeroes = float(counter10)/counter5 * 100
    else:
        if min(counter7, counter8) > min(counter9, counter10):
            if counter7 < counter3/2 or counter8 < counter5/2:
                stat = "NO"
            else:
                stat = "MEDIAN"
                ones = float(counter7)/counter3 * 100
                zeroes = float(counter8)/counter5 * 100
        else:
            if counter9 < counter3/2 or counter10 < counter5/2:
                stat = "NO"
            else:
                stat = "AVERAGE"
                ones = float(counter9)/counter3 * 100
                zeroes = float(counter10)/counter5 * 100

    if stat == "NO":
        ones = 0
        zeroes = 0


    results_dict[company]["stat"] = stat
    results_dict[company]["ones_percent"] = ones
    results_dict[company]["zeroes_percent"] = zeroes
    results_dict[company]["average"] = avg_value
    results_dict[company]["median"] = median_value

    dict_string = json.dumps(results_dict)
    outfile = open('network_output.txt', 'w')
    outfile.write(dict_string)
    outfile.close()


def eval_fitness(population):
    global INPUTS
    global OUTPUTS
    counter = 0
    for chromo in population:
        brain = nn.create_ffphenotype(chromo)

        error = 0.0
        for i, inputs in enumerate(INPUTS):
            brain.flush()
            output = brain.sactivate(inputs)
            error += (output[0] - OUTPUTS[i])**2
        chromo.fitness = 1 - error
        """
        if counter == 0:
            BEST_CHROMO_FITNESS = chromo.fitness
            counter = 1
        if chromo.fitness > BEST_CHROMO_FITNESS:
            BEST_CHROMO_FITNESS = chromo.fitness
            BEST_CHROMO = chromo
        """


def get_companies():
    url = "http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NASDAQ&render=download"
    response = urllib2.urlopen(url)
    #reader = csv.reader(open('companylist.csv', 'r'))
    reader = csv.reader(response)
    company_dict = {}
    for row in reader:
        symbol, name, last_sale, market_cap, adr_tso, ipo_year, sector, industry, summary_quote, blah = row
        if symbol == "Symbol":
            continue
        company_dict[symbol] = {"name":name,
                                "last_sale":last_sale,
                                "market_cap":market_cap,
                                "adr_tso":adr_tso,
                                "ipo_year":ipo_year,
                                "sector":sector,
                                "industry":industry,
                                "summary_quote":summary_quote}

    return company_dict

def get_stock_data(company_dict):
    session = requests.session()
    
    test_company = company_dict[company_dict.keys()[0]]
    print company_dict.keys()[0]
    print test_company
    # response = session.get("http://ichart.finance.yahoo.com/table.csv?s=YHOO&d=0&e=28&f=2010&g=d&a=3&b=12&c=1996&ignore=.csv")
    stock_data = {}
    keys_to_delete = []
    for key in company_dict:
        print "getting data for:", key
        url = "http://ichart.finance.yahoo.com/table.csv?s=" + key
        a = 0
        b = 1
        if company_dict[key]["ipo_year"] == "n/a":
            company_dict[key]["ipo_year"] = 1999
        c = int(company_dict[key]["ipo_year"]) + 1
        date = datetime.date.today() - datetime.timedelta(days=1)
        d = date.month - 1
        e = date.day
        f = date.year
        if c > date.year - 2: # want at least two years of data
            keys_to_delete.append(key)
            continue
        g = "d"
        url += "&d=%d&e=%02d&f=%d&g=%s&a=%d&b=%02d&c=%d&ignore=.csv" % (d, e, f, g, a, b, c)
        print url
        try:
            response = urllib2.urlopen(url)
        except urllib2.HTTPError:
            keys_to_delete.append(key)
            continue
        #print response
        cr = csv.reader(response)
        stock_data[key] = {}
        for row in cr:
            date, open1, high, low, close, volume, adj_close = row
            stock_data[key][date] = {"open":open1,
                                     "high":high,
                                     "low":low,
                                     "close":close,
                                     "volume":volume,
                                     "adj_close":adj_close}

    for key in keys_to_delete:
        del company_dict[key]
    return company_dict, stock_data


main()
