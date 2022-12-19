import sys
import argparse
import dcritsim
import epanet_actions
from csv_writer import CSVWriter

output_file = 'training_data.csv'
LEAK_COEFF = 0.1

def main():
    args = parse()

    project = get_project()
    project.initialize_subsys(input_filename=args.input_filename, hstep=args.hstep, pipe_index=args.pipe)

    project.add_leak()
    results = project.move_leak_along_transect(leak_base=LEAK_COEFF, iterations=args.iter)
    #project.close_hydraulic_solver()
    write_to_csv(results)


def parse():
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', nargs='?', default='net1.inp', help='An EPANET input file describing the system.')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600, help='Hydraulic time step (default 3600s=1h).')
    parser.add_argument('--pipe', metavar='index', type=int, default=2, help='index of pipe to look at (default 2).')
    parser.add_argument('--iter', metavar='number of leakage sizes', type=int, default=1, help='number of leak size iterations (default 1)')
    
    args = parser.parse_args()
    return args

def write_to_csv(results):
    writer = CSVWriter(output_file)
    writer.writeLines(results)
    writer.close()

def get_project():
    #These CANNOT be lumped together in one line for some reason. Don't do it, it messes up everything.
    epanet = dcritsim.epanetwrap.DcritEPANET()
    ph = epanet.get_ph()
    return epanet_actions.ProjectActions(ph)

if __name__ == "__main__":
    sys.exit(main())