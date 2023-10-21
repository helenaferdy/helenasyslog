import requests
from datetime import datetime, timedelta

# WEBEX_ACCESS_TOKEN = 'Yjc3ZTU0ODQtMjBlOS00ZWM0LTkwOGMtYmMxMmI5YjIzMTkwZjBiYzA4MGYtZWQy_PF84_18a7bab3-8072-414f-ad6a-d2c44826aef8'
# MEETING_ID = 'Y2lzY29zcGFyazovL3VzL1JPT00vNTg1NDMyZTAtNTY4Yi0xMWVlLTkwNWYtODUwMjM1ZjJkYzdh'
URL = 'https://webexapis.com/v1/meetings'
WEBEX_MEETING_DELAY = 5
TITLE = 'Meeting'

http_proxy  = "http://10.167.0.5:8080"
https_proxy = "http://10.167.0.5:8080"

proxies = { 
              "http"  : http_proxy, 
              "https" : https_proxy
            }

def get_date():
    raw_start = (datetime.utcnow() + timedelta(hours=7) + timedelta(minutes=WEBEX_MEETING_DELAY))
    start_time = raw_start.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    raw_end = raw_start + timedelta(hours=1)
    end_time = raw_end.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    print(f'\n* Start Time : {start_time}')
    print(f'* End Time : {end_time}')
    return start_time, end_time

def start_meeting(room_id, access_token):
    start_time, end_time = get_date()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'adhoc' : False,
        'roomId' : room_id, 
        'title' : TITLE,
        'start' : start_time,
        'end' : end_time,
        'allowAnyUserToBeCoHost' : True,
        'enabledJoinBeforeHost' : True,
        'enableConnectAudioBeforeHost' : True,
        'sendEmail' : True
    }

    try:
        response = requests.post(URL, headers=headers, json=data, proxies=proxies)

        if response.status_code == 200:
            print(f"* {response.status_code} : Meeting scheduled")
            # print(response.text)
        else:
            print(f"* {response.status_code} : Failed scheduling meeting")
            print(response.text)

    except Exception as e:
        print(f"Error meeting : {str(e)}")


def meeting_check():
    pass