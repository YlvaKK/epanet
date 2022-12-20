import csv
from matplotlib import pyplot
import argparse
import sys

upstream_pressure_deviation_from_mean = []
downstream_pressure_deviation_from_mean = []
flow_differential = []


def main():
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', nargs='?', default='training_data.csv', help='A csv file to graph.')

    args = parser.parse_args()
    input_file = args.input_filename

    reader = CSVReader(input_file)
    reader.read()
    reader.data.derive_calculations()
    make_plots(reader.data)


class CSVReader:
    input_file = None
    data = None

    def __init__(self, input_file):
        self.input_file = input_file
        self.data = Data()

    def read(self):
        input_list = self.get_input()
        self.get_totals(input_list)

    def get_input(self):
        input_list = []
        with open(self.input_file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                input_list.append(row)
        return input_list

    def get_totals(self, input_list):
        for i in range(2, len(input_list)):
            self.data.add_line(float(input_list[i][1]), float(input_list[i][2]),
                               float(input_list[i][3]), float(input_list[i][4]))


class Data:
    upstream_pressure = None
    downstream_pressure = None
    upstream_flow = None
    downstream_flow = None
    upstream_total = None
    downstream_total = None
    length = None
    upstream_pressure_deviation_from_mean = None
    downstream_pressure_deviation_from_mean = None
    flow_differential = None

    def __init__(self):
        self.upstream_pressure = []
        self.downstream_pressure = []
        self.upstream_flow = []
        self.downstream_flow = []
        self.upstream_total = 0
        self.downstream_total = 0
        self.length = 0
        self.upstream_pressure_deviation_from_mean = []
        self.downstream_pressure_deviation_from_mean = []
        self.flow_differential = []

    def add_line(self, up_p, down_p, up_f, down_f):
        self.upstream_pressure.append(up_p)
        self.downstream_pressure.append(down_p)
        self.upstream_flow.append(up_f)
        self.downstream_flow.append(down_f)

        self.upstream_total = self.upstream_total + up_p
        self.downstream_total = self.downstream_total + down_p

        self.length += 1

    def upstream_mean(self):
        return self.upstream_total / self.length

    def downstream_mean(self):
        return self.downstream_total / self.length

    def derive_calculations(self):
        print('appending the stuff')
        for i in range(self.length):
            self.upstream_pressure_deviation_from_mean.append(abs(self.upstream_mean() - self.upstream_pressure[i]))
            self.downstream_pressure_deviation_from_mean.append(
                abs(self.downstream_mean() - self.downstream_pressure[i]))
            self.flow_differential.append(self.upstream_flow[i] - self.downstream_flow[i])


def make_plots(data):
    x = range(data.length)
    print('x len={}, y={}'.format(data.length, len(data.upstream_pressure_deviation_from_mean)))

    """pyplot.scatter(x, upstream_pressure, s=2, c='xkcd:puke green')
    pyplot.scatter(x, downstream_pressure, s=2, c='xkcd:orange')
    pyplot.xlabel('leakage distance from start of pipe (feet)')
    pyplot.ylabel('pressure (psi)')
    pyplot.legend(['pressure in upsteam node', 'pressure in downstream node'])
    pyplot.show()"""

    pyplot.scatter(x, data.upstream_pressure_deviation_from_mean, s=2, c='xkcd:puke green')
    pyplot.scatter(x, data.downstream_pressure_deviation_from_mean, s=2, c='xkcd:orange')
    pyplot.xlabel('leakage position from start (feet)')
    pyplot.ylabel('pressure (psi), derivation from mean')
    pyplot.legend(['upstream node', 'downstream node'])
    pyplot.show()

    pyplot.scatter(x, data.flow_differential, s=2, c='xkcd:puke green')
    pyplot.xlabel('leakage position (feet)')
    pyplot.ylabel('difference in flow before/after leak (gpm)')
    pyplot.show()


if __name__ == "__main__":
    sys.exit(main())
