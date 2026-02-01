
from dataclasses import dataclass

DAYS_OF_THE_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_OF_THE_YEAR = {
    "January": 31,
    "February": 29,
    "March": 31,
    "April": 30,
    "May": 31,
    "June": 30,
    "July": 31,
    "August": 31,
    "September": 30,
    "October": 31,
    "November": 30,
    "December": 31,
}

def positionify(number: int | str, default: str | None = ...):
    if isinstance(number, int):
        number = str(number)
    
    suffix = ("st" if number.endswith("1") and number != "11" else ("nd" if number.endswith("2") and number != "12" else "rd" if number.endswith("3") and number != "13" else "th"))
    
    if not number.isnumeric():
        if not isinstance(default, ellipsis):
            suffix = (default if default is not None else "")
        else:
            raise Exception(f"Text: ({number}) is not numeric")
        
    return number + suffix

@dataclass
class Time:
    hour: int
    min: int
    sec: float
    
    def in_seconds(self):
        return self.sec + self.min * 60 + self.hour * 60 * 60
    
    def in_minutes(self):
        return self.in_seconds() / 60
    
    def in_hours(self):
        return self.in_minutes() / 60
    
    @staticmethod
    def str_to_time(str_time: str):
        _, _, _, t, _ = str_time.split()
        hour, min, sec = t.split(":")
        
        return Time(int(hour), int(min), int(sec))
    
    def copy(self):
        return Time(self.hour, self.min, self.sec)

S_DAY = Time(24, 0, 0).in_seconds()
S_WEEK = S_DAY * 7
def S_MONTH(month: str):
    return S_DAY * MONTHS_OF_THE_YEAR[month]
S_YEAR = S_DAY * 365

@dataclass
class Period:
    time: Time
    day: str
    date: int
    month: str
    year: int
    
    def in_seconds(self):
        focus_months = list(MONTHS_OF_THE_YEAR.values())[:list(MONTHS_OF_THE_YEAR).index(self.month)] + [0]
        
        days = sum(focus_months) + self.date - 1
        
        return self.time.in_seconds() + days * 24 * 60 * 60
    
    def in_minutes(self):
        return self.in_seconds() / 60
    
    def in_hours(self):
        return self.in_minutes() / 60
    
    def in_days(self):
        return self.in_hours() / 24
    
    def in_weeks(self):
        return self.in_days() / 7
    
    @staticmethod
    def str_to_period(str_time: str):
        day, month, date, _, year = str_time.split()
        
        day = next((dotw for dotw in DAYS_OF_THE_WEEK if day in dotw))
        month = next((moty for moty in MONTHS_OF_THE_YEAR if month in moty))
        date = int(date)
        year = int(year)
        
        return Period(Time.str_to_time(str_time), day, date, month, year)
    
    def copy(self):
        return Period(self.time.copy(), self.day, self.date, self.month, self.year)

