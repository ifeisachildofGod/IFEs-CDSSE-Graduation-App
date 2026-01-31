
from os import PathLike
from data.metadata_objects import *
from data.time_data_objects import Period
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
    
    attendance: list["AttendanceEntry"]

@dataclass
class Teacher(Staff):
    department: Department
    subjects: list[Subject]

@dataclass
class Prefect(Staff):
    post_name: str
    cls: Class
    duties: dict[str, list[str]]


@dataclass
class AttendanceEntry:
    period: Period
    
    staff: Staff
    
    is_check_in: bool = True
