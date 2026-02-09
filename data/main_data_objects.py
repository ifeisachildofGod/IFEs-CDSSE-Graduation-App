
from typing import Any
from dataclasses import dataclass
from data.data_objects import Teacher, Prefect, AttendanceEntry
from data.time_data_objects import Time, Period

@dataclass
class AppData:
    teacher_cit: Time
    prefect_cit: Time
    
    teacher_cot: Time
    prefect_cot: Time
    
    teacher_cin_border_interval_minutes: float | int
    teacher_cout_border_interval_minutes: float | int
    
    prefect_cin_border_interval_minutes: float | int
    prefect_cout_border_interval_minutes: float | int
    
    teacher_timeline_dates: list[tuple[Period, Period]]
    prefect_timeline_dates: list[tuple[Period, Period]]
    
    teachers: dict[str, Teacher]
    prefects: dict[str, Prefect]
    
    variables: dict[str, Any]
    
    attendance_data: list[AttendanceEntry]


