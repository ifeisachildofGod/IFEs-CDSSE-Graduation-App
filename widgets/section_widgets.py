
from widgets.section_sub_widgets import *

class BaseListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        scroll_widget = QScrollArea()
        scroll_widget.setWidgetResizable(True)
        
        widget = QWidget()
        scroll_widget.setWidget(widget)
        self.main_layout = QVBoxLayout(widget)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        layout.addWidget(scroll_widget)


class AttendanceWidget(BaseListWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, parent_widget: TabViewWidget, data: AppData, attendance_tab_name: str, punctuality_tab_name: str, comm_system: BaseCommSystem, saved_state_changed: pyBoundSignal):
        super().__init__()
        
        self.data = data
        self.parent_widget = parent_widget
        self.saved_state_changed = saved_state_changed
        
        self.attendance_graph_widget = self.parent_widget.get(attendance_tab_name)
        self.punctuality_graph_widget = self.parent_widget.get(punctuality_tab_name)
        
        self.attendance_dict = {}
        
        _, cit_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cit_teacher_widget, cit_teacher_layout = create_widget(None, QHBoxLayout)
        cit_teacher_layout.addWidget(QLabel(f'Teacher Time'))
        
        t_time_label = QLabel(f'{("0" if self.data.teacher_cit.hour < 10 else "") + str(self.data.teacher_cit.hour)}:{("0" if self.data.teacher_cit.min < 10 else "") + str(self.data.teacher_cit.min)}')
        t_time_label.setProperty("class", "labeled-widget")
        
        cit_teacher_layout.addWidget(t_time_label)
        cit_layout.addWidget(cit_teacher_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        
        cit_prefect_widget, cit_prefect_layout = create_widget(None, QHBoxLayout)        
        t_time_label = QLabel(f'{("0" if self.data.prefect_cit.hour < 10 else "") + str(self.data.prefect_cit.hour)}:{("0" if self.data.prefect_cit.min < 10 else "") + str(self.data.prefect_cit.min)}')
        t_time_label.setProperty("class", "labeled-widget")
        
        cit_prefect_layout.addWidget(t_time_label)
        cit_prefect_layout.addWidget(QLabel(f'Prefect Time'))
        cit_layout.addWidget(cit_prefect_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        _, self.attendance_layout = create_widget(self.main_layout, QVBoxLayout)
        
        for attendance in self.data.attendance_data:
            self.add_attendance_log(attendance)
        
        self.main_layout.addStretch()
        
        self.comm_signal.connect(self.add_new_attendance_log)
        comm_system.set_data_point("IUD", self.comm_signal)
    
    def add_attendance_log(self, attendance_entry: AttendanceEntry):
        if isinstance(attendance_entry.staff, Teacher):
            widget = AttendanceTeacherWidget(attendance_entry)
            self.attendance_graph_widget.teacher_data_changed()
            self.punctuality_graph_widget.teacher_data_changed()
        elif isinstance(attendance_entry.staff, Prefect):
            widget = AttendancePrefectWidget(attendance_entry)
            self.attendance_graph_widget.prefect_data_changed()
            self.punctuality_graph_widget.prefect_data_changed()
        else:
            raise TypeError(f"Type: {type(attendance_entry.staff)} is not supported")
        
        self.saved_state_changed.emit(False)
        
        self.attendance_layout.addWidget(widget)
    
    def add_new_attendance_log(self, IUD: str):
        staff = next((prefect for _, prefect in self.data.prefects.items() if prefect.IUD == IUD), None)
        if staff is None:
            staff = next((teacher for _, teacher in self.data.teachers.items() if teacher.IUD == IUD), None)
        
        if staff is not None:
            day, month, date, t, year = time.ctime().split()
            hour, min, sec = t.split(":")
            
            day = next((dotw for dotw in DAYS_OF_THE_WEEK if day in dotw))
            month = next((moty for moty in MONTHS_OF_THE_YEAR if month in moty))
            
            entry = AttendanceEntry(Time(int(hour), int(min), int(sec)), day, int(date), month, int(year), staff)
            
            self.add_attendance_log(entry)
            
            staff.attendance.append(entry)
            self.data.attendance_data.append(entry)


class PrefectStaffListWidget(BaseListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, tab_name: str, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__()
        
        for _, prefect in data.prefects.items():
            self.main_layout.addWidget(StaffListPrefectWidget(parent_widget, data, prefect, tab_name, comm_system, card_scanner_index, staff_data_index))
        
        self.main_layout.addStretch()

class TeacherStaffListWidget(BaseListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, tab_name: str, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__()
        
        for _, teacher in data.teachers.items():
            self.main_layout.addWidget(StaffListTeacherWidget(parent_widget, data, teacher, tab_name, comm_system, card_scanner_index, staff_data_index))
        
        self.main_layout.addStretch()


class AttendanceBarWidget(BaseListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        # teacher_data: dict[str, tuple[str, tuple[list[str], list[int]]]] = {}
        
        # prefect_names = []
        # prefects_attendance_data = []
        
        # prefect_interval = get_attendance_time_interval(*data.prefect_timeline_dates)
        # teacher_interval = get_attendance_time_interval(*data.teacher_timeline_dates)
        
        self.prefect_data_changed()
        self.teacher_data_changed()
        # for staff_attendance_data in data.attendance_data:
        #     if isinstance(staff_attendance_data.staff, Prefect):
        #         percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, list(staff_attendance_data.staff.duties.keys()), prefect_interval)
                
        #         prefect_names.append(staff_attendance_data.staff.name)
        #         prefects_attendance_data.append(percentage_attendance)
        #     elif isinstance(staff_attendance_data.staff, Teacher):
        #         days_tba = list(set(flatten([[day for day, _ in s.periods] for s in staff_attendance_data.staff.subjects])))
                
        #         percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, days_tba, teacher_interval)
                
        #         if staff_attendance_data.staff.department.id in teacher_data:
        #             teacher_data[staff_attendance_data.staff.department.id][1][0].append(staff_attendance_data.staff.name)
        #             teacher_data[staff_attendance_data.staff.department.id][1][1].append(percentage_attendance)
        #         else:
        #             teacher_data[staff_attendance_data.staff.department.id] = (staff_attendance_data.staff.department.name, [(staff_attendance_data.staff.name), percentage_attendance])
        
        # if prefects_attendance_data:
        #     prefect_info_widget = BarWidget("Cummulative Prefect Attendance", "Prefect Names", "Yearly Attendance (%)")
        #     prefect_info_widget.add_data("Prefects", THEME_MANAGER.get_current_palette()["prefect"], (prefect_names, prefects_attendance_data))
            
        #     self.prefect_attendance_widget = LabeledField("Prefect Attendance", prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            
        #     self.main_layout.addWidget(self.prefect_attendance_widget)
        # else:
        #     label = QLabel("No Prefect Attendance Data")
        #     label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        #     self.prefect_attendance_widget = LabeledField("Prefect Attendance", label, height_size_policy=QSizePolicy.Policy.Maximum)
            
        #     self.main_layout.addWidget(self.prefect_attendance_widget)
        
        # if teacher_data:
        #     dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        #     # dtd_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            
        #     for index, (_, (name, data)) in enumerate(teacher_data.items()):
        #         widget = BarWidget(f"Cummulative {name} Attendance", f"{name} Department Teachers", "Yearly Attendance (%)")
        #         widget.add_data(name, list(get_named_colors_mapping().values())[index], data)
                
        #         dtd_layout.addWidget(widget)
            
        #     self.teacher_attendance_widget = LabeledField("Departmental Attendance", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        #     self.main_layout.addWidget(self.teacher_attendance_widget)
        # else:
            # label = QLabel("No Teacher Attendance Data")
            # label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # self.teacher_attendance_widget = LabeledField("Teacher Attendance", label, height_size_policy=QSizePolicy.Policy.Maximum)
            # self.main_layout.addWidget(self.teacher_attendance_widget, alignment=Qt.AlignmentFlag.AlignTop)
    
    def prefect_data_changed(self):
        if hasattr(self, "prefect_attendance_widget"):
            self.main_layout.removeWidget(self.prefect_attendance_widget)
            self.prefect_attendance_widget.deleteLater()
        
        prefect_names = []
        prefects_attendance_data = []
        
        prefect_interval = get_attendance_time_interval(*self.data.prefect_timeline_dates)
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Prefect):
                percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, list(staff_attendance_data.staff.duties.keys()), prefect_interval)
                
                prefect_names.append(staff_attendance_data.staff.name)
                prefects_attendance_data.append(percentage_attendance)
        
        if prefects_attendance_data:
            prefect_info_widget = BarWidget("Cummulative Prefect Attendance", "Prefect Names", "Yearly Attendance (%)")
            prefect_info_widget.add_data("Prefects", THEME_MANAGER.get_current_palette()["prefect"], (prefect_names, prefects_attendance_data))
            
            self.prefect_attendance_widget = LabeledField("Prefect Attendance", prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        else:
            label = QLabel("No Prefect Attendance Data")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.prefect_attendance_widget = LabeledField("Prefect Attendance", label, height_size_policy=QSizePolicy.Policy.Maximum)
            
        self.main_layout.addWidget(self.prefect_attendance_widget)
    
    def teacher_data_changed(self):
        if hasattr(self, "teacher_attendance_widget"):
            self.main_layout.removeWidget(self.teacher_attendance_widget)
            self.teacher_attendance_widget.deleteLater()
        
        teacher_data: dict[str, tuple[str, tuple[list[str], list[int]]]] = {}
        
        teacher_interval = get_attendance_time_interval(*self.data.teacher_timeline_dates)
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Teacher):
                days_tba = list(set(flatten([[day for day, _ in s.periods] for s in staff_attendance_data.staff.subjects])))
                
                percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, days_tba, teacher_interval)
                
                if staff_attendance_data.staff.department.id in teacher_data:
                    teacher_data[staff_attendance_data.staff.department.id][1][0].append(staff_attendance_data.staff.name)
                    teacher_data[staff_attendance_data.staff.department.id][1][1].append(percentage_attendance)
                else:
                    teacher_data[staff_attendance_data.staff.department.id] = (staff_attendance_data.staff.department.name, [(staff_attendance_data.staff.name), percentage_attendance])
        
        if teacher_data:
            dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
            # dtd_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            
            for index, (_, (name, data)) in enumerate(teacher_data.items()):
                widget = BarWidget(f"Cummulative {name} Attendance", f"{name} Department Teachers", "Yearly Attendance (%)")
                widget.add_data(name, list(get_named_colors_mapping().values())[index], data)
                
                dtd_layout.addWidget(widget)
            
            self.teacher_attendance_widget = LabeledField("Departmental Attendance", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.main_layout.addWidget(self.teacher_attendance_widget)
        else:
            label = QLabel("No Teacher Attendance Data")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.teacher_attendance_widget = LabeledField("Teacher Attendance", label, height_size_policy=QSizePolicy.Policy.Maximum)
            self.main_layout.addWidget(self.teacher_attendance_widget, alignment=Qt.AlignmentFlag.AlignTop)
    
    def get_percentage_attendance(self, attendance: list[AttendanceEntry], valid_attendance_days: list[str], interval: tuple[int, int]):
        remainder_days = sum([day in valid_attendance_days for day in DAYS_OF_THE_WEEK[:interval[1] + 1]])
        max_attendance = (len(valid_attendance_days) * interval[0]) + remainder_days
        
        percentage_attendance = len(attendance) * 100 / max(max_attendance, 1)
        
        return percentage_attendance

class PunctualityGraphWidget(BaseListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        self.prefect_data_changed()
        self.teacher_data_changed()
        
        # teacher_data = {}
        # prefects_data = {}
        
        # for staff_attendance_data in self.data.attendance_data:
        #     if isinstance(staff_attendance_data.staff, Prefect):
        #         prefects_data[staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        #     elif isinstance(staff_attendance_data.staff, Teacher):
        #         teacher_data[staff_attendance_data.staff.department.id][1][staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        
        # sub_data = {
        #     "prefect_id 1": ("Emma", [0, 0, 0, 1, 1, 2, 2, -1, -1, -3, 0, -2, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3]),
        #     "prefect_id 2": ("Bambi", [0, 0, 0, -2, 1, 2, 2, 0, -1, -3, 0, -2, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3]),
        #     "prefect_id 3": ("Mikalele", [0, 0, -1, 0, 1, 1, 2, 0, -1, -3, 0, -2, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3]),
        #     "prefect_id 4": ("Jesse", [0, 0, 0, 1, 1, 2, 3, 0, -1, -3, 0, -2, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3]),
        #     "prefect_id 5": ("Tumbum", [0, 0, 0, 3, 1, 2, 0, 0, -1, -3, 0, -2, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3]),
        # }
        
        # if prefects_data:
        #     prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
            
        #     for index, (_, (name, prefect_data)) in enumerate(prefects_data.items()):
        #         prefect_info_widget.plot([i + 1 for i in range(len(prefect_data))], prefect_data, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
            
        #     self.prefect_punctuality_widget = LabeledField("Prefect Punctuality", prefect_info_widget)
        # else:
        #     label = QLabel("No Prefect Punctuality Data")
        #     label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        #     self.prefect_punctuality_widget = LabeledField("Prefect Punctuality", label, height_size_policy=QSizePolicy.Policy.Maximum)
            
        # self.main_layout.addWidget(self.prefect_punctuality_widget)
        
        # if teacher_data:
        #     dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
            
        #     for _, (dep_name, dep_data) in teacher_data.items():
        #         dep_info_widget = GraphWidget(f"{dep_name} Department Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                
        #         for index, (_, (name, info)) in enumerate(dep_data.items()):
        #             dep_info_widget.plot([i + 1 for i in range(len(info))], info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
                
        #         dtd_layout.addWidget(dep_info_widget)
            
        #     self.teacher_punctuality_widget = LabeledField("Departmental Punctuality", dtd_widget if teacher_data else QLabel("No Teacher Punctuality Data"), QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        # else:
        #     label = QLabel("No Teacher Punctuality Data")
        #     label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        #     self.teacher_punctuality_widget = LabeledField("Departmental Punctuality", label, height_size_policy=QSizePolicy.Policy.Maximum), alignment=Qt.AlignmentFlag.AlignTop
        
        # self.main_layout.addWidget(self.teacher_punctuality_widget)
    
    def prefect_data_changed(self):
        if hasattr(self, "prefect_punctuality_widget"):
            self.main_layout.removeWidget(self.prefect_punctuality_widget)
            self.prefect_punctuality_widget.deleteLater()
        
        prefects_data = {}
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Prefect):
                prefects_data[staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        
        if prefects_data:
            prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
            
            for index, (_, (name, prefect_data)) in enumerate(prefects_data.items()):
                prefect_info_widget.plot([i + 1 for i in range(len(prefect_data))], prefect_data, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
            
            self.prefect_punctuality_widget = LabeledField("Prefect Punctuality", prefect_info_widget)
        else:
            label = QLabel("No Prefect Punctuality Data")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.prefect_punctuality_widget = LabeledField("Prefect Punctuality", label, height_size_policy=QSizePolicy.Policy.Maximum)
            
        self.main_layout.insertWidget(0, self.prefect_punctuality_widget)
    
    def teacher_data_changed(self):
        if hasattr(self, "teacher_punctuality_widget"):
            self.main_layout.removeWidget(self.teacher_punctuality_widget)
            self.teacher_punctuality_widget.deleteLater()
        
        teacher_data = {}
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Teacher):
                teacher_data[staff_attendance_data.staff.department.id][1][staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        
        if teacher_data:
            dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
            
            for _, (dep_name, dep_data) in teacher_data.items():
                dep_info_widget = GraphWidget(f"{dep_name} Department Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                
                for index, (_, (name, info)) in enumerate(dep_data.items()):
                    dep_info_widget.plot([i + 1 for i in range(len(info))], info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
                
                dtd_layout.addWidget(dep_info_widget)
            
            self.teacher_punctuality_widget = LabeledField("Departmental Punctuality", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        else:
            label = QLabel("No Teacher Punctuality Data")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.teacher_punctuality_widget = LabeledField("Departmental Punctuality", label, height_size_policy=QSizePolicy.Policy.Maximum)
            
        self.main_layout.addWidget(self.teacher_punctuality_widget)
    
    def get_punctuality_data(self, staff: Staff):
        prefects_plot_data: list[float] = []
        
        weeks: list[list[Time]] = []
        
        prev_day = DAYS_OF_THE_WEEK[0]
        prev_dt = 1
        
        for attendance in staff.attendance:
            if ((DAYS_OF_THE_WEEK.index(attendance.day) > DAYS_OF_THE_WEEK.index(prev_day)) or
                (prev_dt != attendance.date and
                 DAYS_OF_THE_WEEK.index(attendance.day) == DAYS_OF_THE_WEEK.index(prev_day))
                ):
                weeks.append([attendance.time])
            else:
                weeks[-1].append(attendance.time)
            
            prev_day = attendance.day
            prev_dt = attendance.date
        
        for week_time in weeks:
            weekly_punctuality = sum([(self.data.prefect_cit.hour - t.hour) * 60 + (self.data.prefect_cit.min - t.min) * 60 + (self.data.prefect_cit.sec - t.sec) / 60 for t in week_time])
            prefects_plot_data.append(weekly_punctuality)
        
        return staff.name, prefects_plot_data



class _SensorMetaInfoWidget(QWidget):
    def __init__(self, data: SensorMeta):
        super().__init__()
        self.data = data
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        widget_2_1 = QWidget()
        layout_2_1 = QVBoxLayout()
        widget_2_1.setLayout(layout_2_1)
        
        widget_2_1_1 = QWidget()
        layout_2_1_1 = QHBoxLayout()
        widget_2_1_1.setLayout(layout_2_1_1)
        layout_2_1.addWidget(widget_2_1_1)
        
        name_1 = LabeledField("Sensor Name", QLabel(f"{self.data.sensor_type} sensor"))
        name_2 = LabeledField("Model", QLabel(self.data.model))
        name_3 = LabeledField("Version", QLabel(self.data.version))
        
        layout_2_1_1.addWidget(name_1)
        layout_2_1_1.addWidget(name_2)
        layout_2_1_1.addWidget(name_3)
        
        widget_2_1_2 = QWidget()
        layout_2_1_2 = QHBoxLayout()
        widget_2_1_2.setLayout(layout_2_1_2)
        layout_2_1.addWidget(widget_2_1_2)
        
        name_4 = LabeledField("Manufacturer", QLabel(self.data.developer))
        # name_5 = LabeledField("Abbreviation", QLabel(self.data.abrev))
        
        layout_2_1_2.addWidget(name_4, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(LabeledField("Meta Info", widget_2_1, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum))

class SensorWidget(QWidget):
    comm_signal = pySignal(int)
    
    def __init__(self, main_window, data: AppData, sensor: Sensor, saved_state_changed: pyBoundSignal):
        super().__init__()
        
        self.main_window = main_window
        self.data = data
        self.sensor = sensor
        self.saved_state_changed = saved_state_changed
        
        self.data_key = self.sensor.meta_data.sensor_type + self.sensor.meta_data.version + self.sensor.meta_data.model
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        self.labeled_container = LabeledField(self.sensor.meta_data.sensor_type, self.container)
        
        layout.addWidget(self.labeled_container)
        
        widget_1, layout_1_1 = create_widget(None, QHBoxLayout)
        
        image = Image(self.sensor.img_path, parent=self.container, width=150)
        layout_1_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        widget_2, layout_2 = create_widget(None, QVBoxLayout)
        
        self.reading_slider = QSlider(Qt.Orientation.Horizontal)
        
        self.comm_signal.connect(self.reading_slider_data)
        self.sensor.comm_system.set_data_point(self.sensor.meta_data.sensor_type, self.comm_signal)
        
        self.reading_slider.setDisabled(True)
        self.reading_slider.setValue(10)
        
        meta_info_widget = _SensorMetaInfoWidget(self.sensor.meta_data)
        layout_1_2_1.addWidget(meta_info_widget)
        
        self.safety_reading_slider = QSlider(Qt.Orientation.Horizontal)
        self.safety_reading_slider.setValue(self.data.variables.get(self.data_key, 50))
        self.safety_reading_slider.valueChanged.connect(self.safety_slider_moved)
        
        layout_2.addWidget(LabeledField("Reading", self.reading_slider))
        layout_2.addWidget(LabeledField("Safety Value", self.safety_reading_slider))
        
        layout_1_1.addWidget(widget_1_2_1)
        
        self.main_layout.addWidget(widget_1)
        self.main_layout.addWidget(widget_2)
        
        self.sensor.comm_system.connection_changed_signal.connect(self.connection_changed)
    
    def safety_slider_moved(self, value: int):
        self.data.variables[self.data_key] = value
        self.sensor.comm_system.send_message(f"{self.sensor.meta_data.sensor_type}:{value}")
        self.saved_state_changed.emit(False)
    
    def reading_slider_data(self, value: int):
        self.reading_slider.setValue(value)
    
    def connection_changed(self, state: bool):
        not_connected = not state
        self.container.setDisabled(not_connected)
        if not_connected:
            self.container.setToolTip(f"{self.sensor.meta_data.sensor_type} sensor disabled as there is no connection")
        else:
            self.container.setToolTip("")
            self.sensor.comm_system.send_message(f"{self.sensor.meta_data.sensor_type}:{self.safety_reading_slider.value()}")

class UltrasonicSonarWidget(QWidget):
    comm_signal = pySignal(list)
    
    def __init__(self, main_window, data: AppData, sensor: Sensor, saved_state_changed: pyBoundSignal):
        super().__init__()
        
        self.main_window = main_window
        self.data = data
        self.sonar = sensor
        self.saved_state_changed = saved_state_changed
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        
        self.main_layout = QHBoxLayout()
        self.container.setLayout(self.main_layout)
        
        self.labeled_field = LabeledField(self.sonar.meta_data.sensor_type, self.container)
        
        self.activate_cb = QCheckBox("Activate Sonar")
        self.activate_cb.clicked.connect(self.toogle_activation_state)
        
        layout.addWidget(self.activate_cb, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.labeled_field)
        
        ultrasonic_sensor_meta_info_widget, ultrasonic_sensor_meta_info_layout = create_widget(self.main_layout, QVBoxLayout)
        
        ultrasonic_sensor_meta_info_layout.addWidget(Image(self.sonar.img_path, ultrasonic_sensor_meta_info_widget, width=130), alignment=Qt.AlignmentFlag.AlignCenter)
        ultrasonic_sensor_meta_info_layout.addWidget(_SensorMetaInfoWidget(SensorMeta("Ultrasonic", "Super", "0.0.0.10", "Arduino LC")), alignment=Qt.AlignmentFlag.AlignCenter)
        
        _, sonar_layout = create_widget(self.main_layout, QVBoxLayout)
        
        self.sonar_widget = SonarWidget()
        
        self.safety_slider = QSlider(Qt.Orientation.Horizontal)
        self.safety_slider.valueChanged.connect(self.safety_slider_moved)
        self.safety_slider.setValue(self.data.sonar_safety_value)
        
        self.comm_signal.connect(lambda args: self.sonar_widget.update_sonar([178, 179, 180, 181, 182], args[1]))
        self.sonar.comm_system.set_data_point("distances", self.comm_signal)
        
        sonar_layout.addWidget(self.sonar_widget)
        sonar_layout.addWidget(LabeledField("Safety Distance", self.safety_slider, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        
        self.activate_cb.click()
        self.activate_cb.click()
        
        self.sonar.comm_system.connection_changed_signal.connect(self.connection_changed)
        self.activate_cb.setDisabled(not self.sonar.comm_system.connected)
        
        if not self.sonar.comm_system.connected:
            self.activate_cb.setToolTip("Disabled as there is no connection device")
    
    def connection_changed(self, state: bool):
        not_connected = not state
        
        self.activate_cb.setDisabled(not_connected)
        
        if not_connected:
            self.activate_cb.setToolTip("Disabled as there is no connection device")
        else:
            self.activate_cb.setToolTip("")
            self.toogle_activation_state(self.activate_cb.isChecked())
            self.sonar.comm_system.send_message(f"Ultrasonic:{self.safety_slider.value()}")
                
    
    def safety_slider_moved(self, value: int):
        self.sonar.comm_system.send_message(f"Ultrasonic:{value}")
        self.sonar_widget.update_sonar_limit(value)
        
        self.data.sonar_safety_value = value
        
        self.saved_state_changed.emit(False)
    
    def toogle_activation_state(self, state):
        self.labeled_field.setDisabled(not state)
        if self.sonar.comm_system.connected:
            self.sonar.comm_system.send_message("SECURITY-ACTIVE" if state else "NOT-SECURITY-ACTIVE")




