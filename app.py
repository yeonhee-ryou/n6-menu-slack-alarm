import json
import os
import re
import requests

from bs4 import BeautifulSoup as bs
from datetime import datetime
from slack_sdk import WebClient, errors


RET_NAMES = {
    "교수회관": "emp",
    "카이마루": "fclt"
}


def url(name, y, m, d):
    return f"https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd={name}&stt_dt={y}-{m:0>2}-{d:0>2}"


def get_data():
    menu = [get_menu(name) for name in RET_NAMES]
    return "\n".join(menu)


def get_menu(name):
    t = datetime.now()
    endpoint = url(RET_NAMES[name], t.year, t.month, t.day)
    req = requests.get(endpoint)
    
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
    skip_p = re.compile("\d+")
    for row in rows:
        for key, value in row.items():
            if "중식" in key:
                msg += f"* <{endpoint}|{name}> {key}\n"
                for line in value.splitlines():
                    sline = line.strip()
                    if sline.lower() == "kcal":
                        continue
                    if skip_p.match(sline):
                        continue
                    msg += f"> {sline}\n"
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
