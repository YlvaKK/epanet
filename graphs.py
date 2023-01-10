from matplotlib import pyplot
from graph_tools import CSVReader
import numpy
import sys

colours = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']


def main():
    with_elevation = get_data('example_outputs/training_data_05_with_elev.csv')
    without_elevation = get_data('example_outputs/training_data_05_without_elev.csv')
    two_leaks_1_foot = get_data('example_outputs/training_data_025_2leaks_with_elevation.csv')
    two_leaks_10_feet = get_data('example_outputs/training_data_025_2leaks_10step_with_elev.csv')
    two_leaks_100_feet = get_data('example_outputs/training_data_025_2leaks_100feet.csv')
    two_leaks_1000_feet = get_data('example_outputs/training_data_025_2leaks_1000.csv')
    ten_sizes = get_data('example_outputs/training_data_ten_sizes.csv')

    with_and_without_elevation(with_elevation, without_elevation)
    one_or_two_leaks(with_elevation, two_leaks_1_foot)
    long_or_short_distance(two_leaks_1_foot, two_leaks_10_feet, two_leaks_100_feet, two_leaks_1000_feet)
    many_sizes(ten_sizes)


def get_data(filename):
    read = CSVReader(filename)
    read.read_multiple()
    datasets = read.data

    for dataset in datasets:
        dataset.derive_calculations()

    return datasets


def with_and_without_elevation(data1, data2):
    make_plot([data1[0].location, data1[0].location, data2[0].location, data2[0].location],
              [data1[0].upstream_pressure_deviation_from_mean, data1[0].downstream_pressure_deviation_from_mean,
               data2[0].upstream_pressure_deviation_from_mean, data2[0].downstream_pressure_deviation_from_mean],
              'Leakage position from start of pipe (feet)',
              'Pressure (psi), derivation from mean',
              ['With elevation, upstream node', 'With elevation, downstream node',
               'Without elevation, upstream node', 'Without elevation, downstream node'])

    make_plot([data1[0].location, data2[0].location],
              [data1[0].pressure_differential, data2[0].pressure_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in pressure before/after leak (psi)',
              ['With elevation', 'Without elevation'])

    make_plot([data1[0].location, data2[0].location],
              [data1[0].flow_differential, data2[0].flow_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in flow before/after leak (gpm)', ['with elevation', 'without elevation'], '')


def one_or_two_leaks(data1, data2):
    make_plot([data1[0].location, data1[0].location, data2[0].location, data2[0].location],
              [data1[0].upstream_pressure_deviation_from_mean, data1[0].downstream_pressure_deviation_from_mean,
               data2[0].upstream_pressure_deviation_from_mean, data2[0].downstream_pressure_deviation_from_mean],
              'Leakage position from start of pipe (feet)',
              'Pressure (psi), derivation from mean',
              ['one leak, upstream', 'one leak, downstream', 'two leaks, upstream', 'two leaks, downstream'])

    make_plot([data1[0].location, data2[0].location],
              [data1[0].pressure_differential, data2[0].pressure_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in pressure before/after leak (psi)',
              ['One leak (leak coefficient 0.5)', 'Two leaks (leak coefficient 0.25)'])

    make_plot([data1[0].location, data2[0].location],
              [data1[0].flow_differential, data2[0].flow_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in flow before/after leak (gpm)',
              ['One leak (leak coefficient 0.5)', 'Two leaks (leak coefficient 0.25)'])


def long_or_short_distance(data1, data2, data3, data4):
    make_plot([data1[0].location, data2[0].location, data3[0].location, data4[0].location],
              [data1[0].pressure_differential, data2[0].pressure_differential,
               data3[0].pressure_differential, data4[0].pressure_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in pressure before/after leak (psi)',
              ['1 foot', '10 feet', '100 feet', '1000 feet'])

    make_plot([data1[0].location, data2[0].location, data3[0].location, data4[0].location],
              [data1[0].flow_differential, data2[0].flow_differential,
               data3[0].flow_differential, data4[0].flow_differential],
              'Leakage position from start of pipe (feet)',
              'Difference in flow before/after leak (gpm)',
              ['1 foot', '10 feet', '100 feet', '1000 feet'])


def many_sizes(data):
    numsizes = len(data)
    numdatapoints = data[2].length

    x = [range(numdatapoints)] * numsizes
    y_upstream_p = []
    y_downstream_p = []
    y_pressure_diff = []
    y_flow_diff = []
    for i in range(numsizes):
        y_upstream_p.append(data[i].upstream_pressure)
        y_downstream_p.append(data[i].downstream_pressure)
        y_pressure_diff.append(data[i].pressure_differential)
        y_flow_diff.append(data[i].flow_differential)
    xlabel = 'Leakage position from start of pipe (feet)'
    ylabel_p = 'Pressure (psi), derivation from mean'
    ylabel_pdiff = 'Difference in pressure before/after leak (psi)'
    ylabel_f = 'Difference in flow before/after leak (gpm)'
    legend = numpy.arange(0.1, 1.1, 0.1)
    legend = numpy.around(legend, decimals=1)
    title_up_p = 'Upstream pressure over several leak sizes'
    title_down_p = 'Downstream pressure over several leak sizes'

    make_plot(x, y_upstream_p, xlabel, ylabel_p, legend, title_up_p)
    make_plot(x, y_downstream_p, xlabel, ylabel_p, legend, title_down_p)
    make_plot(x, y_pressure_diff, xlabel, ylabel_pdiff, legend)
    make_plot(x, y_flow_diff, xlabel, ylabel_f, legend)


def make_plot(x, y, xlabel, ylabel, legend, title='', top=0.0):
    for i in range(len(x)):
        pyplot.scatter(x[i], y[i], s=2, c='tab:%s' % colours[i])

    if top == 0:
        bottom, top = pyplot.ylim()

    pyplot.ylim(top=top)
    pyplot.xlabel(xlabel)
    pyplot.ylabel(ylabel)
    pyplot.legend(legend)
    pyplot.title(title)
    pyplot.show()


if __name__ == "__main__":
    sys.exit(main())
