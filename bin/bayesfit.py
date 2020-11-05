#!/usr/bin/python3

import json
import io
import sys
import os
import socket # for sending progress messages to textarea
 
if __name__=='__main__':

    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)

    # read model non-specific Json input
    data = "Isim.dat"
    q_min = float(json_variables['qmin'])
    q_max = float(json_variables['qmax'])
    steps = int(json_variables['steps']) # Number of steps in function integrals
    maxite = int(json_variables['maxite']) # Maximum iterations in minization
    model = json_variables['model'] # model name
    folder = json_variables['_base_directory'] # output folder dir

    # make input file
    f = open("input.d",'w')
    
    # write model non-specific Json input to inputfile
    f.write('%s\n' % data)
    f.write('%s\n' % model)
    f.write('%d %d\n' % (steps,maxite))
    f.write('%f %f\n' % (q_min,q_max))

    # read model specific Json intput
    if model == "coreshell":
        # make for loop
        for i in range(6):
            #tmp = '%s_name_%d' % (model,i+1)
            #par_name(i) = json_variables[tmp]
            tmp = '%s_mean_%d' % (model,i+1)
            mean = float(json_variables[tmp])
            tmp = '%s_sigma_%d' % (model,i+1)
            sigma = float(json_variables[tmp])
            
            # fit, fit with positive constraint or fix?
            FIT = 0 
            tmp = '%s_fit_%d' % (model,i+1)
            try:
                fit = json_variables[tmp]
                FIT +=1
                try:
                    tmp = '%s_pos_%d' % (model,i+1)
                    pos = json_variables[tmp]
                    FIT +=1
                except:
                    pass
            except:
                pass
            
            # write model non-specific Json input to inputfile
            f.write('%f %f %d\n' % (mean,sigma,FIT))
        
    ## close input file 
    f.close()

    ## messaging
    UDP_IP = json_variables['_udphost']
    UDP_PORT = json_variables['_udpport']
    sock = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP

    socket_dict={}
    socket_dict['_uuid'] = json_variables['_uuid']

    socket_dict["_textarea"] = 'Starting Calculations...'
    #socket_dict["progress_output"] =  str(0.0)
    #socket_dict["progress_text"] =  'Fitting Progress: 0%'
    #if socket_dict:
    doc_string = json.dumps(socket_dict)
    sock.sendto(doc_string,(UDP_IP,UDP_PORT))


    ## run bayesfit
    output = {}
    output['_textarea'] = "running bayesfit...\n"
    print( json.dumps(output) )
    os.system('/opt/genapp/bayesfit/bin/BayesFit/bayesfit input.d')
    
    ## send output
    #socket_dict={}
    #socket_dict['_uuid'] = json_variables['_uuid']
    #value = '...'
    #svalue = str(100*value)
    #socket_dict['_progress'] = value
    #socket_dict['progress_output'] = value
    #socket_dict['progress_html'] = '<center>'+svalue+'</center>'
    #doc_string = json.dumps(socket_dict)

    #sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # INTERNET and UDP
    #sock.sendto(doc_string,(UDP_IP,UDP_PORT))

    ## retrive output from parameter file
    f = open('parameters.d','r')
    lines = f.readlines()
    for line in lines:
        if 'Chi2...........=' in line:
            chi2 = line.split('=')[1]
        if 'alpha......... =' in line:
            alpha = line.split('=')[1]
        if 'S..............=' in line:
            S = line.split('=')[1]
        if 'alpha*S........=' in line:
            aS = line.split('=')[1]
        if '-log(Evidence).=' in line:
            evidence = line.split('=')[1]
        if 'M..............=' in line:
            M = line.split('=')[1]
        if 'Ng.............=' in line:
            Ng = line.split('=')[1]
        #if 'Chi2/M.........=' in line:
        #    chi2r_M = int(line.split('=')[1])
        if 'Chi2/(M-Ng)....=' in line:
            chi2r = line.split('=')[1]
        line = f.readline()
    f.close()

    Ns = 'to be implemented'

    ## generating output
    #output = {} # create an empty python dictionary
    output["file_fit"] = "%s/fit.d" % folder
    output["file_prior"] = "%s/prior.d" % folder
    output["file_parameters"] = "%s/parameters.d" % folder
    os.system('zip results.zip fit.d prior.d parameters.d')
    output["file_zip"] = "%s/results.zip" % folder
    output["chi2"] = "%s" % chi2
    output["chi2r"] = "%s" % chi2r
    output["logalpha"] = "%s" % alpha 
    output["S"] = "%s" % S
    output["aS"] = "%s" % aS
    #output["I0"] = "%s" % I0
    output["Ng"] = "%s" % Ng
    output["Ns"] = "%s" % Ns
    output["evidence"] = "%s" % evidence

    #output['_textarea'] = "JSON output from executable:\n" + json.dumps( output, indent=4 ) + "\n\n";
    #output['_textarea'] += "JSON input to executable:\n" + json.dumps( json_variables, indent=4 ) + "\n";

    output["_textarea"] += "bayesfit finished succesfully!"

    print( json.dumps(output) ) # convert dictionary to json and output

