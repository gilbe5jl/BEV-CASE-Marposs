import os
import shutil
from datetime import datetime, timedelta
import time
import logging

# Configuration Options
FOLDER_CONFIG = [
    {'path': r'E:\FTP\172.19.145.80\xg\hist', 'days_threshold': 12},
    {'path': r'E:\FTP\172.19.146.81\xg\hist', 'days_threshold': 12},
    {'path': r'E:\FTP\172.19.147.82\xg\hist', 'days_threshold': 12},
    {'path': r'E:\FTP\172.19.145.80\xg\result', 'days_threshold': 12},
    {'path': r'E:\FTP\172.19.146.81\xg\result', 'days_threshold': 12},
    {'path': r'E:\FTP\172.19.147.82\xg\result', 'days_threshold': 12},
    {'path': r'E:\Images', 'days_threshold': 45},
]

LOG_FILE = 'delete_old_files.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)


def delete_old_files(folder_path, days_threshold):
    try:
        current_time = datetime.now()

        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                age = current_time - file_modified_time

                if age > timedelta(days=days_threshold):
                    logging.info(f"Deleting file: {file_path}")
                    os.remove(file_path)

            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                dir_modified_time = datetime.fromtimestamp(os.path.getmtime(dir_path))
                age = current_time - dir_modified_time

                if age > timedelta(days=days_threshold):
                    logging.info(f"Deleting directory: {dir_path}")
                    shutil.rmtree(dir_path)

    except Exception as error:
        logging.error(f"An error occurred: {error}")


def main():
    while True:
        try:
            for config in FOLDER_CONFIG:
                delete_old_files(config['path'], config['days_threshold'])

            time.sleep(3600)  # Sleep for 1 hour

        except KeyboardInterrupt:
            logging.info("Script terminated by user (Ctrl+C)")
            break


if __name__ == "__main__":
    main()
