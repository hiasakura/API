from datetime import date, timedelta
from collections import defaultdict
import urllib2, time, binascii, sha, json

class RestPy:
    
    YESTERDAY_DATE = (date.today() - timedelta(1)).strftime("%Y-%m-%d")
    def __init__(self, user_name, shared_secret):
        self.user_name = user_name
        self.shared_secret = shared_secret
    
    def __get_header(self):
        nonce = str(time.time())
        base64nonce = binascii.b2a_base64(binascii.a2b_qp(nonce))
        created_date = time.strftime("%Y-%m-%dT%H:%M:%SZ",  time.gmtime())
        sha_object = sha.new(nonce + created_date + self.shared_secret)
        password_64 = binascii.b2a_base64(sha_object.digest())
        return 'UsernameToken Username="%s", PasswordDigest="%s", Nonce="%s", Created="%s"' % (self.user_name, password_64.strip(), base64nonce.strip(), created_date)
    
    def run_omtr_immediate_request(self, method, request_data):
        request = urllib2.Request('https://api.omniture.com/admin/1.4/rest/?method=%s' % method, json.dumps(request_data))
        request.add_header('X-WSSE', self.__get_header())
        return  json.loads(urllib2.urlopen(request).read())
    
    def run_omtr_queue_and_wait_request(self, method, request_data,max_polls=20,max_retries=3):
        status, status_resp = "", ""
        num_retries=0
        while status != 'done' and num_retries < max_retries:
            status_resp = self.run_omtr_immediate_request(method, request_data)
            report_id = status_resp['reportID']
            status = status_resp['status']
            print "Status for Report ID %s is %s" % (report_id, status)
            polls=0
            while status != 'done' and status != 'failed':
                if polls > max_polls:
                    raise Exception("Error:  Exceeded Max Number Of Polling Attempts For Report ID %s" % report_id)
                time.sleep(10)
                status_resp = self.run_omtr_immediate_request('Report.GetStatus', {"reportID" : report_id})
                status = status_resp['status']
                print "Status for Report ID %s is %s" % (report_id, status)
        
            if status == 'failed':
                num_retries += 1
                print "Reported Failure For Report.  Retrying same request."

        if status == 'failed':
            raise Exception("Error: Report Run Failed and passed %s retries.  Full response is %s" % (max_retries, status_resp))        
        return self.run_omtr_immediate_request('Report.GetReport', {'reportID' : report_id})
    
    def get_count_from_report(self, report_suite_id, metric, element=None, selected_element_list=None, date_from=YESTERDAY_DATE, date_to=YESTERDAY_DATE, date_granularity="day", return_one_total_result = True):
        metrics = [{"id":metric}]
        
        if element == None:
            request_type = 'Report.QueueOvertime'
            elements = None
        else:
            request_type= 'Report.QueueTrended'
            elements = [{"id":element, "selected": selected_element_list }]
        
        response = self.run_omtr_queue_and_wait_request(request_type,{"reportDescription":  
                                                {"reportSuiteID" :report_suite_id,
                                                 "dateFrom":date_from,
                                                 "dateTo":date_to,
                                                 "dateGranularity":date_granularity,
                                                 "metrics": metrics, 
                                                 "elements" : elements
                                                }})
        if response["status"] != "done":
            raise Exception("Error:  Full response is %s" % response)
        
        report = response["report"]
        
        if return_one_total_result:
            if selected_element_list == None:
                return int(report["totals"][0]) 
            total_for_selected_elements = 0
            for datum in report["data"]:
                if datum["name"] in selected_element_list:
                    total_for_selected_elements += int(datum["counts"][0])
            return total_for_selected_elements
        
        else:
            result_dict = defaultdict(int) 
            for datum in report["data"]:
                if request_type == "Report.QueueOvertime":
                    result_dict[datum["name"]] = datum["counts"][0]
                elif request_type == "Report.QueueTrended":
                    if selected_element_list == None or datum["name"] in selected_element_list:
                        for day_breakdown in datum["breakdown"]:
                            result_dict[day_breakdown["name"]] += int(day_breakdown["counts"][0])
            return result_dict