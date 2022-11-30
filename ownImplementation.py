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
    #move_leak() #moves leak along pipe and records pressure and flow
    #write_to_csv() #outputs data to csv file


def initialize_subsys(args):
    epanet_toolkit.open(ph, args.input_filename, args.report_filename, args.binary_filename)
    epanet_toolkit.settimeparam(ph, epanet_toolkit.HYDSTEP, args.hstep)
    epanet_toolkit.setstatusreport(ph, epanet_toolkit.NORMAL_REPORT)
    getUnits()

def getUnits():
    global flow_unit
    global pressure_unit
    global length_unit
    global pipe_diameter_unit
    global roughness_unit
    global is_metric

    units = epanet_toolkit.getflowunits(ph)
    flow_unit = FLOW_UNITS[units]

    if units == epanet_toolkit.CFS or units == epanet_toolkit.GPM or units == epanet_toolkit.MGD or units == epanet_toolkit.IMGD or units == epanet_toolkit.AFD:
        is_metric = False
        pressure_unit = "psi"
        length_unit = "foot"
        pipe_diameter_unit = "inch"
        roughness_unit = "Darcy-Weisbach / 10^(-3)foot"
    elif units == epanet_toolkit.LPS or units == epanet_toolkit.LPM or units == epanet_toolkit.MLD or units == epanet_toolkit.CMH or units == epanet_toolkit.CMD:
        is_metric = True
        pressure_unit = "meter" #ACCORDING TO EPANET DOCUMENTATION! I KNOW THIS IS NOT A REAL PRESSURE UNIT
        length_unit = "meter"
        pipe_diameter_unit = "millimeter"
        roughness_unit = "Darcy-Weisbach / millimeter"
    else:
        raise Exception("system does not have units?? flow unit is %s" %units)


def add_leak():
    global pipe_length

    global upstream_node_elevation
    global downstream_node_elevation
    global upper_angle

    global leakage_node_index
    global upstream_node_index
    global downstream_node_index
    global upstream_pipe_index
    global downstream_pipe_index

    #get index of nodes surrounding original pipe
    upstream_node_index, downstream_node_index = epanet_toolkit.getlinknodes(ph, pipe_index)
    upstream_node_id = epanet_toolkit.getnodeid(ph, upstream_node_index)
    downstream_node_id = epanet_toolkit.getnodeid(ph, downstream_node_index)

    #save useful global variables
    pipe_length = epanet_toolkit.getlinkvalue(ph, pipe_index, epanet_toolkit.LENGTH)
    upstream_node_elevation = epanet_toolkit.getnodevalue(ph, upstream_node_index, epanet_toolkit.ELEVATION)
    downstream_node_elevation = epanet_toolkit.getnodevalue(ph, downstream_node_index, epanet_toolkit.ELEVATION)
    
    upper_angle = get_pipe_angle()

    #remove original pipe
    epanet_toolkit.deletelink(ph, pipe_index, actionCode = epanet_toolkit.UNCONDITIONAL)

    #add lekage node (as of yet unmoored)
    leakage_node_index = epanet_toolkit.addnode(ph, LEAK, nodeType= epanet_toolkit.JUNCTION)
    epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value=LEAK_COEFF)
    
    # create new pipes and connect them to leakage node, surrounding nodes
    upstream_pipe_index = make_pipe(UPSTREAM_PIPE, upstream_node_id, LEAK)
    downstream_pipe_index = make_pipe(DOWNATREAM_PIPE, LEAK, downstream_node_id)


def make_pipe(id, node1, node2):
    pipe_index = epanet_toolkit.addlink(ph, id, epanet_toolkit.PIPE, node1, node2)
    epanet_toolkit.setpipedata(ph, pipe_index, length = 1, diam = PIPE_DIAM, rough = PIPE_ROUGHNESS, mloss = PIPE_MLOSS)

    return pipe_index


def move_leak():
    for i in range(1, round(pipe_length)):
        # change length of pipes surrounding leak
        epanet_toolkit.setpipedata(ph, upstream_pipe_index, length = i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
        epanet_toolkit.setpipedata(ph, downstream_pipe_index, length = round(pipe_length)-i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)

        leak_elevation = calculate_leak_elevation(upstream_node_elevation, upper_angle, i)
        epanet_toolkit.setnodevalue(ph, leakage_node_index, epanet_toolkit.ELEVATION, leak_elevation)
        print("leak elev: %s" %leak_elevation)

        #run simulation
        run_hydraulic_solver()
        
        # record pressure and flow
        upstream_node_pressure.append(epanet_toolkit.getnodevalue(ph, upstream_node_index, property=epanet_toolkit.PRESSURE))
        downstream_node_pressure.append(epanet_toolkit.getnodevalue(ph, downstream_node_index, property=epanet_toolkit.PRESSURE))
        upstream_pipe_flow.append(epanet_toolkit.getlinkvalue(ph, upstream_pipe_index, property=epanet_toolkit.FLOW))
        downstream_pipe_flow.append(epanet_toolkit.getlinkvalue(ph, downstream_pipe_index, property=epanet_toolkit.FLOW))

def get_pipe_angle():
    #assume upstream has higher elevation for now
    total_elevation_diff = upstream_node_elevation - downstream_node_elevation
    ground_diff = math.sqrt(math.pow(pipe_length, 2) - math.pow(total_elevation_diff, 2))

    upper_angle = math.asin(ground_diff / pipe_length)

    print("elev_diff: %s, upper_angle: %s" %(total_elevation_diff, upper_angle))
    return upper_angle

def calculate_leak_elevation(upper_elevation, upper_angle, length_from_top):
    height_diff = length_from_top * upper_angle
    print("elevation diff from top to leak: %s, elevation of leak: %s" %(height_diff, upper_elevation - height_diff))
    return upper_elevation - height_diff
    

def run_hydraulic_solver():
    epanet_toolkit.openH(ph)
    epanet_toolkit.initH(ph, epanet_toolkit.SAVE)
    epanet_toolkit.solveH(ph)
        

def write_to_csv():
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['leakage_position (%s)' %length_unit, 'upstream_pressure (%s)' %pressure_unit, 'downstream_pressure (%s)' %pressure_unit, 'upstream_flow (%s)' %flow_unit, 'downstream_flow (%s)' %flow_unit]
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