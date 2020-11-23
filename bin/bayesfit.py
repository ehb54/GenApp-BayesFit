#!/usr/bin/python3

import json
import io
import sys
import os
import socket # for sending progress messages to textarea
from genapp3 import genapp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import subprocess

if __name__=='__main__':

    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)

    # read model non-specific Json input
    data_file_path = json_variables['datafile'][0] # name of datafile
    data = data_file_path.split('/')[-1] 
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

    # read model-specific Json intput
    if model == "coreshell":
        N_params = 6
    elif model == "nanodisc":
        N_params = 12
    elif model == "micelle":
        N_params = 7

    # make for loop
    for i in range(N_params):
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
    d = genapp(json_variables)

    ## run bayesfit
    d.udpmessage({"_textarea":"run bayesfit\n"})

    def execute(command,f):
        popen = subprocess.Popen(command, stdout=subprocess.PIPE,bufsize=1)
        lines_iterator = iter(popen.stdout.readline, b"")
        while popen.poll() is None:
            for line in lines_iterator:
                nline = line.rstrip()
                nline_latin = nline.decode('latin')
                out_line = '%s\n' % nline_latin
                #print(nline.decode("latin"), end = "\r\n",flush =True) # yield line
                d.udpmessage({"_textarea": out_line})
                f.write(out_line)
    
    f = open('stdout.d','w')
    execute([os.path.dirname(os.path.realpath(__file__)) + '/BayesFit/bayesfit','input.d'],f)
    f.close()

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

    ## generate plots
    q,Idat,sigma = np.genfromtxt('data.d',skip_header=0,usecols=[0,1,2],unpack=True)
    q,Ifit = np.genfromtxt('fit.d',skip_header=1,usecols=[0,1],unpack=True)
    q,Iprior = np.genfromtxt('prior.d',skip_header=0,usecols=[0,1],unpack=True)
    R = (Ifit-Idat)/sigma
    maxR = np.ceil(np.amax(abs(R)))
    
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1]) 
    p1 = plt.subplot(gs[0])
    p2 = plt.subplot(gs[1])
    
    ## log-log
    p1.errorbar(q,Idat,yerr=sigma,linestyle='none',marker='.',color='red',label='data',zorder=0)
    p1.plot(q,Iprior,linestyle='--',color='grey',label='prior',zorder=1)
    p1.plot(q,Ifit,color='black',label='fit')
    
    p2.plot(q,q*0,linestyle='none',marker='.',color='red')
    p2.plot(q,R,color='black')

    p1.set_xscale('log')
    p1.set_yscale('log')
    p1.set_ylabel(r'$I(q)$ [cm$^{-1}$]')
    p1.set_xticklabels([])
    p1.legend()
    
    p2.set_xscale('log')
    p2.set_ylim([-maxR,maxR])
    p2.set_yticks([-maxR,0,maxR])
    p2.set_xlabel(r'$q$ [$\AA^{-1}$]')
    p2.set_ylabel(r'$\Delta I/\sigma$')
    p1.set_title('data, prior and fit (log-log scale)')
    
    plt.savefig('plot_loglog.png',dpi=200)

    ## lin -log
    p1.set_xscale('linear')
    p2.set_xscale('linear')
    p1.set_title('data, prior and fit (lin-log scale)')
    plt.savefig('plot_linlog.png',dpi=200)
    plt.close()
   
    ## compress output files to zip file
    os.system('zip results.zip data.d fit.d prior.d parameters.d stdout.d *.png')

    ## generating output
    output = {} # create an empty python dictionary
    output["file_data"] = "%s/data.d" % folder
    output["file_fit"] = "%s/fit.d" % folder
    output["file_prior"] = "%s/prior.d" % folder
    output["file_parameters"] = "%s/parameters.d" % folder
    output["file_stdout"] = "%s/stdout.d" % folder
    output["file_plot"] = "%s/plot_loglog.png" % folder
    output["file_zip"] = "%s/results.zip" % folder
    output["chi2"] = "%s" % chi2
    output["chi2r"] = "%s" % chi2r
    output["alpha"] = "%s" % alpha 
    output["S"] = "%s" % S
    #output["aS"] = "%s" % aS
    output["Ng"] = "%s" % Ng
    output["evidence"] = "%s" % evidence
    output["plotfit"] = "%s/plot_loglog.png" % folder
    output["plotfit_linlog"] = "%s/plot_linlog.png" % folder

    #output['_textarea'] = "JSON output from executable:\n" + json.dumps( output, indent=4 ) + "\n\n";
    #output['_textarea'] += "JSON input to executable:\n" + json.dumps( json_variables, indent=4 ) + "\n";
    
#    ##plot
#    output['plotline'] = {
#            "data" : [
#                {"x": q.tolist(),"y": Idat.tolist(),"error_y": {"type": "data","array":sigma.tolist(),"visible":"true"},"type": "scatter","mode": "markers","marker": {"color": "rgb(250,  0,  0)","size":12},"name": "data"},
#                {"x": q.tolist(),"y": Iprior.tolist(),"mode": "lines",  "line":   {"color": "rgb(170,170,170)","width":3},"name": "prior"},
#                {"x": q.tolist(),"y": Ifit.tolist()  ,"mode": "lines",  "line":   {"color": "rgb(  0,  0,  0)","width":3},"name": "fit"}
#            ]
#            ,"layout": {"title": "data, prior and fit","xaxis": {"title":{"text": "q [1/A]"},"type": "log"},"yaxis": {"title":{"text": "I(q) [1/cm]"},"type": "log"}}
#        }

    ## send output
    print( json.dumps(output) ) # convert dictionary to json and output


