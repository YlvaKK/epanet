#!/usr/bin/env python3

import sys
import argparse
from epanet import toolkit as en
import dcritsim
# import csv
import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns 
# from sklearn.preprocessing import StandardScaler
# from sklearn.decomposition import PCA
# import numpy as np
# from sklearn.manifold import MDS
# import matplotlib.patches as mpatches
# from matplotlib.legend_handler import HandlerLine2D
# from sklearn.decomposition import PCA
# from sklearn.model_selection import train_test_split
# import random
import xlwt
# from keras.models import Sequential
# from keras.layers import Dense
# from keras.wrappers.scikit_learn import KerasRegressor

utfil='Training_data.xls'
Open=True

def main_net (ph):
    length_list = []
    Head1_list = []
    Head2_list=[]
    emitter_list = []
    initqual_list = []
    tank_level_list = []
    print ('#'*100)
    inc = 0 
    for length in range(1,11):
        
        en.setlinkvalue(ph, index=2, property=en.LENGTH,value=inc+100)
        lengt = en.getlinkvalue(ph, index=2, property=en.LENGTH)
        length_list.append(lengt)
        inc+=100
        en.solveH(ph)
        
        nodes = en.getlinknodes(ph, index=2)
        print (nodes[0])
        print (nodes[1])
        PRESSURE1 = en.getnodevalue(ph, index=1, property=en.PRESSURE)
        PRESSURE2 = en.getnodevalue(ph, index=2, property=en.PRESSURE)
        Head1_list.append(PRESSURE1)
        Head2_list.append(PRESSURE2)
        
    
    #print ('length_list=',length_list)
    #print ('')
    #print ('Head1_list=',Head1_list)
    #print ('')
    #print ('Head2_list=',Head2_list)
    #print ('')
    #print ('length_list=',length_list[0])
    #print ('len(length_list)=',len(length_list))

    head_diff = []

    for i in range(len(length_list)):
        diff = Head2_list[i] - Head1_list[i]
        head_diff.append(diff)

    return head_diff, length_list
    

def get_column(col1):
    col = col1
    data_ = []
    for i in range(len(col)):
            y= float(col[i])
            data_.append(y)
    return data_


def epanet_subsys_init(args):
    epanet = dcritsim.epanetwrap.DcritEPANET()

    ph = epanet.get_ph()

    en.open(ph, args.input_filename, args.report_filename, args.binary_filename)

    # Opens a project's hydraulic solver, prior to running the first hydraulic analysis
    # using the EN_initH - EN_runH - EN_nextH sequence. Multiple analyses can be made before
    # calling EN_closeH to close the hydraulic solver.
    en.openH(ph)

    ## Set time step
    ## https://epanetjs.com/api/project-functions/enumerated-types/#timeparameter
    hstep = en.gettimeparam(ph, en.HYDSTEP)      # first we need to get Hydraulic time step (HYDSTEP) from the network
    print(f'Hydraulic time step was: {hstep}', end='')

    hstep = args.hstep  # get Hydraulic time step from input user
    en.settimeparam(ph, en.HYDSTEP, hstep) # set the input Hydraulic time step to network 
    print(f', setting to: {hstep}')

    ## Other initialisation
    # 1- Sets the level of hydraulic status reporting (setStatusReport)
    #    Status reporting writes changes in the hydraulics status of network
    #    elements to a project's report file as a hydraulic simulation unfolds.
    #    There are three levels of reporting:
    #           a) StatusReport.NoReport (no status reporting)
    #           b) StatusReport.NormalReport (normal reporting)
    #           c) StatusReport.FullReport (full status reporting).

    en.setstatusreport(ph, en.NORMAL_REPORT)

    # 2- Initializes a network prior to running a hydraulic analysis (initH)
    #    This function initializes storage tank levels, link status and settings,
    #    and the simulation time clock prior to running a hydraulic analysis.
    #    en.SAVE= 1 means save to a temporary binary hydraulics file , 0 means not save 
    en.initH(ph, en.SAVE)
    #en.setreport(ph, 'NODES ALL')
    #en.setreport(ph, 'LINKS ALL')
    #en.settimeparam(ph, en.REPORTSTEP, 600)
    num_nodes = en.getcount(ph, en.NODECOUNT)
    link_count = en.getcount(ph, en.LINKCOUNT)      
    print(f'num_nodes: {num_nodes}, link count: {link_count}')
    
    head_diff, length_list = main_net(ph)
    print ('head_diff=',head_diff)
    print ('')
    print ('length_list=',length_list)

    PRESSURE1_org = en.getnodevalue(ph, index=1, property=en.PRESSURE)
    PRESSURE2_org = en.getnodevalue(ph, index=2, property=en.PRESSURE)
    diff_org = PRESSURE2_org - PRESSURE1_org
    print ('PRESSURE1_org=',PRESSURE1_org)
    print ('PRESSURE2_org=',PRESSURE2_org)
    print ('diff_org=',diff_org)

    ##################################################################################################################################
    # create data set

    inc = 0
    yy = 0.1
    x = []
    #for i in range(1,5,1):
    #    y =  yy + inc
    #    inc += 0.1
    #    x.append(round(y,4))
    x = [5]
    print ('x=',x)
    print ('')
    print ('len(x)',len(x))
    print ('')


   # delete link
    en.deletelink(ph, index=1, actionCode = en.UNCONDITIONAL )
    # add lekage noed
    en.addnode (ph, "4",nodeType= en.JUNCTION)
    error = en.setnodevalue(ph, index=3, property= en.EMITTER ,value =0+0.1)
    # add nya pipe
    index = en.addlink(ph, "P1", en.PIPE, "2","4")
    error = en.setpipedata(ph, index=2, length= 500, diam =100, rough=120,mloss = 0)   
    en.addlink(ph, "P2", en.PIPE,"4","3")
    error2 = en.setpipedata(ph, index=3, length= 500, diam =100, rough=120,mloss = 0)
    
    v1 = en.getlinkvalue(ph, index=2,property= en.LENGTH)
    v2 = en.getlinkvalue(ph, index=3,property= en.LENGTH)

    #print ('v1=',v1)
    #print ('v2=',v2)

        
    node1_pressure = []
    node1_head = []
    node2_pressure = []
    node2_head = []
    pipe_length = []
    leakage_size = []
    dis = 1
    

    wbk = xlwt.Workbook()  # skapa ny arbetsbok
    Sheet1 = wbk.add_sheet('training_data')
    Sheet1.set_portrait(False)   # välj Landscape
    stylecen = xlwt.easyxf('align: horiz center;borders: left thin, right thin, top thin, bottom thin') # style för centered
    styleboldleft = xlwt.easyxf('font: bold on;borders: left thin, right thin, top thin, bottom thin')
    boldcen = xlwt.easyxf('font: bold on; align: horiz center')
    border = xlwt.Style.easyxf("""align: horiz center;borders: left thin, right thin, top thin, bottom thin;""")
    boldborder = xlwt.Style.easyxf("""align: horiz center;font: bold on;borders: left thin, right thin, top thin, bottom thin;""")
    #Sheet1.write(1,0,'Sammanställning av snitteffekter. Skapad i PSSE med program snittabell.py','latin-1'),styleboldleft)
    rad = 0
    
    Sheet1.write(rad,0,'Length_from_node1',boldborder)
    Sheet1.write(rad,1,'Node1_pressure_c_5',boldborder)
    Sheet1.write(rad,2,'Node2_pressure_c_5',boldborder)    
    Sheet1.write(rad,3,'Link1_flow_c_5',boldborder)
    Sheet1.write(rad,4,'Link2_flow_c_5',boldborder)
    Sheet1.write(rad,5,'Link1_velocity_c_5',boldborder)
    Sheet1.write(rad,6,'Link2_velocity_c_5',boldborder)

    
    colwi = 10
    Sheet1.col(0).width = int(25*260)

    length = []
    kol = 0
    for i in range (1,1000,1):
        
        node1_pressure = []
        node2_pressure = []
        link1_flow = []
        link2_flow = []
        link1_velocity = []
        link2_velocity = []
        for j in range(len(x)):
            error = en.setnodevalue(ph, index=3, property= en.EMITTER ,value =x[j])
            # change length of L2
            en.setpipedata(ph, index=2, length= int(i), diam =100, rough=120,mloss = 0)
            # change length of L3
            en.setpipedata(ph, index=3, length= int(1000-i), diam =100, rough=120,mloss = 0)
            en.solveH(ph)
            PRESSURE11 = en.getnodevalue(ph, index=1, property=en.PRESSURE)
            #print ('PRESSURE11=',PRESSURE11)
            node1_pressure.append(PRESSURE11)
            PRESSURE12 = en.getnodevalue(ph, index=2, property=en.PRESSURE)
            #print ('PRESSURE12=',PRESSURE12)
            node2_pressure.append(PRESSURE12)

            Link1flow = en.getlinkvalue(ph, index=2, property=en.FLOW)
            link1_flow.append(Link1flow)
            
            Link2flow = en.getlinkvalue(ph, index=3, property=en.FLOW)
            link2_flow.append(Link2flow)
            
            Link1velocity = en.getlinkvalue(ph, index=2, property=en.VELOCITY)
            link1_velocity.append(Link1velocity)
            
            Link2velocity = en.getlinkvalue(ph, index=3, property=en.VELOCITY)
            link2_velocity.append(Link2velocity)
            
            
           
        v1 = en.getlinkvalue(ph, index=2,property= en.LENGTH)
        v2 = en.getlinkvalue(ph, index=3,property= en.LENGTH)
        v3 = en.getlinkvalue(ph, index=3,property= en.VELOCITY)
        #print ('v1=',int(v1))
        #print ('v2=',int(v2))
        print ('v3=',v3)

 
        kol = 0
        rad += 1
        Sheet1.write(rad,kol,int(i),stylecen)
      
        for k in range(len(node1_pressure)):
            #length.append(i)
            kol += 1 
            Sheet1.write(rad,kol,node1_pressure[k],stylecen)
            kol += 1
            Sheet1.write(rad,kol,node2_pressure[k],stylecen)                    
            kol += 1
            Sheet1.write(rad,kol,link1_flow[k],stylecen)
            kol += 1
            Sheet1.write(rad,kol,link2_flow[k],stylecen)
            kol += 1
            Sheet1.write(rad,kol,link1_velocity[k],stylecen)
            kol += 1
            Sheet1.write(rad,kol,link2_velocity[k],stylecen) 
      

    #print ('')
    #print ('len(node2_pressure)=',len(node2_pressure))

    wbk.save(utfil)
    length = []
    for i in range(1,1001):
        length.append(int(i-1))
    df = pd.DataFrame(length)
    
    df.set_axis(["Length"], axis=1,inplace=True)
    print ('df=',df)
        
    data = pd.read_excel('Training_data.xls', index_col=0)
    result = pd.concat([data, df], axis=1)
    result_new = result.drop(result.index[0])
 
    print ('result_new =')
    print (result_new)
    print ('')


    NET1 = get_column(list(result_new.Length))
    NET2 = get_column(list(result_new.Node1_pressure_c_0_1))
    NET3 = get_column(list(result_new.Node2_pressure_c_0_1))
    plt.plot(NET1,NET2)
    #plt.plot(NET1,NET3)
    #plt.show()


    diff_ = []
    for i in range(len(NET1)):
        diff1 = NET3[i] - NET2[i]
        diff_.append(diff1)
    plt.plot(NET1,diff_)
    #plt.plot(1000,diff_org, 'bo')
    #plt.ylim(2, 10)
    #plt.show()

     
    en.solveH(ph)

    # Opens a project's water quality solver (openQ). Call openQ prior to running the first water quality analysis
    # using an initQ - runQ - nextQ (or stepQ) sequence.
    # Multiple water quality analyses can be made before calling closeQ to close the water quality solver.

    en.openQ(ph)

    # Initializes a network prior to running a water quality analysis(initQ). Call initQ prior to running
    # a water quality analysis using runQ in conjunction with either nextQ or stepQ.
    # set to InitHydOption.Save if results are to be saved to the project's binary output file, or to InitHydOption.
    # NoSave if not. (see InitHydOption)

    en.initQ(ph, en.NOSAVE)
    

    #PRESSURE3 = en.getnodevalue(ph, index=1, property=en.PRESSURE)
    #print ('PRESSURE3=',PRESSURE3)

    #PRESSURE4 = en.getnodevalue(ph, index=2, property=en.PRESSURE)
    #print ('PRESSURE4=',PRESSURE4)

    en.saveinpfile(ph, "example2.inp")    


    #epanet = dcritsim.epanetwrap.DcritEPANET()
    #ph = epanet.get_ph()
    #en.open(ph, args.input_filename, args.report_filename, args.binary_filename)
    #en.solveH(ph)
    
    #PRESSURE11 = en.getnodevalue(ph, index=1, property=en.PRESSURE)
    #print ('PRESSURE11=',PRESSURE11)

    #PRESSURE12 = en.getnodevalue(ph, index=2, property=en.PRESSURE)
    #print ('PRESSURE12=',PRESSURE12)


    
    return epanet 

class ActionPrintProperty:
    def __init__(self, data_extractor):
        self._data_extractor = data_extractor
        print('print hook: node names=', data_extractor.names)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __call__(self, time):
        print('print hook: time=', time, 'values=', self._data_extractor.values)

    

def main():
    # Input network, binary file name, report file name and hydraulic steps 
    parser = argparse.ArgumentParser(description='Run an EPANET simulation.')
    parser.add_argument('input_filename',
                        help='An EPANET input file describing the system.')
    parser.add_argument('report_filename', nargs='?', default='',
                        help='Report log file from the simulation run.')
    parser.add_argument('binary_filename', nargs='?', default='',
                        help='Hydraulic analysis results file (binary).')
    parser.add_argument('--hstep', metavar='seconds', type=int, default=3600,
                        help='Hydraulic time step (default 3600s=1h).')


    # return all stored information object with two attributes, integers and accumulate.
    # The integers attribute will be a list of one or more ints
    args = parser.parse_args()
    print ('')
    print ('args=',args)
    print ('')
    
    # i dont know what epanet_subsys_init 
    epanet = epanet_subsys_init(args)






    del(epanet)    

    return 0


if __name__ == "__main__":
    sys.exit(main())