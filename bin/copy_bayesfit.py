#!/usr/bin/python3

import json
import io
import sys

if __name__=='__main__':

    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)
    
    output = {} 
    output["note"] = "bayesfit executable";
    
    output['_textarea'] = "JSON output from executable:\n" + json.dumps( output, indent=4 ) + "\n\n";
    output['_textarea'] += "JSON input to executable:\n" + json.dumps( json_variables, indent=4 ) + "\n";
    
    print( json.dumps(output) )

