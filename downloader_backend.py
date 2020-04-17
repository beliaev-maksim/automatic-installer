import argparse
import json
import logging
import os
import re
import shutil
import zipfile
from collections import namedtuple

import requests

import set_log
from downloader import artifactory_dict


class Downloader:
    """
        Main class that operates the download process:
        1. enables logs
        2. parses arguments to get settings file
        3. loads JSON to named tuple
        4. gets URL for selected version based on server
        5. downloads zip archive with BETA build
        """
    def __init__(self):
        set_log.set_logger()

        settings_path = parse_args()
        if not settings_path:
            return

        with open(settings_path, "r") as file:
            self.settings = json.load(file, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))


        url = get_build_link(self.settings)
        if url:
            zip_file = download_file(self.settings, url)
        else:
            logging.error("Cannot receive URL")

        if zip_file:
            install(zip_file)


def get_build_link(settings):
    """
    Function that sends HTTP request to JFrog and get the list of folders with builds for EDT and checks user password
    :param (namedtuple) settings: data parsed from settings file
    :return: (str) url: URL link to the latest build that will be used to download .zip archive
    """
    if not settings.username or not settings.password:
        logging.error("Please provide username and artifactory password")
        return False

    server = artifactory_dict[settings.artifactory]
    try:
        with requests.get(server + "/api/repositories", auth=(settings.username, settings.password),
                          timeout=30) as url_request:
            artifacts_list = json.loads(url_request.text)
    except requests.exceptions.ReadTimeout:
        logging.error("Timeout on connection, please verify your username and password for {}".format(
            settings.artifactory))
        return False

    # catch 401 for bad credentials or similar
    if url_request.status_code != 200:
        if url_request.status_code == 401:
            logging.error("Bad credentials, please verify your username and password for {}".format(
                settings.artifactory))
        else:
            logging.error(artifacts_list["errors"][0]["message"])
        return

    # fill the dictionary with EBU and WB keys since builds could be different
    # still parse the list because of different names on servers
    artifacts_dict = {}
    for artifact in artifacts_list:
        repo = artifact["key"]
        if "EBU_Certified" in repo:
            version = repo.split("_")[0] + "_EDT"
            if version not in artifacts_dict:
                artifacts_dict[version] = repo
        elif "Certified" in repo and "Licensing" not in repo:
            version = repo.split("_")[0] + "_WB"
            if version not in artifacts_dict:
                artifacts_dict[version] = repo

    repo = artifacts_dict[settings.version]

    if "EDT" in settings.version:
        url = server + "/api/storage/" + repo + "?list&deep=0&listFolders=1"
        with requests.get(url, auth=(settings.username, settings.password), timeout=30) as url_request:
            folder_dict_list = json.loads(url_request.text)['files']

        builds_dates = []
        for folder_dict in folder_dict_list:
            folder_name = folder_dict['uri'][1:]
            try:
                builds_dates.append(int(folder_name))
            except ValueError:
                pass

        latest_build = max(builds_dates)

        url = f"{server}/{repo}/{latest_build}/Electronics_{settings.version.split('_')[0][1:]}_winx64.zip"
    elif "WB" in settings.version:
        url = f"{server}/api/archive/download/{repo}-cache/winx64?archiveType=zip"
    else:
        return False
    return url


def download_file(settings, url, recursion=False):
    """
    Downloads file in chunks and saves to the temp.zip file
    :param (namedtuple) settings: settings from settings file
    :param (str) url: to the zip archive or special JFrog API to download WB folder
    :param (bool) recursion: Some artifactories do not have cached folders with WB  and we need recursively run
    the same function but with new_url, however to prevent infinity loop we need this arg
    :return: (str) destination_file: link to the zip file
    """
    with requests.get(url, auth=(settings.username, settings.password), timeout=30, stream=True) as url_request:
        if url_request.status_code == 404 and not recursion:
            # in HQ cached build does not exist and will return 404. Recursively start download with new url
            download_file(settings, url.replace("-cache", ""), True)
            return False

        destination_file = os.path.join(settings.download_path, f"temp_build_{settings.version}.zip")
        logging.info(f"Start download file from {url} to {destination_file}")
        with open(destination_file, 'wb') as f:
            shutil.copyfileobj(url_request.raw, f)

        logging.info(f"File is downloaded to: {destination_file}")
        return destination_file


def install(zip_file):
    # todo check that the same version is already installed or not before deletion
    target_dir = zip_file.replace(".zip", "")
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(target_dir)

    logging.info(f"File is unpacked to {target_dir}")

    product_id = parse_iss(target_dir)
    if product_id:
        logging.info(f"Product ID is {product_id}")
    else:
        logging.error("Unable to extract product ID")
        return


def uninstall(settings):
    pass


def parse_iss(dir_name):
    default_iss_file = ""
    for dir_path, dir_names, file_names in os.walk(dir_name):
        for filename in file_names:
            if "AnsysEM" in dir_path and filename.endswith(".iss"):
                default_iss_file = os.path.join(dir_path, filename)
                break

    if not default_iss_file:
        return False

    try:
        with open(default_iss_file, "r") as iss_file:
            for line in iss_file:
                if "DlgOrder" in line:
                    product_id = re.findall("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", line)[0]
                    return product_id
    except IndexError:
        return False


def parse_args():
    """
    Function to parse arguments provided to the script. Search for -p key to get settings path
    :return: settings_path: path to the configuration file
    """
    parser = argparse.ArgumentParser()
    # Add long and short argument
    parser.add_argument("--path", "-p", help="set path to the settings file generated by UI")
    args = parser.parse_args()

    if args.path:
        settings_path = args.path
        if not os.path.isfile(settings_path):
            logging.error("Settings file does not exist")
            return False

        logging.info(f"Settings path is set to {settings_path}")
    else:
        return False

    return settings_path


if __name__ == "__main__":
    main()
