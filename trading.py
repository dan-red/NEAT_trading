import json
import csv
import requests
import urlparse
import time
import urllib2
import datetime
import copy
import operator
import math
import cPickle as pickle
import os
import dateutil.parser
from neat.nn import nn_pure as nn

def main():
    # network output dictionary
    infile = open('network_output.txt', 'r')
    results = json.loads(infile.readlines()[0])
    infile.close()

    # stock data dictionary (same as obtain_data_test.py)
    company_dict = get_companies()
    company_dict, stock_data = get_stock_data(company_dict)

    # starting variables
    start_money = 1000
    transaction_costs = 0
    current_stocks = {}
    start_date = datetime.date(2015, 7, 26)
    test_results = {}

    for i in range(30):
        start_date += datetime.timedelta(days=1)
        if start_date.weekday() == 5 or start_date.weekday() == 6:
            continue
        test_results[start_date] = {}

        # build the data dictionary (subset of stock_data for the last few dates)
        test_data = {}
        for company in company_dict:
            test_data[company] = {}
            for key in stock_data[company]:
                if key == 'Date':
                    continue
                if dateutil.parser.parse(key).date() < start_date:
                    continue
                #new_data = stock_data[company][key]
                #new_data['date'] = key
                #data_list.append(new_data)
                test_data[company][key] = stock_data[company][key]
                test_data[company][key]['date'] = key

            #data_list.sort(key=operator.itemgetter('date'))

        # see how many predictions we get right for the first day (August 3rd)

        count_correct_gain = 0
        count_correct_loss = 0
        count_incorrect = 0
        count_wtf = 0

        inputs = {}
        for company in results:
            if company not in test_data.keys():
                print "WTF?"
                count_wtf += 1
                continue
            if results[company]['stat'] == "NO":
                continue
            inputs[company] = []
            for key in test_data[company]:
                inputs[company].append(test_data[company][key])
            inputs[company].sort(key=operator.itemgetter('date'))

            # load the brain and test
            try:
                fp = open("company_chromos/best_chromo_99_%s" % company, "r")
            except IOError:
                print "damn, couldn't load the chromo"
                continue
            chromo = pickle.load(fp)
            fp.close()
            brain = nn.create_ffphenotype(chromo)

            #network_inputs = inputs[company][0:5]
            network_inputs = []
            if len(inputs[company]) < 6:
                continue
            for i in range(5):
                network_inputs.append(inputs[company][i]['open'])
            #print network_inputs
            output = brain.sactivate(network_inputs)
            actual_output = output[0]

            if results[company]['stat'] == "ACTUAL":
                if actual_output > 0.5 and inputs[company][5]['open'] > inputs[company][4]['open']:
                    count_correct_gain += 1
                elif actual_output < 0.5 and inputs[company][5]['open'] < inputs[company][4]['open']:
                    count_correct_loss += 1
                else:
                    count_incorrect += 1

            elif results[company]['stat'] == "AVERAGE":
                if actual_output > results[company]['average'] and inputs[company][5]['open'] > inputs[company][4]['open']:
                    count_correct_gain += 1
                elif actual_output < results[company]['average'] and inputs[company][5]['open'] < inputs[company][4]['open']:
                    count_correct_loss += 1
                else:
                    count_incorrect += 1

            elif results[company]['stat'] == "MEDIAN":
                if actual_output > results[company]['median'] and inputs[company][5]['open'] > inputs[company][4]['open']:
                    count_correct_gain += 1
                elif actual_output < results[company]['median'] and inputs[company][5]['open'] < inputs[company][4]['open']:
                    count_correct_loss += 1
                else:
                    count_incorrect += 1
        

            print "CURRENT TABS:"
            print "CORRECT GAIN:", count_correct_gain
            print "CORRECT LOSS:", count_correct_loss
            print "CORRECT TOTAL:", count_correct_gain + count_correct_loss
            print "INCORRECT TOTAL:", count_incorrect
            test_results[start_date]["correct_gain"] = count_correct_gain
            test_results[start_date]["correct_loss"] = count_correct_loss
            test_results[start_date]["correct_total"] = count_correct_gain + count_correct_loss
            test_results[start_date]["incorrect_total"] = count_incorrect

        for date in test_results:
            print date, test_results[date]

        print "wtf_count:", count_wtf


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
            if open1 != "Open":
                stock_data[key][date] = {"open":float(open1),
                                        "high":high,
                                        "low":low,
                                        "close":close,
                                        "volume":volume,
                                        "adj_close":adj_close}
            else:
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
