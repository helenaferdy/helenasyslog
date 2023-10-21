import requests

WEBEX_API_TOKEN = 'OTU0M2NmMjMtN2E0Ni00MTM4LWJjYTMtODg2ZjQzN2MwZWI5MDQxNTNiZDAtMGU0_PF84_18a7bab3-8072-414f-ad6a-d2c44826aef8'
# WEBEX_ROOM_ID = '585432e0-568b-11ee-905f-850235f2dc7a'

HTTP_PROXY  = "http://10.167.0.5:8080"
HTTPS_PROXY = "http://10.167.0.5:8080"

proxies = { 
              "http"  : HTTP_PROXY, 
              "https" : HTTPS_PROXY
            }

def send_webex(message, room_id):
    # url = 'https://api.ciscospark.com/v1/messages'
    url = 'https://webexapis.com/v1/messages'

    headers = {
        'Authorization': f'Bearer {WEBEX_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        'roomId': room_id,
        'text': message
    }

    try:
        response = requests.post(url, headers=headers, json=data, proxies=proxies)

        if response.status_code == 200:
            print(f"* {response.status_code} : Webex Message sent successfully")
        else:
            print(f"* {response.status_code} : Failed to send Webex message")
            print(response.text)

    except Exception as e:
        print(f"Error exception: {str(e)}")

