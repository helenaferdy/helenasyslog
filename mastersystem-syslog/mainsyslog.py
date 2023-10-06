import asyncio
import os
import time, datetime
import yaml
import re
from sendtelegram import send_telegram
from sendwhatsapp import send_whatsapp, send_whatsapp_max
from sendwebex import send_webex
from webex_meeting import start_meeting

# CONFIG_PATH = "conf/lab_config.yml"
CONFIG_PATH = "/opt/mastersystem-syslog/conf/config.yml"

USE_WEBEX_CONNECTOR = True

class PythonSyslog:
    def __init__(self, group, log_path, severities, out_mnemonics, in_mnemonics, out_messages, in_messages, wa_id, tele_id, webex_id, webex_room_id, sub_group):
        self.group = group
        self.log_path = log_path
        self.severities = severities
        self.out_mnemonics = out_mnemonics
        self.in_mnemonics = in_mnemonics
        self.out_messages = out_messages
        self.in_messages = in_messages
        self.wa_id = wa_id
        self.tele_id = tele_id
        self.webex_id = webex_id
        self.webex_room_id = webex_room_id
        self.sub_group = sub_group
        self.sub_key = ""

        if self.out_messages == [None]:
            self.out_messages = ['helenananana123']
        if self.in_messages == [None]:
            self.in_messages = ['helenananana123']
        
        self.log_messages = []

        self.read1_log_date = 0
        self.read2_log_date = 0

        self.processed_count = 0
        self.filtered_count = 0

        self.trigger_meeting = False

    def read_syslog(self):
        try:
            with open(self.log_path, 'r') as file:
                lines = file.readlines()
                if lines:
                    ## REMOVE DUPLICATE
                    lines = list(set(lines))
                    for line in lines:
                        if line.strip():
                            self.log_messages.append(line.strip())
                    return True
                else:
                    return False
        except Exception as e:
            message = f"error exception {e}"
            print(message)
            return False

    def truncate_syslog(self):
        try:
            with open(self.log_path, 'w') as file:
                file.truncate(0)
                print("syslog truncated")
                return True
        except:
            print("error truncating syslog")
            return False

    def read_syslog_date(self):
        try:
            modification_time = os.path.getmtime(self.log_path)
        except:
            print("error getting syslog date")
            return False

        log_delta = CURRENT_TIME - modification_time
        return int(log_delta)

    def message_id(self):
        msg_id = ymlconfig["counter_msg_id"] + 1
        ymlconfig["counter_msg_id"] = msg_id
        try:
            with open(CONFIG_PATH, "w") as yml_file:
                yaml.dump(ymlconfig, yml_file, default_flow_style=False)
        except:
            print("Error updating message id")
        return msg_id

    def delimite_log(self):
        delimited_msg = []
        severity = ""
        hostname = ""
        mnemonic = ""
        ip_address_pattern = r'\d{2}:\d{2}:\d{2} ([^\s]+)' # search IP / hostname after date
        ip_address_pattern2 = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" # Search IP in whole message
        timestamp_pattern = r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
        msg_pattern = r"%(.+)"

        try:
            for lm in self.log_messages:
                # ID
                try:
                    msg_id = self.message_id()
                except:
                    msg_id = 0

                # IP, HOSTNAME
                try:
                    ip_match = re.search(ip_address_pattern, lm)
                    ip_match = ip_match.group(1)
                    if ip_match[0].isdigit():
                        ip_address = ip_match
                        hostname = "x"
                        try:
                            hostname = ymlconfig["host_mapping"][ip_address]
                        except:
                            hostname = "x"
                    else:
                        ip_address = "0.0.0.0"
                        hostname = ip_match
                except:
                    # if IP or Hostname still not detected, bruteforce finding IP
                    try:
                        ip_address = re.findall(ip_address_pattern2, lm)
                        ip_address = ip_address[0]
                        if hostname == "" or hostname == "x":
                            try:
                                hostname = ymlconfig["host_mapping"][ip_address]
                            except:
                                hostname = "x"
                    except:
                        ip_address = "x"
                        hostname = "x"

                # TIMESTAMP
                timestamp = re.findall(timestamp_pattern, lm)
                try:
                    timestamp = timestamp[1]
                except:
                    timestamp = timestamp[0]

                # MNEMONIC, MESSAGE
                try:
                    msg = re.search(msg_pattern, lm)

                    if msg: 
                        msg_final = msg.group(1).strip()
                        parts = msg_final.split(":", 1)
                        mnemonic = parts[0].strip()
                        msg_final = parts[1].strip()
                    else:
                        mnemonic = "x"
                        msg_final = lm
                except:
                    mnemonic = "x"
                    msg_final = lm

                #SEVERITY
                if "-0-" in lm: severity = "0"
                elif "-1-" in lm: severity = "1"
                elif "-2-" in lm: severity = "2"
                elif "-3-" in lm: severity = "3"
                elif "-4-" in lm: severity = "4"
                elif "-5-" in lm: severity = "5"
                elif "-6-" in lm: severity = "6"
                elif "-7-" in lm: severity = "7"
                else: severity = "99"

                if int(severity) < 3:
                    self.trigger_meeting = True

                message = f'{msg_id} | {timestamp} | {hostname.upper()} | {ip_address} | {severity} | {mnemonic} | {msg_final}'
                delimited_msg.append(message)

            return True,delimited_msg
        
        except Exception as e:
            print(f"error delimiting log : {e}")
            for lm in self.log_messages:
                delimited_msg.append(lm)
            return False,delimited_msg

        
    def filtering(self, delimited_message):
        final_message = []
        filtered_message = []
        for msg in delimited_message:
            parts = msg.split(" | ")
            id = parts[0]
            date = parts[1]
            hostname = parts[2]
            ip = parts[3]
            severity = parts[4]
            mnemonic = parts[5]
            event = parts[6]

            if self.sub_group_hostname(hostname):
                severities,out_mnemonics,in_mnemonics,out_messages,in_messages = self.sub_group_config_override()
                config = f"{self.group.upper()} - {self.sub_key.upper()}"
            else:
                severities,out_mnemonics,in_mnemonics,out_messages,in_messages = self.global_config()
                config = self.group.upper()

            if mnemonic not in out_mnemonics:
                for out_msg in out_messages:
                    if out_msg not in event:
                        if mnemonic in in_mnemonics or severity in severities:
                            self.processed_count += 1
                            final_message.append(f"{msg} | {config}")
                        else:
                            # print(f"* ID {id} Filtered | Severity {severity}")
                            self.filtered_count += 1
                            filtered_message.append(f"{msg} | {config} | Cause : Severity {severity}")
                    else:
                        self.filtered_count += 1
                        # print(f"* ID {id} Filtered | Message {out_msg} excluded")
                        filtered_message.append(f"{msg} | {config} | Cause : Message {out_msg} excluded")
            else:
                for in_msg in in_messages:
                    if mnemonic in out_mnemonics and in_msg in event:
                        self.processed_count += 1
                        final_message.append(f"{msg} | {config}")
                    else:
                        self.filtered_count += 1
                        # print(f"* ID {id} Filtered | Mnemonic {mnemonic} excluded")
                        filtered_message.append(f"{msg} | {config} | Cause : Mnemonic {mnemonic} excluded")

        return final_message,filtered_message

    def sub_group_hostname(self, hostname):
        try:
            sub_group_keys = list(self.sub_group.keys())

            for sub_key in sub_group_keys:
                sub_group = self.sub_group[sub_key]
                host = sub_group["host"]

                if host != [None]:
                    for h in host:
                        if h.upper() == hostname.upper():
                            self.sub_key = sub_key
                            return True
        except Exception as e:
            print(f"Error getting sub_group hostname {e}")
            return False
                
    def sub_group_config_override(self):
        try:
            ymlsubconfig = self.sub_group[self.sub_key]

            severities = ymlsubconfig['include_severity']
            out_mnemonics = ymlsubconfig['exclude_code']
            in_mnemonics = ymlsubconfig['include_code']
            out_messages = ymlsubconfig['exclude_message']
            in_messages = ymlsubconfig['include_message']

            if out_messages == [None]:
                out_messages = ['helenananana123']
            if in_messages == [None]:
                in_messages = ['helenananana123']

            return severities,out_mnemonics,in_mnemonics,out_messages,in_messages
        except Exception as e:
            print(f"Error getting sub_group config {e}")
            return self.global_config()

    def global_config(self):
        severities = self.severities
        out_mnemonics = self.out_mnemonics
        in_mnemonics = self.in_mnemonics
        out_messages = self.out_messages
        in_messages = self.in_messages

        return severities,out_mnemonics,in_mnemonics,out_messages,in_messages
    
    def remove_duplicate(self, message):
        unique = []
        final = []

        for msg in message:
            ip = msg.split(" | ")[3].strip()
            event = msg.split(" | ")[6].strip()
            ip_event = f'{ip} {event}'

            if ip_event not in unique:
                unique.append(ip_event)
                final.append(msg)
        
        return final

    def beautify_log(self, log_data):
        parsed_data = {}

        for log_entry in log_data:
            parts = log_entry.split(" | ")
            log_id = parts[0]
            timestamp = parts[1]
            hostname = parts[2]
            ip_address = parts[3]
            ## ONLY SHOWS HOSTNAME
            ip_address = hostname
            # ip_address = hostname+" : "+ip_address
            severity_code = parts[4]
            mnemonic = parts[5]
            event = parts[6]

            try: severity_text = SEVERITIES_TEXT[int(severity_code)]
            except: severity_text = "Others"
            
            if ip_address not in parsed_data:
                parsed_data[ip_address] = {}
            if severity_code not in parsed_data[ip_address]:
                parsed_data[ip_address][severity_code] = []
            
            parsed_data[ip_address][severity_code].append({
                "Log ID": log_id,
                "Timestamp": timestamp,
                "Mnemonic": mnemonic,
                "Event": event,
            })
    
        result = ""
        for ip_address, errors in parsed_data.items():
            result += f"[{ip_address}]\n"
            for severity_code, entries in errors.items():
                result += f"\nSeverity : {severity_text} ({severity_code})\n"
                for entry in entries:
                    result += f"* ID: {entry['Log ID']}\n"
                    result += f"   Time: {entry['Timestamp']}\n"
                    result += f"   Code: {entry['Mnemonic']}\n"
                    result += f"   Msg: {entry['Event']}\n"
            result += "\n"
        return result

    def archive_syslog(self, processed_msg, filtered_msg):
        try:
            with open(ARCHIVE_LOG, "a") as log:
                for msg in processed_msg:
                    log.write(msg + '\n')
        except Exception as e:
            print(f"exception writing to archived_syslog.log: {e}")
        
        try:
            with open(FILTERED_LOG, "a") as log:
                for msg in filtered_msg:
                    log.write(msg + '\n')
        except Exception as e:
            print(f"exception writing to filtered_syslog.log: {e}")

    def send_message(self, message):
        if USE_WEBEX_CONNECTOR:
            send_webex(message, self.webex_id)
        else:
            send_webex(message, self.webex_id)
            send_whatsapp(message, self.wa_id)
            asyncio.run(send_telegram(message, self.tele_id))


#### Non Object ####

CURRENT_TIME = int(time.time())
CURRENT_DATE = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\n\n-----------------------------")
print(f"--- {CURRENT_DATE}")


## OPEN CONFIG FILE
try:
    with open(CONFIG_PATH, "r") as yml_file:
        ymlconfig = yaml.safe_load(yml_file)
except:
    print("Error opening config file")

GROUP_PATH = ymlconfig["group_path"] 
ARCHIVE_LOG = ymlconfig["archive_log"] 
FILTERED_LOG = ymlconfig["filtered_log"]
WEBEX_ACCESS_TOKEN = ymlconfig["access_token"]
SEVERITIES_TEXT = ['Emergency', 'Alert', 'Critical', 'Error', 'Warning', 'Notification', 'Informational', 'Debugging']

x = []
def read_groups():
    group_list = os.listdir(GROUP_PATH)

    for group_file in group_list:
        group_full_path = os.path.join(GROUP_PATH, group_file)
        
        if os.path.isfile(group_full_path):
            try:
                with open(group_full_path, "r") as yml_file:
                    ymlgroupconfig = yaml.safe_load(yml_file)

                    group = group_file[:-4]
                    log_path = ymlgroupconfig['log_path']
                    severities = ymlgroupconfig['include_severity']
                    out_mnemonics = ymlgroupconfig['exclude_code']
                    in_mnemonics = ymlgroupconfig['include_code']
                    out_messages = ymlgroupconfig['exclude_message']
                    in_messages = ymlgroupconfig['include_message']
                    wa_id = ymlgroupconfig['whatsapp_id']
                    tele_id = ymlgroupconfig['telegram_id']
                    webex_id = ymlgroupconfig['webex_id']
                    webex_room_id = ymlgroupconfig['webex_room_id']
                    sub_group = ymlgroupconfig['sub_group']

                    object = PythonSyslog(group, log_path, severities, out_mnemonics, in_mnemonics, out_messages, in_messages, wa_id, tele_id, webex_id, webex_room_id, sub_group)
                    x.append(object)
            except:
                print(f"Error opening {group_file}")

def run_python_syslog():
    for xx in x:
        print(f"\n---= {xx.group.upper()} =---")
        while True:
            xx.read1_log_date = xx.read_syslog_date()
            print(f"log is {xx.read1_log_date} seconds old")

            if xx.read_syslog():
                print(f"{len(xx.log_messages)} log lines detected")
                ## CROSSCHECK LOG FILE
                xx.read2_log_date = xx.read_syslog_date()
                if xx.read1_log_date == xx.read2_log_date:
                    ## TRUNCATE LOG FILE
                    xx.truncate_syslog()
                    break
                else:
                    print("new log detected mid process. rerunning")
            else:
                print("log empty")
                break

        ## PARSING LOGS
        if xx.log_messages != []:
            final_message = ""
            delimited_msg_check, delimited_msg = xx.delimite_log()
            if delimited_msg_check:
                processed_msg,filtered_msg = xx.filtering(delimited_msg)
                ## WRITE TO archive_syslog.log AND filtered_syslog.log
                xx.archive_syslog(processed_msg,filtered_msg)
                ## REMOVE DUPLICATE
                non_duplicate = xx.remove_duplicate(processed_msg)
                final_message = xx.beautify_log(non_duplicate)
            else:
                for msg in delimited_msg:
                    final_message += msg+"\n"
            ## SENDING MESSAGES
            if final_message != "":
                # print(final_message)
                xx.send_message(final_message)
                pass
            else:
                print(f"all messages are filtered out")

        print(f"\n=> Total Log Messages : {len(xx.log_messages)}")
        print(f"=> Filtered Messages : {xx.filtered_count}")
        print(f"=> Processed Messages : {xx.processed_count}")
        print(f"=> Trigger Meeting : {xx.trigger_meeting}")

        if xx.trigger_meeting:
            start_meeting(xx.webex_room_id, WEBEX_ACCESS_TOKEN)


read_groups()
run_python_syslog()

    

