import os
import requests
import json
import shutil
import subprocess
import wx
import re
from collections import OrderedDict
import pathlib
import xml.etree.ElementTree as ET
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

days_dict = {"Monday": "Mo",
             "Tuesday": "Tu",
             "Wednesday": "We",
             "Thursday": "Th",
             "Friday": "Fr",
             "Saturday": "Sa",
             "Sunday": "Su"}

# todo check if WB exists make automatic integration with EDT
# todo add windows notification when build is updated (maybe if password is wrong but need to check that it persists)
# todo create a function that alternates statusbar color on error message self.StatusBar.SetForegroundColour(wx.RED)
# todo https://wxpython.org/Phoenix/docs/html/wx.adv.NotificationMessage.html
class MyWindow(Ansys_Beta_Downloader_UI):
    def __init__(self, parent):
        Ansys_Beta_Downloader_UI.__init__(self, parent)

        self.username_text.Value = os.environ["USERNAME"]
        self.download_path_textbox.Value = os.environ["TEMP"]
        self.install_path_textbox.Value = self._get_previous_edt_path()
        appdata = os.environ["APPDATA"]
        self.settings_folder = os.path.join(appdata, "build_downloader")

        if not os.path.isdir(self.settings_folder):
            os.mkdir(self.settings_folder)

        # setup tasks viewlist
        self.schtasks_viewlist.AppendTextColumn('Product', width=60)
        self.schtasks_viewlist.AppendTextColumn('Version', width=50)
        self.schtasks_viewlist.AppendTextColumn('Schedule', width=175)
        self.get_active_schtasks()

        # todo create a directory when execute (os.makedirs())if not exists if user enters path manually
        self._init_combobox(artifactory_dict.keys(), self.artifactory_dropmenu, "Otterfing")
        self.artifacts_dict = {}

        self.password_json = os.path.join(self.settings_folder, "pass.json")
        if os.path.isfile(self.password_json):
            with open(self.password_json) as file:
                self.password_dict = json.load(file)
        else:
            self.password_dict = {}

        self.password_field.Value = self.password_dict.get(self.artifactory_dropmenu.Value, "")

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
        event.Skip()  # need to skip, otherwise stuck on field

        if not self.password.Value:
            return

        answer = self._add_message("Do you want to save password for {}?".format(self.artifactory_dropmenu.Value),
                                   "Save password?", "?")

        if answer == wx.ID_OK:
            self.password_dict[self.artifactory_dropmenu.Value] = self.password.Value
            with open(self.password_json, "w") as file:
                json.dump(self.password_dict, file)

    def get_artifacts_info(self, _unused_event):
        """Populate arifact_dict with versions and available dates for these versions"""
        # todo on change check file with passwords and grab pass from there, otherwise make focus on password field
        server = artifactory_dict[self.artifactory_dropmenu.Value]
        username = self.username_text.Value
        password = self.password_dict.get(self.artifactory_dropmenu.Value, "")
        # todo check if called after password changed and not save then we get password.Value otherwise dictionary
        self.password.Value = password
        if not username or not password:
            self.status_bar.SetStatusText("Please provide username and artifactory password")
            return

        try:
            with requests.get(server + "/api/repositories", auth=(username, password),
                              timeout=30) as url_request:
                artifacts_list = json.loads(url_request.text)
        except requests.exceptions.ReadTimeout:
            self.status_bar.SetStatusText("Timeout on connection, " +
                                          "please verify your username and password for {}".format(
                                              self.artifactory_dropmenu.Value))
            return

        # todo handle error on wrong pass
        for artifact in artifacts_list:
            repo = artifact["key"]
            if "Certified" in repo:
                version = repo.split("_")[0]
                if version not in self.artifacts_dict:
                    self.artifacts_dict[version] = [repo, []]

        for version in self.artifacts_dict:
            repo = self.artifacts_dict[version][0]
            url = server + "/api/storage/" + repo + "?list&deep=0&listFolders=1"
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

    def get_active_schtasks(self):
        """
        Function to get schtasks that are already scheduled for EDT and WB
        UI is updated with this info
        """

        command = r"schtasks /query /xml"
        all_tasks = subprocess.check_output(command, shell=True).decode("ascii", errors="ignore")
        all_tasks = all_tasks.split("\r\n\r\n\r\n")

        for task in all_tasks:
            if "AnsysDownloader" in task:
                task_data_dict = self.get_task_details(task)
                schedule_time = ", ".join(task_data_dict["days"]) + " at " + task_data_dict["time"]
                self.schtasks_viewlist.AppendItem([task_data_dict["product"],
                                                  task_data_dict["version"],
                                                  schedule_time])

    @staticmethod
    def get_task_details(task):
        """
        Function that extracts parameters of individual task
        :param task: XML string contained all data about the task
        :return task_data_dict = {"days": [],
                                  "time": "00:00",
                                  "product": "EDT",
                                  "version": "v201"}
        """

        task_data_dict = {"days": [],
                          "time": "00:00",
                          "product": "EDT",
                          "version": "v201"}

        task = "\n".join(task.replace("\r\n", "").split("\r")[1:])  # remove empty lines

        schtasks = ET.fromstring(task)
        ns = {"win": re.search("{(.*)}Task", schtasks.tag).group(1)}  # name space

        calendar_trig = schtasks.find("win:Triggers/win:CalendarTrigger", ns)
        start_boundary = calendar_trig.find("win:StartBoundary", ns).text
        days = calendar_trig.find("win:ScheduleByWeek/win:DaysOfWeek", ns)
        for day in days:
            day_name = days_dict[day.tag.split("}")[1]]
            task_data_dict["days"].append(day_name)

        task_data_dict["time"] = start_boundary.split("T")[1][:-3]

        uri = schtasks.find("win:RegistrationInfo/win:URI", ns)
        name = uri.text.split("\\")[2]
        task_data_dict["product"], task_data_dict["version"] = name.split("_")
        return task_data_dict

    @staticmethod
    def _get_previous_edt_path():
        """Function which returns path of EDT installation based on environment variable"""
        all_vars = os.environ
        env_var = ""
        for key in all_vars:
            if "ANSYSEM" in key:
                env_var = all_vars[key]

        if env_var:
            edt_root = str(pathlib.Path(env_var).parent.parent.parent)
            return edt_root
        else:
            return ""

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
