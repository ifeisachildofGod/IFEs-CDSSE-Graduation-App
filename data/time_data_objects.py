
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
    
    def to_str(self):
        return f"{self.hour}:{self.min}:{self.sec}"
    
    def normalize(self):
        min_add = self.hour % 1
        
        # Hour
        if not hasattr(self, "carry"):
            self.carry = 0
        
        self.carry += self.hour // 24
        
        self.hour //= 1
        self.hour %= 24
        
        self.hour = int(self.hour)
        
        # Minutes
        self.min += min_add * 60
        
        sec_add = self.min % 1
        
        self.hour += self.min // 60
        
        self.min //= 1
        self.min %= 60
        
        self.min = int(self.min)
        
        # Seconds
        self.sec += sec_add * 60
        
        self.min += self.sec // 60
        
        self.sec %= 60
        
        if self.hour >= 24 or self.min >= 60:
            self.normalize()
    
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
    
    def noramlize(self):
        self.time.normalize()
        self.date += self.time.carry
        
        orig_date = self.date
        
        m_list = list(MONTHS_OF_THE_YEAR)
        
        m_index = m_list.index(self.month)
        day_index = DAYS_OF_THE_WEEK.index(self.day)
        
        if self.date > MONTHS_OF_THE_YEAR[self.month]:
            self.date -= MONTHS_OF_THE_YEAR[self.month]
            
            self.month = m_list[(m_index + 1) % len(MONTHS_OF_THE_YEAR)]
            
            if m_index == len(MONTHS_OF_THE_YEAR) - 1:
                self.year += 1
            
            self.day = DAYS_OF_THE_WEEK[(day_index + (MONTHS_OF_THE_YEAR[self.month] + self.date - orig_date) % 7) % 7]
        elif self.date < 1:
            self.date += MONTHS_OF_THE_YEAR[self.month]
            
            self.month = m_list[m_index - 1]
            
            if m_index == 0:
                self.year -= 1
            
            self.day = DAYS_OF_THE_WEEK[(day_index - abs(orig_date - 1) % 7) % 7]
        
        del self.time.carry
    
    @staticmethod
    def str_to_period(str_time: str):
        day, month, date, _, year = str_time.split()
        
        day = next((dotw for dotw in DAYS_OF_THE_WEEK if day in dotw))
        month = next((moty for moty in MONTHS_OF_THE_YEAR if month in moty))
        date = int(date)
        year = int(year)
        
        return Period(Time.str_to_time(str_time), day, date, month, year)
    
    def to_str(self):
        return f"{self.time.to_str()}, {self.day}, {positionify(self.date)} {self.month}, {self.year}"
    
    def copy(self):
        return Period(self.time.copy(), self.day, self.date, self.month, self.year)

