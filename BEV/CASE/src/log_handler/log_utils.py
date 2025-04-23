import logging
import os
from datetime import datetime, timedelta

class Logger:
    """
    Handles logging for multiple machines, automatically creating daily logs 
    and deleting outdated logs.
    """

    LOG_DIR = "logs"  # Define directory to store log files

    def __init__(self, machine_ids=None):
        """
        Initializes loggers for the specified machine IDs.

        :param machine_ids: List of machine IDs to create loggers for.
        """
        if machine_ids is None:
            machine_ids = ["3", "4"]  # Default machines if none provided

        self.loggers = {}
        today = datetime.now().strftime("%a-%b-%d-%Y")  # Get today's date for filename

        # Ensure log directory exists
        os.makedirs(self.LOG_DIR, exist_ok=True)

        # Create loggers for each machine
        for machine_id in machine_ids:
            log_file = os.path.join(self.LOG_DIR, f"BEV-Case-Thread({machine_id})-{today}.log")
            self.loggers[machine_id] = self._configure_logger(f"Logger_{machine_id}", log_file)

    def _configure_logger(self, logger_name, log_file_name):
        """
        Configures an individual logger.

        :param logger_name: Name of the logger.
        :param log_file_name: File path to store log.
        :return: Configured logger object.
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler(log_file_name)
        now = datetime.now().strftime("%I:%M:%S.%f")[:-3]  # Includes milliseconds, trims to 3 decimal places
        formatter = logging.Formatter(f"{now} - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False
        return logger
    
    def out(self, log_data):
        """
        Logs messages for specified machines.

        :param log_data: 
            - If a dictionary -> logs specific messages per machine. Example: { "3": "message1", "4": "message2" }
            - If a string -> logs the same message to all available loggers.
        """
        # print(self.loggers)
        if isinstance(log_data, dict):
            for machine_num, message in log_data.items():
                machine_int = int(machine_num)  # Ensure machine number is string
                if machine_int in self.loggers:
                    self.loggers[machine_int].info(message)
                    print(f"({machine_int}){message}")
                else:
                    print(f"⚠️ No logger found for Machine {machine_num}")
        elif isinstance(log_data, str):
            for machine_num, logger in self.loggers.items():
                logger.info(log_data)
        else:
            print("⚠️ Invalid log data type. Must be a dict or string.")

    def delete_old_logs(self, days_old=1):
        """
        Deletes log files older than the specified number of days.

        :param days_old: Number of days old a log file must be to be deleted.
        """
        old_date = (datetime.now() - timedelta(days=days_old)).strftime("%a-%b-%d-%Y")

        for machine_id in self.loggers.keys():
            old_log_file = os.path.join(self.LOG_DIR, f"Machine({machine_id})-{old_date}.log")
            try:
                os.remove(old_log_file)
                print(f"🗑️ Deleted old log: {old_log_file}")
            except FileNotFoundError:
                pass  # Ignore if file doesn't exist

# Example Usage:
# logger = Logger(machine_ids=[3, 4])  # Initialize logger for machines 3 and 4
# logger.out(3, "Inspection started.")  # ✅ Logs message for Machine 3
# logger.out(4, "Inspection complete.")  # ✅ Logs message for Machine 4
# logger.delete_old_logs(days_old=0)  # 🗑️ Cleans up logs from yesterday