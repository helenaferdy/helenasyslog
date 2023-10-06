import requests

def send_whatsapp(message, chat_id):
    url = "http://localhost:5000/syslog"
    headers = {"Content-Type": "application/json", "Authorization":"Basic YWRtaW46Y2lzY28xMjM="}
    msg = {
                "id":chat_id,
                "status":message
            }

    try:
        response = requests.post(url, headers=headers, json=msg)
        
        if response.status_code == 200:
            print(f"* Whatsapp message sent : {response.status_code} : {response.json()}")
            return True
        else:
            print(f"* Failed sending whatsapp message : {response.status_code} : {response.json()}")
            return False
    except Exception as e:
        print(f"* Exception sending whatsapp message {e}")
        return False
    
def send_whatsapp_max(message, chat_id):
    GROUP_ID = chat_id

    url = "https://core.maxchat.id/mastersystem/api/messages"
    headers = {"Content-Type": "application/json", "Authorization": "bearer Pvv74Z0AxgWQMhZa"}
    msg = {
        "to": GROUP_ID,
        "type": "text",
        "text": message,
        "caption": "Rsyslog Monitoring System",
        "url": "https://www.fnordware.com/superpng/pnggrad16rgb.png"
        }

    try:
        response = requests.post(url, headers=headers, json=msg)

        if response.status_code == 200:
            print(f"* Whatsapp message sent : {response.status_code} : {response.json()['status']}")
            return True
        else:
            print(f"* Failed sending whatsapp message : {response.status_code} : {response.json()['error']}")
            return False
    except Exception as e:
        print(f"* Exception sending whatsapp message {e}")
        return False