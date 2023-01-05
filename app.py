import json
import os
import requests

from bs4 import BeautifulSoup as bs
from datetime import datetime
from slack_sdk import WebClient, errors


def url(name, y, m, d):
    return f"https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd={name}&stt_dt={y}-{m:0>2}-{d:0>2}"


def get_data():
    t = datetime.now()
    req = requests.get(url("emp", t.year, t.month, t.day))
    
    soup = bs(req.text, "html.parser")
    table = soup.find("table")
    thead = soup.find("thead")
    field_names = [th.getText().strip() for th in thead.find_all("th")]
    rows = []
    for row in table.find("tbody").find_all("tr"):
        cells = [cell.getText().strip() for cell in row.find_all("td")]
        assert len(field_names) == len(cells)
        row = dict(zip(field_names, cells))
        rows.append(row)
    
    msg = ""
    for row in rows:
        for key, value in row.items():
            if "조식" not in key:
                msg += f"\n{key}\n"
                for line in value.splitlines():
                    msg += f"> {line.strip()}\n"
    return msg.strip()


def send_message(token, channel):
    client = WebClient(token=token)
    try:
        resp = client.chat_postMessage(channel=channel, text=get_data())
    except errors.SlackApiError as e:
        print(repr(e))
        raise e


if __name__ == "__main__":
    token=os.environ['SLACK_API_TOKEN']
    channel=os.environ['SLACK_LUNCH_CHANNEL']
    if not token:
        raise ValueError("environment variable 'SLACK_API_TOKEN' is not set")
    elif not channel:
        raise ValueError("environment variable 'SLACK_LUNCH_CHANNEL' is not set")
    else:
        send_message(token, channel)
