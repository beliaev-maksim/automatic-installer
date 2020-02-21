import os
import requests
import json
import shutil
import wx
from collections import OrderedDict
from downloader_ui_src import Ansys_Beta_Downloader_UI

artifactory_dict = OrderedDict([
    ('Austin', r'http://ausatsrv01.ansys.com:8080/artifactory'),
    ('Boulder', r'http://bouatsrv01:8080/artifactory'),
    ('Canonsburg', r'http://canartifactory.ansys.com:8080/artifactory'),
    ('Concord', r'http://convmartifact.win.ansys.com:8080/artifactory'),
    ('Darmstadt', r'http://darvmartifact.win.ansys.com:8080/artifactory'),
    ('Evanston', r'http://evavmartifact:8080/artifactory'),
    ('Gothenburg', r'http://gotvmartifact1:8080/artifactory'),
    ('Hannover', r'http://hanartifact1.ansys.com:8080/artifactory'),
    ('Horsham', r'http://horvmartifact1.ansys.com:8080/artifactory'),
    ('Lebanon', r'http://lebartifactory.win.ansys.com:8080/artifactory'),
    ('Lyon', r'http://lyovmartifact.win.ansys.com:8080/artifactory'),
    ('MiltonPark', r'http://milvmartifact.win.ansys.com:8080/artifactory'),
    ('Otterfing', r'http://ottvmartifact.win.ansys.com:8080/artifactory'),
    ('Pune', r'http://punvmartifact.win.ansys.com:8080/artifactory'),
    ('Sheffield', r'http://shfvmartifact.win.ansys.com:8080/artifactory'),
    ('SanJose', r'http://sjoartsrv01.ansys.com:8080/artifactory'),
    ('Waterloo', r'http://watatsrv01.ansys.com:8080/artifactory')
])


class MyWindow(Ansys_Beta_Downloader_UI):
    def __init__(self, parent):
        Ansys_Beta_Downloader_UI.__init__(self, parent)

        self.username_text.Value = os.environ["USERNAME"]
        self.download_path_textbox.Value = os.environ["TEMP"]
        # todo create a directory when execute (os.makedirs())if not exists if user enters path manually
        self._init_combobox(artifactory_dict.keys(), self.artifactory_dropmenu, "Otterfing")
        self.artifacts_dict = {}

    def set_install_path(self, _unused_event):
        """Invoked when clicked on "..." set_path_button."""
        path = self._path_dialogue("Install")
        if path:
            self.install_path_textbox.Value = path

    def set_download_path(self, _unused_event):
        """Invoked when clicked on "..." set_path_button."""
        path = self._path_dialogue("Download")
        if path:
            self.download_path_textbox.Value = path

    def save_question(self, event):
        """Function is fired up when you leave field of entering password"""
        self._add_message("Do you want to save password for {}?".format(self.artifactory_dropmenu.Value),
                          "Save password?", "?")
        event.Skip()  # need to skip, otherwise stuck on field

    def get_artifacts_info(self, _unused_event):
        """Populate arifact_dict with versions and available dates for these versions"""
        # todo on change check file with passwords and grab pass from there, otherwise make focus on password field
        server = artifactory_dict[self.artifactory_dropmenu.Value]
        username = self.username_text.Value
        password = self.password.Value
        if not username or not password:
            # todo log entry
            return

        with requests.get(server + "/artifactory/api/repositories", auth=(username, password),
                          timeout=30) as url_request:
            artifacts_list = json.loads(url_request.text)

        for artifact in artifacts_list:
            repo = artifact["key"]
            if "Certified" in repo:
                version = repo.split("_")[0]
                if version not in self.artifacts_dict:
                    self.artifacts_dict[version] = [repo, []]

        for version in self.artifacts_dict:
            repo = self.artifacts_dict[version][0]
            url = server + "/artifactory/api/storage/" + repo + "?list&deep=0&listFolders=1"
            with requests.get(url, auth=(username, password), timeout=30) as url_request:
                folder_dict_list = json.loads(url_request.text)['files']

            builds_dates = self.artifacts_dict[version][1]
            for folder_dict in folder_dict_list:
                folder_name = folder_dict['uri'][1:]
                try:
                    builds_dates.append(int(folder_name))
                except ValueError:
                    pass

        self._init_combobox(self.artifacts_dict.keys(), self.version_dropmenu, sorted(self.artifacts_dict.keys())[-1])
        builds_dates = self.artifacts_dict[self.version_dropmenu.Value][1]
        self._init_combobox(builds_dates, self.date_dropmenu, max(builds_dates))

    @staticmethod
    def _path_dialogue(which_dir):
        """Creates a dialogue where user can select directory"""
        get_dir_dialogue = wx.DirDialog(None, "Choose {} directory:".format(which_dir), style=wx.DD_DEFAULT_STYLE)
        if get_dir_dialogue.ShowModal() == wx.ID_OK:
            path = get_dir_dialogue.GetPath()
            get_dir_dialogue.Destroy()
            return path
        else:
            get_dir_dialogue.Destroy()
            return False

    @staticmethod
    def _init_combobox(entry_list, combobox, default_value=''):
        """
        Fills a wx.Combobox element with the entries in a list
        Input parameters
        :param entry_list: List of text entries to appear in the combobox element
        :param combobox: object pointing to the combobox element
        :param default_value: (optional default value (must be present in the entry list, otherwise will be ignored)

        Outputs
        :return: None
        """
        combobox.Clear()
        index = 0
        for i, v in enumerate(list(entry_list)):
            if v == default_value:
                index = i
            combobox.Append(v)
        combobox.SetSelection(index)

    @staticmethod
    def _add_message(message, title="", icon="?"):
        """
        Create a dialog with different set of buttons
        :param message: Message you want to show
        :param title:
        :param icon: depending on the input will create either question dialogue (?), error (!) or just information
        :return Answer of the user eg wx.OK
        """

        if icon == "?":
            icon = wx.OK | wx.CANCEL | wx.ICON_QUESTION
        elif icon == "!":
            icon = wx.OK | wx.ICON_ERROR
        else:
            icon = wx.OK | wx.ICON_INFORMATION

        dlg_qdel = wx.MessageDialog(None, message, title, icon)
        result = dlg_qdel.ShowModal()
        dlg_qdel.Destroy()

        return result


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
