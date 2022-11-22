import csv
from matplotlib import pyplot
import argparse
import sys

upstream_pressure = []
downstream_pressure = []
upstream_flow = []
downstream_flow = []

upstream_pressure_deviation_from_mean = []
downstream_pressure_deviation_from_mean = []
flow_differential = []

def main():
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', nargs='?', default='training_data.csv', help='A csv file to graph.')

    args = parser.parse_args()
    global input_file
    input_file = args.input_filename

    read_csv()
    derive_calculations()
    make_plots()


def read_csv():
    list = []

    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter = ',')
        for row in reader:
            list.append(row)
        
    global length
    length = len(list)

    global upstream_total
    global downstream_total
    upstream_total = 0
    downstream_total = 0

    for i in range(1,length):
        upstream_pressure.append(float(list[i][1]))
        downstream_pressure.append(float(list[i][2]))
        upstream_flow.append(float(list[i][3]))
        downstream_flow.append(float(list[i][4]))

        upstream_total = upstream_total + float(list[i][1])
        downstream_total = downstream_total + float(list[i][2])

def derive_calculations():
    upstream_mean = upstream_total/(length - 1)
    downstream_mean = downstream_total/(length - 1)

    for i in range(length - 1):
        upstream_pressure_deviation_from_mean.append(abs(upstream_mean - upstream_pressure[i]))
        downstream_pressure_deviation_from_mean.append(abs(downstream_mean - downstream_pressure[i]))
        flow_differential.append(upstream_flow[i] - downstream_flow[i])

def make_plots():
    x = range(1, length)

    pyplot.scatter(x, upstream_pressure_deviation_from_mean, s=2, c='xkcd:puke green')
    pyplot.scatter(x, downstream_pressure_deviation_from_mean, s=2, c='xkcd:orange')
    pyplot.xlabel('leakage position (unit)')
    pyplot.ylabel('pressure (unit), derivation from mean')
    pyplot.legend(['upsteam node', 'downstream node'])
    pyplot.show()

    pyplot.scatter(x, flow_differential, s=2, c='xkcd:puke green')
    pyplot.xlabel('leakage position (unit)')
    pyplot.ylabel('difference in flow before/after leak (unit)')
    pyplot.show()


if __name__ == "__main__":
    sys.exit(main())