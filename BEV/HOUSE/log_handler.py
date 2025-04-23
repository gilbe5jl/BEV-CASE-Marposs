import os
import logging
from datetime import timedelta,time
# from datetime import datetime 
import datetime
# from time import sleep
import time




class PhoenixLogger:
    def __init__(self):
        self.station_nums = ['3','4']
        self.loggers = self.log_gen()
    def configure_logger(self,logger_name,log_file_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file_name)
        now = datetime.datetime.now().strftime("%I:%M:%S")
        formatter = logging.Formatter(f"{now}-%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        return logger
    def log_gen(self):
        today = datetime.datetime.now().strftime("%a-%b-%d-%Y")
        log_files = [f"Station({num})-{today}.log" for num in self.station_nums]
        loggers =[]
        for num, log_file in zip(self.station_nums, log_files):
            logger = self.configure_logger(f"Station_{num}_Logger", log_file)
            loggers.append(logger)
        return loggers
    def delete_old_logs(self):
        yesterday = (datetime.datetime.now() - timedelta(days=1)).strftime("%a-%b-%d-%Y")
        log_files = [f"Station({num})-{yesterday}.log" for num in self.station_nums]
        try:
            for log_file in log_files:
                os.remove(log_file)
        except FileNotFoundError as error:
            pass
    def log_print(self,station_num:str,message:str)->None:
        for station in self.station_nums:
            if station == station_num:
                logger = self.loggers[self.station_nums.index(station)]
                logger.info(message)
                print(f"({station_num}){message}\n")