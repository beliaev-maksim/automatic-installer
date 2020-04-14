import logging
import os


def set_logger():
    """
    Function to setup logging output to stream and log file. Will be used by UI and backend
    :return: None
    """
    appdata = os.environ["APPDATA"]
    logging_file = os.path.join(appdata, "build_downloader", "downloader.log")

    if not os.path.isdir(os.path.dirname(logging_file)):
        os.mkdir(os.path.dirname(logging_file))

    # add logging to console and log file
    logging.basicConfig(filename=logging_file, format='%(asctime)s (%(levelname)s) %(message)s', level=logging.DEBUG,
                        datefmt='%d.%m.%Y %H:%M:%S')
    logging.getLogger().addHandler(logging.StreamHandler())
