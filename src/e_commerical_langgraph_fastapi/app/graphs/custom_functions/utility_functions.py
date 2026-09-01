import csv
import chardet
from pathlib import Path
import requests
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.environ["EMAIL"]

FAIL="failed"
SUCCESS="success"
USER_AGENT_INFO=f"MyPersonalAgentApp/1.0 ({EMAIL})"
HEADER={
    "User-Agent":USER_AGENT_INFO
}

def handle_web_requests(url: str):
    try:
        # Fixed: Changed 'request' to 'requests.get'
        respond = requests.get(url=url, timeout=2, headers=HEADER)
        
        if respond.status_code == 200:
            return (respond, SUCCESS)
        else:
            # Fixed: Changed '{e}' to '{respond.status_code}' and '{respond.reason}'
            error_msg = f"Error Failed due to status_code: {respond.status_code} Reason: {respond.reason}"
            return (error_msg, FAIL)
            
    except Exception as e:
        error_msg = f"Error Failed to handle_web_requests reason : {e}"
        return (error_msg, FAIL)

#################################################################
def get_encoding(filepath) -> str:
    """Given a filepath it will read it as binary text file to detect its encoding, note encoding detection is not 100% accurate"""
    with open(filepath,mode="rb") as file:
        raw_content_binary = file.read()
        result = chardet.detect(raw_content_binary)
        return result["encoding"]


def locate_file(filepath, allowed_time=30) -> Path | str:
    """given filepath it checks if it exists else it will search for file based on filename in current directory,
    then correct filepath"""

    file_path = Path(filepath)
    if file_path.is_file():
        return file_path
    else:
        target=file_path.name
        extension=file_path.suffix
        root = Path(Path.cwd())
        files_seen=0
        for file in root.rglob(f"*{extension}"):
            if file.is_file() and file.name == target:
                return file
            files_seen+=1
            if files_seen==allowed_time:
                return FAIL
    print(f"error does not exist {filepath}")
    return FAIL



def pythonic_text_clean(target_string: str) -> str:
    """using only pythonic methods to clean large string documents"""
    url_pattern=r"https://[^\s]+"
    email_pattern=r"[A-Za-z0-9]+[@]{1}[^\s]*"
    phone_pattern=r"[0-9]+[-]{1}[0-9]+[^\s]*"
    soup_string = BeautifulSoup(target_string,"html.parser")
    string_without_tags = soup_string.get_text()
    string_stripped = string_without_tags.strip() #remove whitespaces    
    urls = re.findall(url_pattern,string_stripped)
    emails = re.findall(email_pattern,string_stripped)
    phones = re.findall(phone_pattern,string_stripped)
    stuff_to_remove = [urls,emails,phones]
    for list_to_remove in stuff_to_remove:
        for substring in list_to_remove:
            string_stripped = string_stripped.replace(substring,"")
    string_stripped  = string_stripped.replace("\n","")
    string_stripped  = string_stripped.replace("\t","")

    #removing all white spaces but leaving a single space in between words
    split_string = string_stripped.split()
    string = " ".join(split_string)
    return string


