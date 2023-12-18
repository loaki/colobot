import requests
import json
from datetime import date
from dateutil import relativedelta

TOKEN = "YzFhNWZjZjUtNjA4ZS00MzZlLWFjYmYtMDllYzM0NTU5ZjEzOjBmYjdmOWRlLWFiNDYtNGU5Yy1hYWMyLTRhZDU5NGY5MTQ4MA=="

auth_url = "https://digital.iservices.rte-france.com/token/oauth"
tempo_url = "https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
headers = {"Authorization": f"Basic {TOKEN}"}
response = requests.get(auth_url, headers=headers)
if response.status_code == requests.codes.ok:
    r_json = json.loads(response.text)
    headers = {"Authorization": f"Bearer {r_json.get('access_token')}"}
    today = date.today()
    tomorrow = today + relativedelta.relativedelta(days=2)
    data = {
        "start_date": today.strftime("%Y-%m-%dT00:00:00+01:00"),
        "end_date": tomorrow.strftime("%Y-%m-%dT00:00:00+01:00")
    }
    response = requests.get(tempo_url, headers=headers, params=data)
    if response.status_code == requests.codes.ok:
        r_json = json.loads(response.text)
        today_color = r_json["tempo_like_calendars"]["values"][1]["value"]
        tomorrwo_color = r_json["tempo_like_calendars"]["values"][0]["value"]
        print(today_color)
        print(tomorrwo_color)