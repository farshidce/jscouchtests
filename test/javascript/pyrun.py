# --t testname --output json.xunit --timeout 10 --server
from threading import Thread

import fileinput
import os
import fnmatch
import logging
from optparse import OptionParser
import json
from xunit import XUnitTestResult
import time
from subprocess import Popen, PIPE, STDOUT


def init_logger():
    logger = logging.getLogger("pyrun")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logger.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    logger.addHandler(consoleHandler)
    return logger


def find_files(search_path):
    files = []
    #see if path has "*" character
    #or if its just a file
    if search_path.find("*") == -1:
        logger.info("looking for single file in {0}".format(search_path))
        if os.path.isfile(search_path):
            files.append(search_path)
    else:
        directory_path = search_path[:search_path.find("*")]
        logger.info("search path : {0}".format(directory_path))
        for file in os.listdir(directory_path):
            if fnmatch.fnmatch(file, search_path[search_path.find("*"):]):
                if file.find("attachment") != -1:
                    continue
                files.append(directory_path + file)
    return files

def pick_file(files, filename):
    for file in files:
        if file.find(filename) != -1:
            return file
    raise Exception("unable to find {0}".format(filename))


def sort_js_files(files):
    json2 = pick_file(files, "json2.js")
    sha1 = pick_file(files, "sha1.js")
    oauth = pick_file(files, "script/oauth.js")
    couch = pick_file(files, "couch.js")
    couch_test_runner = pick_file(files, "couch_test_runner.js")
    couch_http = pick_file(files, "couch_http.js")
    cli_runner = pick_file(files, "cli_runner.js")
    sorted = [json2, sha1, oauth, couch, couch_http]
    for file in files:
        if not file in sorted and file != cli_runner:
            sorted.append(file)
    sorted.append(cli_runner)
    return sorted


def append_files(files, output, replace_token, with_token):
    output_file = open(output, 'w')
    try:
        for file in files:
            new_comment_link = "//appending {0} \n".format(file)
            output_file.write(new_comment_link)
            for line in fileinput.input(file):
                if replace_token and with_token:
                    if line.find(replace_token) != -1:
                        line = line.replace(replace_token, with_token)
                output_file.write(line)
        output_file.close()
        return True
    except:
        return False



def start_couchjs_with_timeout(process,xunit):
    line = process.stdout.readline()
    while line:
        try:
            print line,
            obj = json.loads(line)
            if "name" in obj and "time" in obj and "status" in obj:
                if obj["status"] == "pass":
                    xunit.add_test(name=obj["name"], status=obj["status"], time=obj["time"])
                elif obj["status"] == "fail":
                    xunit.add_test(name=obj["name"], status=obj["status"], time=obj["time"],
                                   errorType='couchdb.error', errorMessage=obj["error"])
        except:
            pass
        line = couchjs_test_runner.stdout.readline()


#parse test execution results and create a xnit result out of it


logger = init_logger()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-s", "--script", dest="script", default="*.js",
                      help="which script(s) to run", metavar="*.js")
    parser.add_option("-o", "--output",
                      dest="output", help="test results will be printed out in the given format",
                      default="xunit")
    parser.add_option("--timeout", dest="timeout", help="timeout limit for each test", default="120")
    parser.add_option("-n", "--node", dest="node", help="couchdb ip , defaults to 127.0.0.1:5984",
                      default="127.0.0.1:5984")
    parser.add_option("-x", "--exclusion-filter", dest="exclusion", default="",
                      help="which scripts to exclude when running the tests", metavar="all_docs.js,basics.js")
   

    options, args = parser.parse_args()
    exclusion = options.exclusion
    if exclusion != "":
       exclusion = exclusion.split(",")

    logger.info("exclusion: ".format(exclusion))
    script = options.script
    logger.info("script : {0}".format(script))
    timeout = int(options.timeout)
    logger.info("timeout : {0}".format(timeout))
    output = options.output
    logger.info("output : {0}".format(output))
    node = options.node
    logger.info("node : {0}".format(node))
    # script can be abc.js or *.js 
    # use file_finder to find all the files which match the given expression
    logger.info("finding files for script : {0}".format(script))
    #let' load all the scripts for now!
    base_url = "../../share/www/script/"
    required_scripts = [base_url + "json2.js", base_url + "sha1.js",
                        base_url + "couch.js", base_url + "oauth.js",
                        base_url + "couch_test_runner.js"]
    base_files = []
    for file in required_scripts:
        found = find_files(file)
        base_files.extend(found)

    xunits = []
    for found in find_files(base_url + "test/{0}".format(script)):
        should_be_excluded = False
        for exc in exclusion:
           if found.find(exc) >= 0:
              should_be_excluded = True
              break
        if should_be_excluded:
           logger.info("skipping {0}".format(exc))
           continue
        logger.info("running {0}".format(found))
        more_js = find_files("./*.js")
        files = []
        files.extend(base_files)
        files.append(found)
        files.extend(more_js)
        files = sort_js_files(files)
        logger.info("files matched : {0}".format(files))
        merged_filename = "merged-js-files.txt"
        if append_files(files, merged_filename, "127.0.0.1:5984", options.node):
            logger.info("merged all files into one file {0}".format(merged_filename))
        xunit = XUnitTestResult()
        command = ["../../src/couchdb/priv/couchjs", "-H", "merged-js-files.txt"]
        couchjs_test_runner = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        run_test_thread = Thread(name="run-test",target=start_couchjs_with_timeout,args=(couchjs_test_runner,xunit))
        run_test_thread.start()
        start = time.time()
        status = "ok"
        while (time.time() - start) < timeout:
            if not run_test_thread.isAlive():
                status = "ok"
                break
            else:
                time.sleep(2)


        if status != "ok":
            couchjs_test_runner.kill()

        str_time = time.strftime("%H:%M:%S", time.localtime()).replace(":", "-")
        xunit.write("report-{0}.xml".format(str_time))
        xunit.print_summary()
        xunits.append(xunit)

    logger.info("executed all test cases.printing out the summary...")
    for x in xunits:
        x.print_summary()
