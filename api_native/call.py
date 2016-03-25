# -*- coding: utf-8 -*-
import json
from datetime import datetime
from rest import RestPy


############### Setting #################
user = "XXXXXXXXXXXXXXXX"
key = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
method = "ReportSuite.GetIPAddressExclusions"
req={
	"rsid_list":[
		row[0]
	]
}
#########################################


# call api
rest = RestPy(user,key)
json_object =  rest.run_omtr_immediate_request(method, req) 
now = datetime.now().strftime("%Y%m%d%H%M%S")

# response
outfile = "res_"+ method + "_" + now + ".json"
outdata = json.dumps(json_object, ensure_ascii=False, indent=4)
with open(outfile, "w") as fo:
    fo.write(outdata.encode("utf-8"))

# request
infile = "req_"+ method + "_" + now + ".json"
indata = json.dumps(req, ensure_ascii=False, indent=4)
with open(infile, "w") as fi:
    fi.write(indata.encode("utf-8"))
