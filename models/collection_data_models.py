
from typing import Any
from dataclasses import dataclass
from models.object_models import *

@dataclass
class AppData:
    teacher_cit: Time
    prefect_cit: Time
    
    teacher_cot: Time
    prefect_cot: Time
    
    teacher_timeline_dates: tuple[AttendanceEntry, AttendanceEntry]
    prefect_timeline_dates: tuple[AttendanceEntry, AttendanceEntry]
    
    teachers: dict[str, Teacher]
    prefects: dict[str, Prefect]
    
    sonar_safety_value: int
    
    variables: dict[str, Any]
    
    attendance_data: list[AttendanceEntry]


