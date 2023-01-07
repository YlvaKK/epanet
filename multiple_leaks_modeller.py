import sys
import argparse
import dcritsim
import epanet_actions
from csv_writer import CSVWriter

output_file = 'training_data.csv'
LEAK_COEFF = 0.25
use_elev = True


def main():
    args = parse()

    # do NOT under any circumstances try to move these three lines to a function. everything breaks.
    epanet = dcritsim.epanetwrap.DcritEPANET()
    ph = epanet.get_ph()
    project = epanet_actions.ProjectActions(ph, use_elev)

    project.initialize_subsys(args)
    project.add_leakage_suite()
    results = project.move_several_leaks_along_transect(leak_coeff=LEAK_COEFF)
    write_to_csv(results)


def parse():
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', nargs='?', default='net1.inp',
                        help='An EPANET input file describing the system.')
    parser.add_argument('report_filename', nargs='?', default='', help='Report log file from the simulation run.')
    parser.add_argument('binary_filename', nargs='?', default='', help='Hydraulic analysis results file (binary).')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600,
                        help='Hydraulic time step (default 3600s=1h).')
    parser.add_argument('--pipe', metavar='unitless', type=int, default=2, help='index of pipe to look at (default 2).')
    parser.add_argument('--lstep', metavar='length unit', type=int, default=1,
                        help='Distance between leaks (default 1)')
    parser.add_argument('--nleaks', metavar='unitless', type=int, default=1,
                        help='Number of leaks (default 2)')

    args = parser.parse_args()
    return args


def write_to_csv(results):
    writer = CSVWriter(output_file)
    writer.write_lines(results)
    writer.close()


if __name__ == "__main__":
    sys.exit(main())