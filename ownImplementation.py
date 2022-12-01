import sys
import argparse
from epanet import toolkit as epanet_toolkit
import dcritsim
import csv
import math

output_file='training_data.csv'
LEAK = "leakage_node"
UPSTREAM_PIPE = "upstream_pipe"
DOWNATREAM_PIPE = "downstream_pipe"
LEAK_COEFF = 0.1
#LENGTH_STEP = 100
#PIPE_LENGTH = 1000
PIPE_DIAM = 100
PIPE_ROUGHNESS = 120
PIPE_MLOSS = 0

FLOW_UNITS = ['cfs', 'gpm', 'mgd', 'imgd', 'afd', 'lps', 'lpm', 'mld', 'cmh', 'cmd']

upstream_node_pressure = []
downstream_node_pressure = []
upstream_pipe_flow = []
downstream_pipe_flow = []

#TODO: hantera enheter! olika inp-filer kan ha olika enheter!!!!!!!

def main():
    print("INFO: in main")
    #parse all arguments
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', help='An EPANET input file describing the system.')
    parser.add_argument('report_filename', nargs='?', default='', help='Report log file from the simulation run.')
    parser.add_argument('binary_filename', nargs='?', default='', help='Hydraulic analysis results file (binary).')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600, help='Hydraulic time step (default 3600s=1h).')
    parser.add_argument('--pipe', metavar='index', type=int, default=2, help='index of pipe to look at (default 2).')

    #gets epanet sim project from dcritsim
    epanet = dcritsim.epanetwrap.DcritEPANET()
    global ph
    ph = epanet.get_ph()

    #initialize subsys
    args = parser.parse_args()
    global pipe_index 
    pipe_index = args.pipe

    #unpack args and initialize water distribution 
    initialize_subsys(args)

    add_leak() #replaces a pipe with a leakage suite
    move_leak() #moves leak along pipe and records pressure and flow
    #write_to_csv() #outputs data to csv file


def initialize_subsys(args):
    epanet_toolkit.open(ph, args.input_filename, args.report_filename, args.binary_filename)
    epanet_toolkit.settimeparam(ph, epanet_toolkit.HYDSTEP, args.hstep)
    epanet_toolkit.setstatusreport(ph, epanet_toolkit.NORMAL_REPORT)
    check_units()

def check_units():
    flow_units = epanet_toolkit.getflowunits(ph)
    if (flow_units != epanet_toolkit.GPM):
        raise Exception("input file must use GPM as flow unit")

def add_leak():
    global pipe_length

    global upstream_node_elevation
    global downstream_node_elevation

    global angle
    global upper_elevation

    global leakage_node_index
    global upstream_node_index
    global downstream_node_index
    global upstream_pipe_index
    global downstream_pipe_index

    #get index of nodes surrounding original pipe
    upstream_node_index, downstream_node_index = epanet_toolkit.getlinknodes(ph, pipe_index)

    #save useful global variables
    pipe_length = epanet_toolkit.getlinkvalue(ph, pipe_index, epanet_toolkit.LENGTH)
    
    angle, upper_elevation = get_pipe_angle(upstream_node_index, downstream_node_index)
    print("angle: %s, upper elevation: %s" %(angle, upper_elevation))

    #remove original pipe
    epanet_toolkit.deletelink(ph, pipe_index, actionCode = epanet_toolkit.UNCONDITIONAL)

    #add lekage node (as of yet unmoored)
    leakage_node_index = epanet_toolkit.addnode(ph, LEAK, nodeType= epanet_toolkit.JUNCTION)
    epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value=LEAK_COEFF)
    
    # create new pipes and connect them to leakage node, surrounding nodes
    upstream_pipe_index = make_pipe(UPSTREAM_PIPE, epanet_toolkit.getnodeid(ph, upstream_node_index), LEAK)
    downstream_pipe_index = make_pipe(DOWNATREAM_PIPE, LEAK, epanet_toolkit.getnodeid(ph, downstream_node_index))


def make_pipe(id, node1, node2):
    pipe_index = epanet_toolkit.addlink(ph, id, epanet_toolkit.PIPE, node1, node2)
    epanet_toolkit.setpipedata(ph, pipe_index, length = 1, diam = PIPE_DIAM, rough = PIPE_ROUGHNESS, mloss = PIPE_MLOSS)

    return pipe_index


def move_leak():
    for i in range(1, round(pipe_length)):
        # change length of pipes surrounding leak
        epanet_toolkit.setpipedata(ph, upstream_pipe_index, length = i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
        epanet_toolkit.setpipedata(ph, downstream_pipe_index, length = round(pipe_length)-i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)

        if (waterRunsUphill):
            distance_from_top = round(pipe_length) - i
        else:
            distance_from_top = i

        leak_elevation = calculate_leak_elevation(upper_elevation, angle, distance_from_top)

        epanet_toolkit.setnodevalue(ph, leakage_node_index, epanet_toolkit.ELEVATION, leak_elevation)

        #run simulation
        run_hydraulic_solver()
        
        # record pressure and flow
        upstream_node_pressure.append(epanet_toolkit.getnodevalue(ph, upstream_node_index, property=epanet_toolkit.PRESSURE))
        downstream_node_pressure.append(epanet_toolkit.getnodevalue(ph, downstream_node_index, property=epanet_toolkit.PRESSURE))
        upstream_pipe_flow.append(epanet_toolkit.getlinkvalue(ph, upstream_pipe_index, property=epanet_toolkit.FLOW))
        downstream_pipe_flow.append(epanet_toolkit.getlinkvalue(ph, downstream_pipe_index, property=epanet_toolkit.FLOW))

def get_pipe_angle(upstream_index, downstream_index):
    upper_elevation, elevation_diff = find_upper_node(upstream_index, downstream_index)
    
    angle = math.asin(elevation_diff/pipe_length)
    return angle, upper_elevation

def find_upper_node(upstream_index, downstream_index):
    upstream_node_elevation = epanet_toolkit.getnodevalue(ph, upstream_index, epanet_toolkit.ELEVATION)
    downstream_node_elevation = epanet_toolkit.getnodevalue(ph, downstream_index, epanet_toolkit.ELEVATION)

    elevation_diff = upstream_node_elevation - downstream_node_elevation;

    global waterRunsUphill
    if (elevation_diff < 0):
        waterRunsUphill = True
        upper_elevation = downstream_node_elevation
        elevation_diff = abs(elevation_diff)
    else:
        waterRunsUphill = False
        upper_elevation = upstream_node_elevation

    return upper_elevation, elevation_diff

def calculate_leak_elevation(upper_elevation, angle, length_from_upper):
    elevation_diff_from_upper_elevation = math.sin(angle) * length_from_upper
    return upper_elevation - elevation_diff_from_upper_elevation
    

def run_hydraulic_solver():
    epanet_toolkit.openH(ph)
    epanet_toolkit.initH(ph, epanet_toolkit.SAVE)
    epanet_toolkit.solveH(ph)
        

def write_to_csv():
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['leakage_position (foot)', 'upstream_pressure (psi)', 'downstream_pressure (psi)', 'upstream_flow (gpm)', 'downstream_flow (gpm)']
        writer = csv.DictWriter(csvfile, delimiter = ',', fieldnames=fieldnames)
        writer.writeheader()

        for i in range(round(pipe_length) - 1):
            writer.writerow(
                {fieldnames[0]: i, 
                fieldnames[1]: upstream_node_pressure[i], 
                fieldnames[2]: downstream_node_pressure[i], 
                fieldnames[3]: upstream_pipe_flow[i], 
                fieldnames[4]: downstream_pipe_flow[i]}
                )

if __name__ == "__main__":
    sys.exit(main())