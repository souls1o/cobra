import datetime
from colorama import init, Fore, Style

init(autoreset=True)

class Logger:
    COLORS = {
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.GREEN,
        "SUCCESS": Fore.MAGENTA
    }

    LOG_FILES = {
        "BOT": "bot.log",
        "SERVER": "server.log"
    }

    def __init__(self, name: str = "Logger"):
        if name not in self.LOG_FILES:
            raise ValueError("Logger name must be 'Bot' or 'Server'.")
        self.name = name
        self.log_file = self.LOG_FILES[name]

    def _log(self, level: str, message: str):
        timestamp = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        color = self.COLORS.get(level, Fore.WHITE)

        print(f"{color}({timestamp}) [{level}] {message}{Style.RESET_ALL}")

        if level == "ERROR":
            with open(f"logs/{self.log_file}", "a") as f:
                f.write(f"[{timestamp}] {message}\n")


    def info(self, message: str):
        self._log("INFO", message)

    def warning(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)

    def debug(self, message: str):
        self._log("DEBUG", message)

    def success(self, message: str):
        self._log("SUCCESS", message)