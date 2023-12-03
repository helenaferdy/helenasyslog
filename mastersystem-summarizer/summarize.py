import yaml
import os
import shutil
from collections import Counter
from datetime import datetime, timedelta
import sys


TESTING_ENV = False
TOP_COUNT = 5

sys.path.append('/opt/mastersystem-syslog/') 
if TESTING_ENV:
    sys.path.append('../mastersystem-syslog/') 
from sendwebex import send_webex


class Summarizer:
    def __init__(self, group_name, webex_id, sent_logs, filtered_logs):
        self.group_name = group_name
        self.webex_id = webex_id
        self.sent_logs = sent_logs
        self.filtered_logs = filtered_logs

    def categorize(self, logs):
        log_total = 0
        log_device = []
        log_code = []
        log_msg = []
        
        for log in logs:
            parts = log.split(" | ")
            hostname = parts[2].strip()
            code = parts[5].strip()
            msg = parts[6].strip()
            log_group = parts[7].strip()
            if self.group_name == log_group:
                log_total += 1
                log_device.append(hostname)
                log_code.append(f'{hostname} : {code}')
                log_msg.append(f'{hostname} : {msg}')

        # device_count = self.count_device(log_device)
        top_5_device = self.sort(log_device)
        top_5_code = self.sort(log_code)
        top_5_msg = self.sort(log_msg)

        return log_total, log_device, top_5_device, top_5_code, top_5_msg
            
    def count_device(self, data):
        # Convert the list to a set to remove duplicates
        unique_set = set(data)
        # Convert the set back to a list
        unique_list = list(unique_set)

        return len(unique_list)
    

    def sort(self, data):
        # Count the occurrences of each element
        counter_dict = Counter(data)
        # Sort the elements by the number of appearances in descending order
        sorted_elements = sorted(counter_dict.items(), key=lambda x: x[1], reverse=True)
        # limit to 5
        top_elements = sorted_elements[:TOP_COUNT]
        # Create a formatted string
        formatted_string = "\n".join([f" {index + 1}. {element} ({count})" for index, (element, count) in enumerate(top_elements)])

        return formatted_string

    def send_message(self, message):
        send_webex(message, self.webex_id)



## NON OBJECT ##

DATE = datetime.now().strftime("%Y_%m_%d")
DATE_MINS = datetime.now().strftime("%d/%m %H:%M")
previous_date = datetime.now() - timedelta(hours=24)
PREV_DATE_MINS = previous_date.strftime("%d/%m %H:%M")

CONFIG_PATH = "/opt/mastersystem-syslog/conf/config.yml"
if TESTING_ENV:
    CONFIG_PATH = "../mastersystem-syslog/conf/lab_config.yml"

## OPEN CONFIG FILE
try:
    with open(CONFIG_PATH, "r") as yml_file:
        ymlconfig = yaml.safe_load(yml_file)
except:
    print("Error opening config file")

SENT_LOG_PATH = ymlconfig["archive_log"] 
FILTERED_LOG_PATH = ymlconfig["filtered_log"]
GROUP_PATH = ymlconfig["group_path"] 
MOVE_DEST = "/opt/mastersystem-syslog/logs/archived/"

if TESTING_ENV:
    SENT_LOG_PATH = "../mastersystem-syslog/logs/sent_syslog.log"
    FILTERED_LOG_PATH = "../mastersystem-syslog/logs/filtered_syslog.log"
    GROUP_PATH =  "../mastersystem-syslog/groups/"
    MOVE_DEST = "../mastersystem-syslog/logs/archived/"

SENT_LOGS = []
FILTERED_LOGS = []

## OPEN LOGS
try:
    with open(SENT_LOG_PATH, "r") as logs:
        for log in logs:
            SENT_LOGS.append(log.strip())

    with open(FILTERED_LOG_PATH, "r") as logs:
        for log in logs:
            FILTERED_LOGS.append(log.strip())
except:
    print("Error opening log files")


## MOVE LOGS
def move_logs(source, dest):
    try:
        shutil.move(source, dest)
        print('logs moved successfully')
    except:
        print('failed moving logs')

def count_total_device(sent, filtered):
    merged_list = list(set(sent + filtered))
    total = len(merged_list)

    return total


x = []
def read_groups():
    group_list = os.listdir(GROUP_PATH)

    for group_file in group_list:
        group_full_path = os.path.join(GROUP_PATH, group_file)
        
        if os.path.isfile(group_full_path):
            try:
                with open(group_full_path, "r") as yml_file:
                    group_name = group_file[:-4].upper()
                    ymlgroupconfig = yaml.safe_load(yml_file)
                    webex_id = ymlgroupconfig['webex_id']

                    object = Summarizer(group_name, webex_id, SENT_LOGS, FILTERED_LOGS)
                    x.append(object)
            except:
                print(f"Error opening {group_file}")

def run_summarizer():
    if SENT_LOGS or FILTERED_LOGS:
        if not TESTING_ENV:
            move_logs(SENT_LOG_PATH, f"{MOVE_DEST}{DATE}_sent_syslog.log")
            move_logs(FILTERED_LOG_PATH, f"{MOVE_DEST}{DATE}_filtered_syslog.log")
        for xx in x:
            print(f"\n---= {xx.group_name} =---")

            sent_total, sent_device_count, sent_device, sent_code, sent_msg = xx.categorize(xx.sent_logs)
            filtered_total, filtered_device_count, filtered_device, filtered_code, filtered_msg = xx.categorize(xx.filtered_logs)

            total_device = count_total_device(sent_device_count, filtered_device_count)

            x_header = f'''
[SYSLOG DAILY SUMMARY]
[{PREV_DATE_MINS}] - [{DATE_MINS}]
[TOTAL LOGS] : [{sent_total+filtered_total}]
[TOTAL DEVICES] : [{total_device}]

------------------------------------------
'''
            x_sent_0 = f'''
[LOGS SENT] : [{sent_total}]
'''

            x_sent = f'''
[LOGS SENT] : [{sent_total}]

Top {TOP_COUNT} devices :
{sent_device}

Top {TOP_COUNT} codes :
{sent_code}

Top {TOP_COUNT} messages :
{sent_msg}
'''
            x_filtered_0 = f'''
------------------------------------------

[LOGS FILTERED] : [{filtered_total}]

------------------------------------------
'''
            
            x_filtered = f'''
------------------------------------------

[LOGS FILTERED] : [{filtered_total}]

Top {TOP_COUNT} codes :
{filtered_code}

Top {TOP_COUNT} messages :
{filtered_msg}

------------------------------------------
'''
            final = x_header
            if sent_total > 0:
                final += x_sent
            else:
                final += x_sent_0
            if filtered_total > 0:
                final += x_filtered
            else:
                final += x_filtered_0


            if not TESTING_ENV:
                xx.send_message(final)
            else:
                print(final)

        

read_groups()
run_summarizer()