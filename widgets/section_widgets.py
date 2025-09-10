
from widgets.section_sub_widgets import *

class BaseListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        widget = QWidget()
        self.scroll_widget.setWidget(widget)
        self.main_layout = QVBoxLayout(widget)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        layout.addWidget(self.scroll_widget)


class AttendanceWidget(BaseListWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, parent_widget: TabViewWidget, data: AppData, attendance_chart_widget: "AttendanceBarWidget", punctuality_graph_widget: "PunctualityGraphWidget", comm_system: BaseCommSystem, saved_state_changed: pyBoundSignal):
        super().__init__()
        
        self.data = data
        self.comm_system = comm_system
        self.parent_widget = parent_widget
        self.saved_state_changed = saved_state_changed
        
        self.attendance_chart_widget = attendance_chart_widget
        self.punctuality_graph_widget = punctuality_graph_widget
        
        self.attendance_dict = {}
        
        self.create_time_labels()
        
        _, self.attendance_layout = create_widget(self.main_layout, QVBoxLayout)
        
        for attendance in self.data.attendance_data:
            self._add_attendance_log(attendance)
        
        self.main_layout.addStretch()
        
        self.comm_signal.connect(self.add_new_attendance_log)
        self.comm_system.set_data_point("IUD", self.comm_signal)
    
    def create_time_labels(self):
        _, time_layout = create_widget(self.main_layout, QHBoxLayout)
        
        
        teacher_widget, teacher_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cit_teacher_widget, cit_teacher_layout = create_widget(None, QHBoxLayout)
        cot_teacher_widget, cot_teacher_layout = create_widget(None, QHBoxLayout)
        
        it_time_label = QLabel(f'{("0" if self.data.teacher_cit.hour < 10 else "") + str(self.data.teacher_cit.hour)}:{("0" if self.data.teacher_cit.min < 10 else "") + str(self.data.teacher_cit.min)}')
        it_time_label.setProperty("class", "labeled-widget")
        
        ot_time_label = QLabel(f'{("0" if self.data.teacher_cot.hour < 10 else "") + str(self.data.teacher_cot.hour)}:{("0" if self.data.teacher_cot.min < 10 else "") + str(self.data.teacher_cot.min)}')
        ot_time_label.setProperty("class", "labeled-widget")
        
        cit_teacher_layout.addWidget(QLabel(f'Teacher CIT'))
        cit_teacher_layout.addWidget(it_time_label)
        
        cot_teacher_layout.addWidget(QLabel(f'Teacher COT'))
        cot_teacher_layout.addWidget(ot_time_label)
        
        teacher_layout.addWidget(cit_teacher_widget)
        teacher_layout.addWidget(cot_teacher_widget)
        
        
        
        prefect_widget, prefect_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cit_prefect_widget, cit_prefect_layout = create_widget(None, QHBoxLayout)
        cot_prefect_widget, cot_prefect_layout = create_widget(None, QHBoxLayout)        
             
        it_time_label = QLabel(f'{("0" if self.data.prefect_cit.hour < 10 else "") + str(self.data.prefect_cit.hour)}:{("0" if self.data.prefect_cit.min < 10 else "") + str(self.data.prefect_cit.min)}')
        it_time_label.setProperty("class", "labeled-widget")
        
        ot_time_label = QLabel(f'{("0" if self.data.prefect_cot.hour < 10 else "") + str(self.data.prefect_cot.hour)}:{("0" if self.data.prefect_cot.min < 10 else "") + str(self.data.prefect_cot.min)}')
        ot_time_label.setProperty("class", "labeled-widget")
        
        cit_prefect_layout.addWidget(it_time_label)
        cit_prefect_layout.addWidget(QLabel(f'Prefect CIT'))
        
        cot_prefect_layout.addWidget(ot_time_label)
        cot_prefect_layout.addWidget(QLabel(f'Prefect COT'))
        
        prefect_layout.addWidget(cit_prefect_widget)
        prefect_layout.addWidget(cot_prefect_widget)
        
        
        time_layout.addWidget(teacher_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        time_layout.addWidget(prefect_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
    
    def _add_attendance_log(self, attendance_entry: AttendanceEntry):
        if isinstance(attendance_entry.staff, Teacher):
            widget = AttendanceTeacherWidget(attendance_entry)
            self.attendance_chart_widget.teacher_data_changed()
            self.punctuality_graph_widget.teacher_data_changed()
        elif isinstance(attendance_entry.staff, Prefect):
            widget = AttendancePrefectWidget(attendance_entry)
            self.attendance_chart_widget.prefect_data_changed()
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
            
            t_ = Time(int(hour), int(min), int(sec))
            
            another_present = next((True for entry in staff.attendance if entry.date == int(date) and entry.month == month and entry.year == int(year)), False)
            ct_data = (self.data.prefect_cit, self.data.prefect_cot) if isinstance(staff, Prefect) else (self.data.teacher_cit, self.data.teacher_cot)
            
            is_ci = is_check_in(t_, ct_data[0], ct_data[1])
            
            if another_present and is_ci:
                return
            
            entry = AttendanceEntry(t_, day, int(date), month, int(year), is_ci, staff)
            
            self.comm_system.send_message(f"setId:{staff.name.abrev},{is_ci},{hour}'{min}")
            
            self.data.attendance_data.append(entry)
            staff.attendance.append(entry)
            
            self._add_attendance_log(entry)
        else:
            self.comm_system.send_message("state:8")
            QMessageBox.warning(self.parent_widget, "CardScannerError", f"No staff is linked to this card (IUD: {IUD})")
    
    def keyPressEvent(self, a0):
        if a0.text() == "6":
            self.add_new_attendance_log("6999BDB2")
        elif a0.text() == "b":
            self.add_new_attendance_log("B3A6DE0C")
        elif a0.text() == "8":
            self.add_new_attendance_log("89A2A1B4")
        elif a0.text() == "6":
            self.add_new_attendance_log("637B910C")
        elif a0.text() == "a":
            self.add_new_attendance_log("A3DEB30C")
        elif a0.text() == "f":
            self.add_new_attendance_log("F93E13B4")
        return super().keyPressEvent(a0)


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
        
        self.prefect_data_changed()
        self.teacher_data_changed()
    
    def prefect_data_changed(self):
        if hasattr(self, "prefect_attendance_widget"):
            self.main_layout.removeWidget(self.prefect_attendance_widget)
            self.prefect_attendance_widget.deleteLater()
        
        prefect_names = []
        prefects_attendance_data = []
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Prefect):
                latest_attendance = next(p for p in reversed(self.data.attendance_data) if p.staff == staff_attendance_data.staff)
                prefect_interval = get_attendance_time_interval(self.data.prefect_timeline_dates[0], latest_attendance)
                
                percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, list(staff_attendance_data.staff.duties.keys()), prefect_interval)
                
                prefect_names.append(staff_attendance_data.staff.name.abrev)
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
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Teacher):
                latest_attendance = next(t for t in reversed(self.data.attendance_data) if t.staff == staff_attendance_data.staff)
                teacher_interval = get_attendance_time_interval(self.data.teacher_timeline_dates[0], latest_attendance)
                
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
        remainder_days_amt = sum([day in valid_attendance_days for day in DAYS_OF_THE_WEEK[:interval[1] + 1]])
        max_attendance = (len(valid_attendance_days) * interval[0]) + remainder_days_amt
        
        percentage_attendance = sum(1 for entry in attendance if entry.day in valid_attendance_days) * 100 / (max_attendance if max_attendance else 1)
        
        return percentage_attendance

class PunctualityGraphWidget(BaseListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        self.prefect_data_changed()
        self.teacher_data_changed()
    
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
        
        # weeks: list[list[Time]] = []
        
        # prev_day = DAYS_OF_THE_WEEK[0]
        # prev_dt = 1
        
        # for attendance in staff.attendance:
        #     if attendance.is_check_in:
        #         if ((DAYS_OF_THE_WEEK.index(attendance.day) > DAYS_OF_THE_WEEK.index(prev_day)) or
        #             (prev_dt != attendance.date and
        #             DAYS_OF_THE_WEEK.index(attendance.day) == DAYS_OF_THE_WEEK.index(prev_day))
        #             ):
        #             weeks.append([attendance.time])
        #         else:
        #             weeks[-1].append(attendance.time)
                
        #         prev_day = attendance.day
        #         prev_dt = attendance.date
        
        # for week_time in weeks:
        #     all_puncuality_in_week = [(self.data.prefect_cit.hour - t.hour) * 60 + (self.data.prefect_cit.min - t.min) + (self.data.prefect_cit.sec - t.sec) * (1/60) for t in week_time]
        #     weekly_punctuality = (sum(all_puncuality_in_week) if len(all_puncuality_in_week) else 0) / (len(all_puncuality_in_week) if len(all_puncuality_in_week) else 1)
        #     prefects_plot_data.append(weekly_punctuality)
        
        for attendance in staff.attendance:
            if attendance.is_check_in:
                prefects_plot_data.append((self.data.prefect_cit.hour - attendance.time.hour) * 60 + (self.data.prefect_cit.min - attendance.time.min) + (self.data.prefect_cit.sec - attendance.time.sec) * (1/60))
        
        return staff.name.abrev, prefects_plot_data



class _SensorWidget(QWidget):
    comm_signal = pySignal(int)
    
    def __init__(self, data: AppData, sensor: Sensor, saved_state_changed: pyBoundSignal, minimum:int=None, maximum:int=None, gradient_start_color=None, gradient_middle_color=None, gradient_end_color=None):
        super().__init__()
        self.data = data
        self.sensor = sensor
        self.saved_state_changed = saved_state_changed
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        self.reading_dial = ThreshDial(self.container, minimum, maximum, gradient_start_color=gradient_start_color, gradient_middle_color=gradient_middle_color, gradient_end_color=gradient_end_color)
        self.reading_dial.setFixedHeight(100)
        
        slider_widget, slider_layout = create_widget(None, QHBoxLayout)
        sub_slider_widget, sub_slider_layout = create_widget(None, QVBoxLayout)
        
        self.thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.thresh_slider.setValue(self.data.variables.get(self.sensor.name + " thresh", 0))
        self.thresh_slider.valueChanged.connect(self.thresh_slider_moved)
        
        self.thresh_value_label = QLabel(str(self.thresh_slider.value()))
        
        sub_slider_layout.addWidget(self.thresh_slider)
        sub_slider_layout.addWidget(self.thresh_value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        slider_layout.addWidget(QLabel(str(self.reading_dial.minimum())))
        slider_layout.addWidget(sub_slider_widget)
        slider_layout.addWidget(QLabel(str(self.reading_dial.maximum())))
        
        self.comm_signal.connect(self.reading_dial_updated)
        self.sensor.comm_system.set_data_point(self.sensor.name, self.comm_signal)
        self.main_layout.addWidget(self.reading_dial)
        self.main_layout.addWidget(slider_widget)
        
        layout.addWidget(LabeledField(self.sensor.name, self.container, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum))
    
    def reading_dial_updated(self, value: int):
        self.reading_dial.setValue(value)
    
    def thresh_slider_moved(self, value: int):
        self.data.variables[self.sensor.name] = value
        self.saved_state_changed.emit(False)
        
        new_thresh = value * self.reading_dial.maximum() / 100
        
        self.reading_dial.set_thresh_value(new_thresh)
        self.thresh_value_label.setText(str(new_thresh))
        
        self.reading_dial.update()
    
    def connection_changed(self, state: bool):
        not_connected = not state
        
        self.container.setDisabled(not_connected)
        if not_connected:
            self.container.setToolTip(f"No device connection")
        else:
            self.container.setToolTip("")
            self.sensor.comm_system.send_message(f"{self.sensor.name}:{self.thresh_slider.value()}")
    

class SensorsWidget(QWidget):
    fire_state_comm_signal = pySignal(int)
    
    def __init__(self, data: AppData, comm_system: BaseCommSystem, saved_state_changed: pyBoundSignal):
        super().__init__()
        self.data = data
        self.comm_system = comm_system
        self.saved_state_changed = saved_state_changed
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container, self.main_layout = create_scrollable_widget(layout, QVBoxLayout)
        
        gas_widget, gas_layout = create_widget(None, QHBoxLayout)
        ultrasonic_widget, ultrasonic_layout = create_widget(None, QHBoxLayout)
        
        self.gas1_widget = _SensorWidget(self.data, Sensor("Gas 1", self.comm_system), self.saved_state_changed, 0, 420)
        self.gas2_widget = _SensorWidget(self.data,Sensor("Gas 2", self.comm_system), self.saved_state_changed, 0, 420)
        
        self.gas1_widget.thresh_slider.valueChanged.connect(self.gas_thresh_changed)
        self.gas2_widget.thresh_slider.valueChanged.connect(self.gas_thresh_changed)
        
        gas_layout.addWidget(self.gas1_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        gas_layout.addWidget(self.gas2_widget, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.gas_labeled_field = LabeledField("Gas sensors", gas_widget)
        
        self.ultrasonic_cb = QCheckBox("Security activated")
        self.ultrasonic_cb.clicked.connect(self.toogle_security)
        
        self.ultrasonic1_widget = _SensorWidget(self.data, Sensor("East", self.comm_system), self.saved_state_changed, 0, 300, gradient_start_color="red", gradient_middle_color="yellow", gradient_end_color="green")
        self.ultrasonic2_widget = _SensorWidget(self.data, Sensor("South", self.comm_system), self.saved_state_changed, 0, 300, gradient_start_color="red", gradient_middle_color="yellow", gradient_end_color="green")
        self.ultrasonic3_widget = _SensorWidget(self.data, Sensor("West", self.comm_system), self.saved_state_changed, 0, 300, gradient_start_color="red", gradient_middle_color="yellow", gradient_end_color="green")
        
        self.ultrasonic1_widget.thresh_slider.valueChanged.connect(self.ultrasonic_thresh_changed)
        self.ultrasonic2_widget.thresh_slider.valueChanged.connect(self.ultrasonic_thresh_changed)
        self.ultrasonic3_widget.thresh_slider.valueChanged.connect(self.ultrasonic_thresh_changed)
        
        ultrasonic_layout.addWidget(self.ultrasonic1_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        ultrasonic_layout.addWidget(self.ultrasonic2_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        ultrasonic_layout.addWidget(self.ultrasonic3_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        self.ultasonic_labeled_field = LabeledField("Ultrasonic sensors", ultrasonic_widget)
        
        self.fire_text_widget = QLabel("FIRE!!! FIRE!!! FIRE!!!")
        self.fire_text_widget.setStyleSheet("font-size: 50px; color: red;")
        self.fire_text_widget.setVisible(False)
        
        self.fire_state_comm_signal.connect(self.fire_state_changed)
        self.comm_system.set_data_point("Flame", self.fire_state_comm_signal)
        
        self.main_layout.addWidget(self.gas_labeled_field)
        self.main_layout.addWidget(self.ultrasonic_cb, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.ultasonic_labeled_field)
        self.main_layout.addWidget(self.fire_text_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.ultrasonic_cb.click()
        self.ultrasonic_cb.click()
        
        self.comm_system.connection_changed_signal.connect(self.connection_changed)
    
    def gas_thresh_changed(self, _):
        self.comm_system.send_message(f"Gas:{self.gas1_widget.thresh_slider.value()},{self.gas2_widget.thresh_slider.value()}")
    
    def ultrasonic_thresh_changed(self, _):
        self.comm_system.send_message(f"Ultrasonic:{self.ultrasonic1_widget.thresh_slider.value()},{self.ultrasonic2_widget.thresh_slider.value()},{self.ultrasonic2_widget.thresh_slider.value()}")
    
    def toogle_security(self, on: bool):
        self.ultasonic_labeled_field.setDisabled(not on)
        if self.comm_system.connected:
            self.comm_system.send_message("SECURITY-ACTIVE" if on else "NOT-SECURITY-ACTIVE")
    
    def connection_changed(self, connected: bool):
        self.gas_labeled_field.setDisabled(not connected)
        self.ultrasonic_cb.setDisabled(not connected)
        self.ultasonic_labeled_field.setDisabled(not connected)
        
        if not connected:
            self.ultrasonic_cb.setToolTip("No device connection")
        else:
            self.ultrasonic_cb.setToolTip("")
            self.toogle_security(self.ultrasonic_cb.isChecked())
    
    def fire_state_changed(self, value: bool):
        self.fire_text_widget.setVisible(value)
    


