import json
import daemon
import time
import requests
import os
# global variables

log_file = "magnificent.log"
last_connectionerror = 0
connection_errors = 0
last_state = None
# healthcheck every 20 seconds
pull_interval = 20
# report every 40 seconds
info_interval = 40
data = {"errors": 0, "fatals": 0, "successes":0, "avg_rsp":0}
averages_cache = []

# helper function appending to unix file handle with format string
def log(t, d):
    open(log_file, "a").write("[%s] [%s]: [%s]\n" %(t, str(time.time()), d))

# hello
log("info", "Monitor up and running.")

daemon.basic_daemonize()
if True:
    t1 = time.time()
    t2 = time.time()
    while True:
        # every pull_interval seconds
        if (time.time() - t1 >= pull_interval):
            # try catch in case of specific errors, doing only ConnectionError
            try:
                conn1 = time.time()
                r = requests.get("http://localhost:12345/")
                conn2 = time.time()
                averages_cache.append(conn2-conn1)
                sum_avg = 0
                for a in averages_cache:
                    sum_avg += a
                data["avg_rsp"] = sum_avg / len(averages_cache)
                # verify it really works
                if (r.status_code == 200 and r.content == b"Magnificent!"):
                   # set last state to keep track of repeating errors
                   last_state = "success"
                   data["successes"] += 1
                else:
                    log("error", "failure")
                    data["errors"] += 1
                    last_state = "fail"
            except requests.ConnectionError:
                if (last_state == "connectionerror"):
                    # if repeating connection error, system is probably down
                    log("fatal", "system seems down entirely")
                else:
                    log("fatal", "connection error")
                data["fatals"] += 1
                last_state = "connectionerror"
                last_connectionerror = time.time()
            t1 = time.time()
        if (time.time() - t2 >= info_interval):
            log("stats", json.dumps(data))
            # reset after each info interval
            data["errors"] = 0
            data["fatals"] = 0
            data["successes"] = 0
            data["avg_rsp"] = 0
            if (last_state == "connectionerror"):
                log("stats_fatal", "System seems down!")
            t2 = time.time()

