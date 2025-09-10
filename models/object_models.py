
from os import PathLike
from models.data_models import *
from dataclasses import dataclass

@dataclass
class Class:
    id: str
    
    name: str

@dataclass
class Subject:
    id: str  # Not unique
    
    name: str
    cls: Class
    periods: list[tuple[str, int]]

@dataclass
class Staff:
    id: str
    IUD: str | None
    
    name: CharacterName
    img_path: str | PathLike

@dataclass
class Teacher(Staff):
    department: Department
    subjects: list[Subject]
    attendance: list["AttendanceEntry"]

@dataclass
class Prefect(Staff):
    post_name: str
    cls: Class
    duties: dict[str, list[str]]
    attendance: list["AttendanceEntry"]


@dataclass
class AttendanceEntry:
    time: Time
    day: str
    date: int
    month: str
    year: int
    
    is_check_in: bool = True
    
    staff: Staff | None = None


@dataclass
class Sensor:
    name: str
    comm_system: ... # type:BaseCommSystem

