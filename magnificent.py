
 ####    ##   #    #  ####  ######    #        ##   #####   ####  
#       #  #  #    # #    # #         #       #  #  #    # #      
 ####  #    # #    # #      #####     #      #    # #####   ####  
     # ###### #    # #      #         #      ###### #    #      # 
#    # #    # #    # #    # #         #      #    # #    # #    # 
 ####  #    #  ####   ####  ######    ###### #    # #####   ####  


                                                                  
import os
import time
import requests
import json

from daemoniker import Daemonizer

name = "magnificient"
pid_file = "%s.pid" %name
log_file = "%s.log" %name

# clean up pid file
if (os.path.exists(pid_file)): os.remove(pid_file)
if (os.path.exists(log_file)): os.remove(log_file)

# helper function appending to unix file handle with format string
def log(t, d):
    """open log file ina append mode and log type, time and date"""
    open(log_file, "a").write("[%s] [%s]: [%s]\n" %(t, str(time.time()), d))

conf = {
    "last_connectionerror": 0,
    "connection_errors":0,
    "last_state": None,
    # healthcheck every 20 seconds
    "pull_interval": 2,
    # report every 40 seconds
    "info_interval": 5
}

# cache stats
data = {
    "errors": 0,
    "fatals": 0,
    "successes": 0,
    # rolling average
    "avg_rsp": 0,
    "averages_cache": []
}

# one could do a is_(.*) syntax filter here like in perl with MooseX
# random thought. or is_...("success") but then one would had to check
# if it exists in data[] for solidity. 
def is_success():
    conf["last_state"] = "success"
    data["successes"] += 1

def is_error():
    log("e", "content not delivered, server responsive")
    conf["last_state"] = "error"
    data["errors"] += 1

def is_fatal():
    log("f", "server unresponsive")
    conf["last_state"] = "fatal"
    data["fatals"] += 1

def main():
    # last probe, last stats
    t1 = time.time()
    t2 = time.time()

    # hello
    log("info", "Monitor up and running.")

    while True:
        # every pull_interval seconds
        if (time.time() - t1 >= conf["pull_interval"]):
            # try catch in case of specific errors, doing only ConnectionError
            try:
                # measure http/tcp roundtrip time
                conn1 = time.time()
                r = requests.get("http://localhost:12345/")
                conn2 = time.time()

                # one could add checking the unix process of magnificent here, cpu consumption, ram,
                # process health etc.

                # add to stack of times
                data["averages_cache"].append(conn2-conn1)

                # rolling average
                sum_avg = 0
                for a in data["averages_cache"]:
                    sum_avg += a

                data["avg_rsp"] = sum_avg / len(data["averages_cache"])
                is_success() if (r.status_code == 200 and r.content == b"Magnificent!") else is_error()

            except requests.ConnectionError:
                # if repeating connection error, system is probably down
                log("fatal", "system seems down entirely" if conf["last_state"] == "connectionerror" else "connection error")
                data["fatals"] += 1
                conf["last_state"] = "connectionerror"
                conf["last_connectionerror"] = time.time()
            t1 = time.time()

        # check if time for stats
        if (time.time() - t2 >= conf["info_interval"]):
            data["averages_cache"] = []
            log("stats", json.dumps(data, indent=4))
            # reset after each info interval
            data["errors"] = 0
            data["fatals"] = 0
            data["successes"] = 0
            data["avg_rsp"] = 0
            # clear cache too
            if (conf["last_state"] == "connectionerror"):
                log("stats_fatal", "System seems down!")
            t2 = time.time()

with Daemonizer() as (is_setup, daemonizer):
    is_parent, data, conf = daemonizer(pid_file, data, conf)

main()
