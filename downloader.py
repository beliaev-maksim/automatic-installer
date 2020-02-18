import requests
import json
import shutil
import wx
from downloader_ui_src import Ansys_Beta_Downloader_UI

class MyWindow(Ansys_Beta_Downloader_UI):
    def __init__(self, parent):
        Ansys_Beta_Downloader_UI.__init__(self, parent)


def main():
    """Main function to generate UI. Validate that only one instance is opened."""
    app = wx.App()
    ex = MyWindow(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()

# username = "mbeliaev"
# password = "AP4j2Kid4WoTzXdzHEs2AkMya6b"
# server = "http://milvmartifact.win.ansys.com:8080"
# repo = "v202_EBU_Certified-cache"
# with requests.get(server + "/artifactory/api/storage/" + repo + "?list&deep=0&listFolders=1", auth=(username, password),
#                   timeout=30) as url_request:
#     folder_dict_list = json.loads(url_request.text)['files']
#
# builds_dates = []
# for folder_dict in folder_dict_list:
#     folder_name = folder_dict['uri'][1:]
#     try:
#         builds_dates.append(int(folder_name))
#     except ValueError:
#         pass
#
# latest_build = max(builds_dates)
#
# url = server + r"/artifactory/" + repo + r"/" + str(latest_build) + r"/Electronics_202_winx64.zip"
# # url = server + r"/artifactory/v201_Licensing_Certified-cache/winx64/setup.exe"
#
# save_to = r"D:\C_replacement\Downloads\temp_build.zip"
#
#
# # save_to = r"D:\C_replacement\Downloads\setup.exe"
#
# # r = requests.get(url, auth=(username, password), timeout=30, , stream=True)
#
# # with open(save_to, 'wb') as zip_file:
# # for chunk in r.iter_content(chunk_size=8192):
# # if chunk:
# # zip_file.write(chunk)
#
#
# def download_file(url, save_to):
#     with requests.get(url, auth=(username, password), timeout=30, stream=True) as url_request:
#         with open(save_to, 'wb') as f:
#             shutil.copyfileobj(url_request.raw, f)
#
#
# download_file(url, save_to)
