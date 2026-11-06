from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO  = "info"
    SUCCESS = "success"