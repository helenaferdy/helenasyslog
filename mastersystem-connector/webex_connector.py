import requests
import asyncio
import os
import time, datetime
import yaml
from sendtelegram import send_telegram
from sendwhatsapp import send_whatsapp

TESTING_ENV = False

CONFIG_PATH = '/opt/mastersystem-connector/config/config.yml'
GROUP_PATH = '/opt/mastersystem-connector/groups/'

if TESTING_ENV:
    CONFIG_PATH = 'config/config.yml'
    GROUP_PATH = 'groups/'

# HTTP_PROXY  = "http://10.167.0.5:8080"
# HTTPS_PROXY = "http://10.167.0.5:8080"

class PythonConnector:
    def __init__(self, ymlgroupconfig, access_token, config_group_name, config_group_full_path, config_telegram_id, config_whatsapp_id, config_webex_id, config_webex_room_id, config_chat_id):
        self.ymlgroupconfig = ymlgroupconfig
        self.access_token = access_token
        self.config_group_name = config_group_name
        self.config_group_full_path = config_group_full_path
        self.config_telegram_id = config_telegram_id
        self.config_whatsapp_id = config_whatsapp_id
        self.config_webex_id = config_webex_id
        self.config_room_id = config_webex_room_id
        self.config_chat_id = config_chat_id

        self.max_msg_retrieved = 10
        self.message = ''
        self.bot_email_address = 'mastersystem_syslog@webex.bot'

        self.datas = []

    def read_message(self):
        url = f'https://webexapis.com/v1/messages?roomId={self.config_room_id}&max={self.max_msg_retrieved}'
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # proxies = { 
        #       "http"  : HTTP_PROXY, 
        #       "https" : HTTPS_PROXY
        #     }

        try:
            response = requests.get(url,headers=headers)

            if response.status_code == 200:
                self.datas = response.json()['items']
                for data in self.datas:
                    if data['personEmail'] == self.bot_email_address:
                        self.id = data['id']
                        self.email = data['personEmail']
                        self.message = data['text']

                        print('\n**************************************************************************************************************')
                        print(self.message)
                        print('**************************************************************************************************************\n')
                        return True
            else:
                print(response.status_code, response.content)
                return False
        except Exception as e:
            print(f'* Exception: {e}')
            return False
        
    def read_message_summary(self):
        pass

    def check_id(self):
        if self.config_chat_id == self.id:
            print('* No new messages')
            return False
        else:
            return self.update_id()

    def update_id(self):
        self.ymlgroupconfig["last_message_id"] = self.id
        try:
            with open(self.config_group_full_path, "w") as yml_file:
                yaml.dump(self.ymlgroupconfig, yml_file, default_flow_style=False)
            return True
        except:
            print("* Error updating message id")
            return False

    def send_message(self):
        send_whatsapp(self.message, self.config_whatsapp_id)
        asyncio.run(send_telegram(self.message, self.config_telegram_id))



CURRENT_TIME = int(time.time())
CURRENT_DATE = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\n\n-----------------------------")
print(f"--- {CURRENT_DATE}")


## OPEN CONFIG FILE
try:
    with open(CONFIG_PATH, "r") as yml_file:
        ymlconfig = yaml.safe_load(yml_file)
except:
    print("* Error opening config file")

ACCESS_TOKEN = ymlconfig["access_token"]

x = []
def read_groups():
    group_list = os.listdir(GROUP_PATH)

    for group_file in group_list:
        group_full_path = os.path.join(GROUP_PATH, group_file)
        
        if os.path.isfile(group_full_path):
            try:
                with open(group_full_path, "r") as yml_file:
                    ymlgroupconfig = yaml.safe_load(yml_file)

                    config_group_name = group_file[:-4]
                    config_telegram_id = ymlgroupconfig['telegram_id']
                    config_whatsapp_id = ymlgroupconfig['whatsapp_id']
                    config_webex_id = ymlgroupconfig['webex_id']
                    config_webex_room_id = ymlgroupconfig['webex_room_id']
                    config_chat_id = ymlgroupconfig['last_message_id']

                    object = PythonConnector(ymlgroupconfig, ACCESS_TOKEN, config_group_name, group_full_path, config_telegram_id, config_whatsapp_id, config_webex_id, config_webex_room_id, config_chat_id)
                    x.append(object)
            except:
                print(f"* Error opening {group_file}")
    

read_groups()
for xx in x:
    print(f"\n---= {xx.config_group_name.upper()} =---")
    if xx.read_message():
        if xx.check_id():
            if not TESTING_ENV:
                xx.send_message()
            # else:
            #     print(xx.message)
    


