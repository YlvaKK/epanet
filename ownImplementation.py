import sys
import argparse
from epanet import toolkit as epanet_toolkit
import dcritsim
import csv
import faulthandler

output_file='training_data.csv'
LEAK = "leakage_node"
UPSTREAM_PIPE = "upstream_pipe"
DOWNATREAM_PIPE = "downstream_pipe"
LEAK_COEFF = 0.1
LENGTH_STEP = 100
PIPE_LENGTH = 1000
PIPE_DIAM = 100
PIPE_ROUGHNESS = 120
PIPE_MLOSS = 0

pipe_index = 2
leakage_node_index = 0
upstream_pipe_index = 0
downstream_pipe_index = 0
# hej
def main():
    print("INFO: in main")
    faulthandler.enable()

    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', help='An EPANET input file describing the system.')
    parser.add_argument('report_filename', nargs='?', default='', help='Report log file from the simulation run.')
    parser.add_argument('binary_filename', nargs='?', default='', help='Hydraulic analysis results file (binary).')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600, help='Hydraulic time step (default 3600s=1h).')
    parser.add_argument('--pipe', metavar='index', type=int, default=2, help='index of pipe to look at (default 2).')

    epanet = dcritsim.epanetwrap.DcritEPANET()
    #TODO: figure out what ph means
    ph = epanet.get_ph()

    args = parser.parse_args()
    epanet_subsys_init(args, ph)

def epanet_subsys_init(args, ph) -> any:
    print("INFO: in epanet_subsys_init")

    pipe_index = args.pipe

    epanet_toolkit.open(ph, args.input_filename, args.report_filename, args.binary_filename)

    epanet_toolkit.settimeparam(ph, epanet_toolkit.HYDSTEP, args.hstep)
    epanet_toolkit.setstatusreport(ph, epanet_toolkit.NORMAL_REPORT)

    ###########################################
    #       start of add leak
    ###########################################
    epanet_toolkit.deletelink(ph, int(pipe_index), actionCode = epanet_toolkit.UNCONDITIONAL)
    # add lekage node
    leakage_node_index = epanet_toolkit.addnode(ph, LEAK, nodeType= epanet_toolkit.JUNCTION)
    epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value=LEAK_COEFF)

    #get index of surrounding nodes
    upstream_node_index, downstream_node_index = epanet_toolkit.getlinknodes(ph, pipe_index)
    upstream_node_id = epanet_toolkit.getnodeid(ph, upstream_node_index)
    downstream_node_id = epanet_toolkit.getnodeid(ph, downstream_node_index)
    
    # add nya pipes
    #upstream pipe
    upstream_pipe_index = epanet_toolkit.addlink(ph, UPSTREAM_PIPE, epanet_toolkit.PIPE, upstream_node_id,LEAK)
    epanet_toolkit.setpipedata(ph, upstream_pipe_index, length= PIPE_LENGTH/2, diam =100, rough=120, mloss = 0)

    #downstream pipe
    downstream_pipe_index = epanet_toolkit.addlink(ph, DOWNATREAM_PIPE, epanet_toolkit.PIPE, LEAK, downstream_node_id)
    epanet_toolkit.setpipedata(ph, downstream_pipe_index, length= PIPE_LENGTH/2, diam =100, rough=120, mloss = 0)

    ###########################################
    #       start of move_leak
    ###########################################

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        for i in range (1,1000):
            #changing emitter to 5, replacing leak coefficient, why?
            epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value = 5)

            # change length of upstream pipe
            epanet_toolkit.setpipedata(ph, upstream_pipe_index, length = i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
            # change length of downstream pipe
            epanet_toolkit.setpipedata(ph, downstream_pipe_index, length = PIPE_LENGTH-i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
            solveH(ph)

            node1_pressure = epanet_toolkit.getnodevalue(ph, upstream_node_index, property=epanet_toolkit.PRESSURE)
            node2_pressure = epanet_toolkit.getnodevalue(ph, downstream_node_index, property=epanet_toolkit.PRESSURE)

            link1_flow = epanet_toolkit.getlinkvalue(ph, upstream_pipe_index, property=epanet_toolkit.FLOW)
            link2_flow = epanet_toolkit.getlinkvalue(ph, downstream_pipe_index, property=epanet_toolkit.FLOW)

            print('writing row %s to csv' %i)
            writer.writerow([node1_pressure, node2_pressure, link1_flow, link2_flow, i])
        
        
    
def solveH(ph):
    epanet_toolkit.openH(ph)
    epanet_toolkit.initH(ph, epanet_toolkit.SAVE)
    epanet_toolkit.solveH(ph)

def move_leak(ph):
    #TODO: can pipes have length 0? test later change range
    for i in range (1,1000):
        #changing emitter to 5, replacing leak coefficient, why?
        epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value = 5)

        # change length of upstream pipe
        epanet_toolkit.setpipedata(ph, upstream_pipe_index, length = i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
        # change length of downstream pipe
        epanet_toolkit.setpipedata(ph, downstream_pipe_index, length = PIPE_LENGTH-i, diam=PIPE_DIAM, rough=PIPE_ROUGHNESS, mloss=PIPE_MLOSS)
        epanet_toolkit.solveH(ph)
        
        node1_pressure = epanet_toolkit.getnodevalue(ph, upstream_pipe_index, property=epanet_toolkit.PRESSURE)
        node2_pressure = epanet_toolkit.getnodevalue(ph, downstream_pipe_index, property=epanet_toolkit.PRESSURE)

        link1_flow = epanet_toolkit.getlinkvalue(ph, index=2, property=epanet_toolkit.FLOW)
        link2_flow = epanet_toolkit.getlinkvalue(ph, index=3, property=epanet_toolkit.FLOW)

        write_row(node1_pressure, node2_pressure, link1_flow, link2_flow, i)
        
def write_row(p1, p2, f1, f2, p):
    with open(output_file, 'w', newline='') as csvfile:
        #fieldnames = ['upstream_node_pressure', 'downstream_node_pressure', 'upstream_flow', 'downstream_flow', 'leak_position']
        writer = csv.writer(csvfile, delimiter = ',')
        
        #if (p == 1):
        #    writer.writeheader()
        writer.writerow([p1, p2, f1, f2, p])

def get_pressure_data(ph):
    num_nodes = epanet_toolkit.getcount(ph, epanet_toolkit.NODECOUNT)
    num_links = epanet_toolkit.getcount(ph, epanet_toolkit.LINKCOUNT)      
    print(f'num_nodes: {num_nodes}, num_links: {num_links}')

    pressure_diff, length_list = main_net(ph)
    print ('pressure_diff = %s' %pressure_diff)
    print ('length_list = %s' %length_list)

    #TODO: this returns pressure of two nodes when pipe length is 1000, why that length?
    PRESSURE1_org = epanet_toolkit.getnodevalue(ph, index=1, property=epanet_toolkit.PRESSURE)
    PRESSURE2_org = epanet_toolkit.getnodevalue(ph, index=2, property=epanet_toolkit.PRESSURE)
    diff_org = PRESSURE2_org - PRESSURE1_org
    print('PRESSURE1_org=',PRESSURE1_org)
    print('PRESSURE2_org=',PRESSURE2_org)
    print('diff_org=',diff_org)


    x = [5]
    leakage_coefficient = 0.1

    epanet_toolkit.deletelink(ph, index=1, actionCode = epanet_toolkit.UNCONDITIONAL )
    
    # add lekage node
    #TODO: how can we know that the new node has index 3? WHY IS IT HARD CODED GOD
    epanet_toolkit.addnode(ph, "leakage_node", nodeType= epanet_toolkit.JUNCTION)
    leakage_node_index = epanet_toolkit.getnodeindex(ph, "leakage_node")
    epanet_toolkit.setnodevalue(ph, leakage_node_index, property= epanet_toolkit.EMITTER, value=leakage_coefficient)
    
    # add nya pipes
    index = epanet_toolkit.addlink(ph, "upstream_pipe", epanet_toolkit.PIPE, "2","leakage_node")
    error = epanet_toolkit.setpipedata(ph, index=2, length= 500, diam =100, rough=120,mloss = 0)

    index2 = epanet_toolkit.addlink(ph, "downstream_pipe", epanet_toolkit.PIPE,"leakage_node","3")
    error2 = epanet_toolkit.setpipedata(ph, index=3, length= 500, diam =100, rough=120,mloss = 0)
    
def main_net (ph):

    inc = 0
    length_list = []
    pressure_diff = []

    #TODO: why lenth in steps of 100, irrespective of original length?
    for i in range(0,10):
        """inc += LENGTH_STEP
        epanet_toolkit.setlinkvalue(ph, pipe_index, property=epanet_toolkit.LENGTH,value=inc)
        length = epanet_toolkit.getlinkvalue(ph, pipe_index, property=epanet_toolkit.LENGTH)
        length_list.append(length)"""
        epanet_toolkit.solveH(ph)
        
        #returns index of both nodes surrounding link
        """nodes = epanet_toolkit.getlinknodes(ph, pipe_index)
        up_node_index = nodes[0]
        down_node_index = nodes[1]
        print ("upstream node index: %s" %up_node_index)
        print ("downstream node index: %s" %down_node_index)
        

        #TODO: hardcodes different nodes than those already found, why? (originally 1 and 2, testing fix rn)
        upstream_pressure = epanet_toolkit.getnodevalue(ph, up_node_index, property=epanet_toolkit.PRESSURE)
        downstream_pressure = epanet_toolkit.getnodevalue(ph, down_node_index, property=epanet_toolkit.PRESSURE)

        pressure_diff.append(downstream_pressure - upstream_pressure)

    return pressure_diff, length_list"""


if __name__ == "__main__":
    sys.exit(main())