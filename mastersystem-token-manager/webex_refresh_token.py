import requests
import os
import yaml
import time, datetime

HTTP_PROXY  = "http://10.167.0.5:8080"
HTTPS_PROXY = "http://10.167.0.5:8080"

CURRENT_TIME = int(time.time())
CURRENT_DATE = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\n\n-----------------------------")
print(f"--- {CURRENT_DATE}")


# DIR_SYSLOG = '../mastersystem-syslog/conf/'
# DIR_CONNECTOR = '../mastersystem-connector/config/'

DIR_SYSLOG = '/opt/mastersystem-syslog/conf/'
DIR_CONNECTOR = '/opt/mastersystem-connector/config/'

token_url = "https://webexapis.com/v1/access_token"
client_id = "C545c21bd8bdf6668cbeee2f874691c1895bd390e75802fecd9e4c3f9eedc9d7a"
client_secret = "35a36975b94ea1a19b1999c035d944cdcf92d6d2694cf7b8820df79fb2fb65d3"


##check dir
if os.path.isdir(DIR_SYSLOG):
    print('Mastersystem Syslog')
    CONFIG_PATH = DIR_SYSLOG+'config.yml'
elif os.path.isdir(DIR_CONNECTOR):
    print('Mastersystem Connector')
    CONFIG_PATH = DIR_CONNECTOR+'config.yml'

try:
    with open(CONFIG_PATH, "r") as yml_file:
        print(f'Opened : {CONFIG_PATH}')
        ymlconfig = yaml.safe_load(yml_file)
except:
    print("Error opening config file")


proxies = {
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }

REFRESH_TOKEN = ymlconfig["access_token_refresh"]

payload = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN,
    "client_id": client_id,
    "client_secret": client_secret
}

response = requests.post(token_url, data=payload, proxies=proxies)

if response.status_code == 200:
    new_access_token = response.json().get("access_token")
    new_refresh_token = response.json().get("refresh_token")
    print(f"New Access Token: {new_access_token}")
    print(f"New Refresh Token: {new_refresh_token}")
else:
    print(f"Error refreshing token: {response.status_code}")
    print(response.text)


ymlconfig["access_token"] = new_access_token
ymlconfig["access_token_refresh"] = new_refresh_token

try:
    with open(CONFIG_PATH, "w") as yml_file:
        yaml.dump(ymlconfig, yml_file, default_flow_style=False)
        print(f'Updated : {CONFIG_PATH}')
except:
    print("Error updating access token")