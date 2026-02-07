
from widgets.base_widgets import *
from widgets.extra_widgets import *
from data.time_data_objects import positionify


class _CharacterNameWidget(QWidget):
    def __init__(self, name: CharacterName):
        super().__init__()
        self.name = name
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        widget_2_1 = QWidget()
        layout_2_1 = QVBoxLayout()
        widget_2_1.setLayout(layout_2_1)
        
        widget_2_1_1 = QWidget()
        layout_2_1_1 = QHBoxLayout()
        widget_2_1_1.setLayout(layout_2_1_1)
        layout_2_1.addWidget(widget_2_1_1)
        
        name_1 = LabeledField("Surname", QLabel(self.name.sur))
        name_2 = LabeledField("First name", QLabel(self.name.first))
        name_3 = LabeledField("Middle name", QLabel(self.name.middle))
        
        layout_2_1_1.addWidget(name_1)
        layout_2_1_1.addWidget(name_2)
        layout_2_1_1.addWidget(name_3)
        
        widget_2_1_2 = QWidget()
        layout_2_1_2 = QHBoxLayout()
        widget_2_1_2.setLayout(layout_2_1_2)
        layout_2_1.addWidget(widget_2_1_2)
        
        name_4 = LabeledField("Other name", QLabel(self.name.other if self.name.other is not None else "No other name"))
        name_5 = LabeledField("Abbreviation", QLabel(self.name.abrev))
        
        layout_2_1_2.addWidget(name_4)
        layout_2_1_2.addWidget(name_5, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(LabeledField("Names", widget_2_1, height_policy=QSizePolicy.Policy.Maximum))

    

class AttendanceTeacherEntryWidget(BaseAttendanceEntryWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Teacher", data)
        
        self.labeled_container.setProperty("class", "AttendanceTeacherEntryWidget")
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.min < 10 else "") + str(self.data.period.time.min))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.sec < 10 else "") + str(self.data.period.time.sec))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = _CharacterNameWidget(self.staff.name)
        layout_2.addWidget(name_widget)
        
        _, layout_2_2 = create_widget(layout_2, QVBoxLayout)
        
        widget_2_2_2, layout_2_2_2 = create_scrollable_widget(None, QVBoxLayout)
        
        layout_2_2.addWidget(LabeledField("Subjects", widget_2_2_2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        periods_data: dict[tuple[str, str], dict[tuple[str, str], list[int]]] = {}
        
        for subject in self.staff.subjects:
            for day_name, period in subject.periods:
                if self.data.period.day == day_name:
                    key = subject.id, subject.name
                    sub_key = subject.cls.id, subject.cls.name
                    
                    if periods_data.get(key) is None:
                        periods_data[key] = {}
                    if periods_data[key].get(sub_key) is None:
                        periods_data[key][sub_key] = []
                    periods_data[key][sub_key].append(period)
        
        for (_, subject_name), subject_data in periods_data.items():
            widget_2_2_2_1, layout_2_2_2_1 = create_widget(None, QGridLayout)
            
            for index, ((_, cls_name), periods) in enumerate(subject_data.items()):
                widget_2_2_2_1_1, layout_2_2_2_1_1 = create_widget(None, QVBoxLayout)
                for period in periods:
                    layout_2_2_2_1_1.addWidget(QLabel(f"{positionify(str(period))} period"), alignment=Qt.AlignmentFlag.AlignTop)
                layout_2_2_2_1.addWidget(LabeledField(cls_name, widget_2_2_2_1_1), int(index / 3), index % 3)
            layout_2_2_2.addWidget(LabeledField(subject_name, widget_2_2_2_1))

class AttendancePrefectEntryWidget(BaseAttendanceEntryWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Prefect", data)
        
        self.labeled_container.setProperty("class", "AttendancePrefectEntryWidget")
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.min < 10 else "") + str(self.data.period.time.min))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.sec < 10 else "") + str(self.data.period.time.sec))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = _CharacterNameWidget(self.staff.name)
        layout_2.addWidget(name_widget)
        
        widget_2_2, layout_2_2 = create_widget(None, QHBoxLayout)
        
        layout_2_2.addWidget(LabeledField("Class", QLabel(self.staff.cls.name), height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_3_1, layout_1_3_1 = create_scrollable_widget(None, QVBoxLayout)
        
        for index, duty in enumerate(self.staff.duties.get(self.data.period.day, [])):
            layout_1_3_1.addWidget(QLabel(f"{index + 1}. {duty}"))
        
        layout_2_2.addWidget(LabeledField("Duties", widget_1_3_1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        layout_2.addWidget(widget_2_2)



class StaffListPrefectEntryWidget(BaseStaffListEntryWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, prefect: Prefect, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, prefect, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListPrefectEntryWidget")
        
        self.sub_info_layout.addWidget(LabeledField("Post", QLabel(self.staff.post_name)))
        self.sub_info_layout.addWidget(LabeledField("Class", QLabel(self.staff.cls.name)))

class StaffListTeacherEntryWidget(BaseStaffListEntryWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, teacher: Teacher, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, teacher, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListTeacherEntryWidget")
        
        self.sub_info_layout.addWidget(LabeledField("Dept", QLabel(self.staff.department.name), QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))


