import sys
import argparse
from epanet import toolkit as epanet_toolkit
import dcritsim

LENGTH_STEP = 100

pipe_index = 2
up_node_index = 0
down_node_index = 0

def main():
    print("INFO: in main")
    #ylvas kommentar
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename', help='An EPANET input file describing the system.')
    parser.add_argument('report_filename', nargs='?', default='', help='Report log file from the simulation run.')
    parser.add_argument('binary_filename', nargs='?', default='', help='Hydraulic analysis results file (binary).')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600, help='Hydraulic time step (default 3600s=1h).')
    parser.add_argument('--pipe', metavar='index', type=int, default=2, help='index of pipe to look at (default 2).')

    args = parser.parse_args()
    epanet_subsys_init(args)

def epanet_subsys_init(args):
    print("INFO: in epanet_subsys_init")
    epanet = dcritsim.epanetwrap.DcritEPANET()

    #TODO: figure out what ph means
    ph = epanet.get_ph()

    epanet_toolkit.open(ph, args.input_filename, args.report_filename, args.binary_filename)
    epanet_toolkit.openH(ph)
    pipe_index = args.pipe

    #getting time step from network
    #TODO: testa att kommentera ut detta när koden funkar, borde inte göra något?
    timestep = epanet_toolkit.gettimeparam(ph, epanet_toolkit.HYDSTEP)

    #getting time step from user or default to overwrite
    timestep = args.hstep
    epanet_toolkit.settimeparam(ph, epanet_toolkit.HYDSTEP, timestep)

    epanet_toolkit.setstatusreport(ph, epanet_toolkit.NORMAL_REPORT)
    epanet_toolkit.initH(ph, epanet_toolkit.SAVE)

    get_pressure_data(ph)
    #model_leakage(ph)

def get_pressure_data(ph):
    num_nodes = epanet_toolkit.getcount(ph, epanet_toolkit.NODECOUNT)
    num_links = epanet_toolkit.getcount(ph, epanet_toolkit.LINKCOUNT)      
    print(f'num_nodes: {num_nodes}, num_links: {num_links}')

    pressure_diff, length_list = main_net(ph)
    print ('pressure_diff = %s' %pressure_diff)
    print ('length_list = %s' %length_list)

    #TODO: this returns pressure of two nodes when pipe length is 1000, why that length?
    #changed indices from origonal 1 and 2
    PRESSURE1_org = epanet_toolkit.getnodevalue(ph, index=1, property=epanet_toolkit.PRESSURE)
    PRESSURE2_org = epanet_toolkit.getnodevalue(ph, index=2, property=epanet_toolkit.PRESSURE)
    diff_org = PRESSURE2_org - PRESSURE1_org
    print('PRESSURE1_org=',PRESSURE1_org)
    print('PRESSURE2_org=',PRESSURE2_org)
    print('diff_org=',diff_org)

#TODO:this is the bit that contains all the errors!!!!! wow!
""" def model_leakage(ph):
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
    
    #v1 = epanet_toolkit.getlinkvalue(ph, index=2,property= epanet_toolkit.LENGTH)
    #v2 = epanet_toolkit.getlinkvalue(ph, index=3,property= epanet_toolkit.LENGTH) """


def main_net (ph):
    inc = 0
    length_list = []
    pressure_diff = []

    #TODO: why lenth in steps of 100, irrespective of original length?
    for i in range(0,10):
        inc += LENGTH_STEP
        epanet_toolkit.setlinkvalue(ph, pipe_index, property=epanet_toolkit.LENGTH,value=inc)
        length = epanet_toolkit.getlinkvalue(ph, pipe_index, property=epanet_toolkit.LENGTH)
        length_list.append(length)
        epanet_toolkit.solveH(ph)
        
        #returns index of both nodes surrounding link
        nodes = epanet_toolkit.getlinknodes(ph, pipe_index)
        up_node_index = nodes[0]
        down_node_index = nodes[1]
        print ("upstream node index: %s" %up_node_index)
        print ("downstream node index: %s" %down_node_index)
        

        #TODO: hardcodes different nodes than those already found, why? (originally 1 and 2, testing fix rn)
        upstream_pressure = epanet_toolkit.getnodevalue(ph, up_node_index, property=epanet_toolkit.PRESSURE)
        downstream_pressure = epanet_toolkit.getnodevalue(ph, down_node_index, property=epanet_toolkit.PRESSURE)

        pressure_diff.append(downstream_pressure - upstream_pressure)

    return pressure_diff, length_list

if __name__ == "__main__":
    sys.exit(main())