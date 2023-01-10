import csv

upstream_pressure_deviation_from_mean = []
downstream_pressure_deviation_from_mean = []
flow_differential = []


class CSVReader:
    input_file = None
    data = None

    def __init__(self, input_file):
        self.input_file = input_file

    def get_input(self):
        input_list = []
        with open(self.input_file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                input_list.append(row)
        return input_list

    def read_multiple(self):
        input_list = self.get_input()

        columns = len(input_list[2])
        multiples = columns // 4
        self.data = []

        for i in range(multiples):
            data = Data()

            for j in range(2, len(input_list)):
                data.clear_location
                data.add_line(float(input_list[j][1 + i*4]), float(input_list[j][2 + i*4]),
                              float(input_list[j][3 + i*4]), float(input_list[j][4 + i*4]), float(input_list[j][0]))
            self.data.append(data)


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
        self.location = []
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
        self.pressure_differential = []

    def add_line(self, up_p, down_p, up_f, down_f, location):
        self.upstream_pressure.append(up_p)
        self.downstream_pressure.append(down_p)
        self.upstream_flow.append(up_f)
        self.downstream_flow.append(down_f)
        self.location.append(location)

        self.upstream_total = self.upstream_total + up_p
        self.downstream_total = self.downstream_total + down_p

        self.length += 1

    def clear_location(self):
        self.location.clear()

    def upstream_mean(self):
        return self.upstream_total / self.length

    def downstream_mean(self):
        return self.downstream_total / self.length

    def derive_calculations(self):
        for i in range(self.length):
            self.upstream_pressure_deviation_from_mean.append(abs(self.upstream_mean() - self.upstream_pressure[i]))
            self.downstream_pressure_deviation_from_mean.append(
                abs(self.downstream_mean() - self.downstream_pressure[i]))
            self.flow_differential.append(self.upstream_flow[i] - self.downstream_flow[i])
            self.pressure_differential.append(self.upstream_pressure[i] - self.downstream_pressure[i])
