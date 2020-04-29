var os_path = require('path');
var fs = require('fs');
const {remote} = require('electron');
const { dialog } = require('electron').remote;

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");

$("#install_path, #download_path").click(
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {properties: [ 'openDirectory' ] }).then(
            result => {
                if (result.canceled == false) {
                    this.value = result.filePaths;
                    save_settings.call(this);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


window.onload = function() {
    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);

        $("#install_path").val(settings.install_path);
        $("#download_path").val(settings.download_path);
        $("#delete_zip").prop("checked", settings.delete_zip);
        $("#force_install").prop("checked", settings.force_install);
        $("#wb_flags").val(settings.wb_flags);
    }

    set_default_tooltips_settings();
}

$("#install_path, #download_path, #password, #force_install, #delete_zip, #wb_flags").bind("change", save_settings);

var save_settings = function(){
  if (this.id == "force_install" || this.id == "delete_zip"){
    settings[this.id] = this.checked;
  } else {
    settings[this.id] = this.value;
  }

  let data = JSON.stringify(settings, null, 4);
  fs.writeFileSync(settings_path, data);

};