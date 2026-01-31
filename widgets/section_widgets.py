from itertools import combinations
from PyQt6.QtWidgets import QComboBox
from widgets.section_sub_widgets import *
from data.time_data_objects import *

class BaseListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        widget = QWidget()
        self.main_layout = QVBoxLayout()
        widget.setLayout(self.main_layout)
        
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
    
    # Category name is here to avoid edge cases
    def addWidget(self, widget: QWidget, category_name: str | None = None, stretch: int = ..., alignment: Qt.AlignmentFlag = ...):
        self.main_layout.addWidget(widget, stretch, alignment)

class BaseScrollListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        widget = QWidget()
        self.scroll_widget.setWidget(widget)
        self.main_layout = QVBoxLayout(widget)
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._layout.addWidget(self.scroll_widget)
    
    def addWidget(self, widget: QWidget, stretch: int = ..., alignment: Qt.AlignmentFlag = ...):
        self.main_layout.addWidget(widget, stretch, alignment)

class _FilterCategoriesWidget(BaseListWidget):
    def __init__(self):
        super().__init__()
        
        self.category_widgets = {}
    
    def addWidget(self, widget: "AttendanceWidget", category_name: str, stretch: int = ..., alignment: Qt.AlignmentFlag = ...):
        if category_name not in self.category_widgets:
            cat_widg = QWidget()
            cat_layout = QVBoxLayout()
            cat_widg.setLayout(cat_layout)
            
            self.category_widgets[category_name] = LabeledField(category_name, cat_widg)
            
            super().addWidget(self.category_widgets[category_name])
        
        self.category_widgets[category_name].addWidget(widget, stretch, alignment)

class AttendanceWidget(BaseScrollListWidget):
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
        
        self.filter_views = {}
        
        self.filter_data = [(["All", "Prefects", "Teachers"], 0), (["All", "Today", "This week", "This month", "This year"], 0)]
        
        filter_combinations = [comb for comb in list(combinations(range(len(sorted(self.filter_data)[-1][0])), len(self.filter_data))) if next((False for i, c in enumerate(comb) if c >= len(self.filter_data[i])), True)]
        
        for comb in filter_combinations:
            self.filter_views[comb] = self._determine_filter_widget_type(comb)
        
        for attendance in self.data.attendance_data:
            self._add_attendance_log(attendance)
        
        self.main_layout.addStretch()
        
        self.comm_signal.connect(self.add_new_attendance_log)
        self.comm_system.set_data_point("IUD", self.comm_signal)
            
        for i, widget in enumerate(self.filter_views.values()):
            widget.setVisible(i == 0)
        
        filter_widget, filter_layout = create_widget(None, QHBoxLayout)
        
        for index, (f_data, _) in enumerate(self.filter_data):
            filter = QComboBox()
            filter.addItems(f_data)
            filter.currentIndexChanged.connect(self._make_c_change_func(index))
            filter_layout.addWidget(filter, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._layout.insertWidget(0, filter_widget, alignment=Qt.AlignmentFlag.AlignRight)
    
    def _determine_category_name(self, comb: tuple, entry: AttendanceEntry):
        match comb[1]:
            case 0:
                return
            case 1:
                return
            case 2:
                return entry.period.day
            case 3:
                return f"{entry.period.day}, {positionify(entry.period.date)} {entry.period.month}"
            case 4:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                months_list = list(MONTHS_OF_THE_YEAR)
                
                if entry.period.date - day_index < 1:
                    start_month = months_list[months_list.index(entry.period.month) - 1]
                    start_date = MONTHS_OF_THE_YEAR[start_month] + (entry.period.date - day_index)
                else:
                    start_month = entry.period.month
                    start_date = entry.period.date - day_index
                
                if entry.period.date + (6 - day_index) > MONTHS_OF_THE_YEAR[entry.period.month]:
                    if months_list.index(entry.period.month) + 1 < len(months_list):
                        end_month = months_list[months_list.index(entry.period.month) + 1]
                        end_date = (entry.period.date + (6 - day_index)) % MONTHS_OF_THE_YEAR[entry.period.month]
                    else:
                        end_month = entry.period.month
                        end_date = MONTHS_OF_THE_YEAR[end_month]
                else:
                    end_month = entry.period.month
                    end_date = entry.period.date + (6 - day_index)
                
                return f"{positionify(start_date)} {start_month} - {positionify(end_date)} {end_month}, {entry.period.year}"
        
        raise Exception()
    
    def _determine_filter_widget_type(self, comb: tuple):
        return BaseListWidget() if comb[1] in (0, 1) else _FilterCategoriesWidget()
    
    def _make_c_change_func(self, index: int):
        def c_change(i):
            self.filter(*tuple((i if index == s_i else None) for s_i in range(len(self.filter_data))))
        
        return c_change
    
    def _assess_filter(a_obj: BaseAttendanceWidget, comb: tuple):
        i1, i2 = comb
        
        curr_day = Period.ctime_to_period(time.ctime())
        
        a_types = [(AttendancePrefectWidget, AttendanceTeacherWidget), AttendancePrefectWidget, AttendanceTeacherWidget]
        
        if isinstance(a_obj, a_types[i1]):
            if i2 == 0:
                return True
            elif i2 == 1:
                return a_obj.data.period.date == curr_day.date
            elif i2 == 2:
                obj_day_index = DAYS_OF_THE_WEEK.index(a_obj.data.period.day)
                cur_day_index = DAYS_OF_THE_WEEK.index(curr_day.day)
                
                return cur_day_index - obj_day_index == curr_day.date - a_obj.data.period.date
            elif i2 == 3:
                return curr_day.month == a_obj.data.period.month
            elif i2 == 4:
                return curr_day.year == a_obj.data.period.year
        
        return False
    
    def filter(self, *args):
        for i, index in enumerate(args):
            if index is not None:
                self.filter_data[i][1] = index
        
        for key, widget in self.filter_views.items():
            widget.setVisible(key == tuple(i for _, i in self.filter_data))
    
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
        
        for comb, m_widget in self.filter_views.items():
            if self._assess_filter(attendance_entry, comb):
                m_widget.addWidget(widget, self._determine_category_name(comb, widget.data))
    
    def add_new_attendance_log(self, IUD: str):
        staff = next((prefect for _, prefect in self.data.prefects.items() if prefect.IUD == IUD), None)
        if staff is None:
            staff = next((teacher for _, teacher in self.data.teachers.items() if teacher.IUD == IUD), None)
        
        if staff is not None:
            period = Period.ctime_to_period(time.ctime())
            
            another_present = next((True for entry in staff.attendance if entry.date == period.date and entry.month == period.month and entry.year == period.year), False)
            ct_data = (self.data.prefect_cit, self.data.prefect_cot) if isinstance(staff, Prefect) else (self.data.teacher_cit, self.data.teacher_cot)
            
            is_ci = is_check_in(period.time, ct_data[0], ct_data[1])
            
            if another_present and is_ci:
                return
            
            entry = AttendanceEntry(period, staff, is_ci)
            
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


class StaffListWidget(BaseScrollListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, tab_name: str, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__()
        prefects = sorted([(k, v) for k, v in data.prefects.items()], key=lambda params: params[1].name.full_name())
        teachers = sorted([(k, v) for k, v in data.teachers.items()], key=lambda params: params[1].name.full_name())
        boths = sorted([(k, v) for k, v in data.prefects.items()] + [(k, v) for k, v in data.teachers.items()], key=lambda params: params[1].name.full_name())
        
        prefects_widget = QWidget()
        prefects_layout = QVBoxLayout()
        prefects_widget.setLayout(prefects_layout)
        
        for _, prefect in prefects:
            prefects_layout.addWidget(StaffListPrefectEntryWidget(parent_widget, data, prefect, comm_system, card_scanner_index, staff_data_index))
        
        teachers_widget = QWidget()
        teachers_layout = QVBoxLayout()
        teachers_widget.setLayout(teachers_layout)
        
        for _, teacher in teachers:
            teachers_layout.addWidget(StaffListTeacherEntryWidget(parent_widget, data, teacher, comm_system, card_scanner_index, staff_data_index))
        
        boths_widget = QWidget()
        boths_layout = QVBoxLayout()
        boths_widget.setLayout(boths_layout)
        
        for _, both in boths:
            if isinstance(both, Teacher):
                boths_layout.addWidget(StaffListTeacherEntryWidget(parent_widget, data, both, comm_system, card_scanner_index, staff_data_index))
            else:
                boths_layout.addWidget(StaffListPrefectEntryWidget(parent_widget, data, both, comm_system, card_scanner_index, staff_data_index))
        
        self.widgets = {
            "All": boths_widget,
            "Prefects": prefects_widget,
            "Teachers": teachers_widget,
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(i == 0)
            self.main_layout.addWidget(staff_widget)
        
        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(index == i)

class AttendanceBarWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        # boths_widget = QWidget()
        # boths_layout = QVBoxLayout()
        # boths_widget.setLayout(boths_layout)
        
        # boths_layout.addWidget(prefect_widget)
        # boths_layout.addWidget(teacher_widget)
        
        self.prefect_info_widget = BarWidget("Cummulative Prefect Attendance", "Prefect Names", "Yearly Attendance (%)")
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        self.teacher_dep_widgets = {}
        
        _checked_departments = []
        for teacher in self.data.teachers.values():
            if teacher.department.id not in _checked_departments:
                dep_name = teacher.department.id
                
                widget = BarWidget(f"Cummulative {dep_name} Attendance", f"{dep_name} Department Teachers", "Yearly Attendance (%)")
                
                self.teacher_dep_widgets[teacher.department.id] = widget
                dtd_layout.addWidget(widget)
                
                _checked_departments.append(teacher.department.id)
        
        self.widgets = {
            "Prefects": LabeledField("Prefect Attendance", self.prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            "Teachers": LabeledField("Departmental Attendance", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            # "Both": boths_widget
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(i == 0)
            self.main_layout.addWidget(staff_widget)
        
        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(index == i)
    
    def prefect_data_changed(self):
        self.prefect_info_widget.clear()
        
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
            self.prefect_info_widget.add_data("Prefects", THEME_MANAGER.get_current_palette()["prefect"], (prefect_names, prefects_attendance_data))
    
    def teacher_data_changed(self):
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
            for index, (dep_id, (name, data)) in enumerate(teacher_data.items()):
                widget = self.teacher_dep_widgets[dep_id]
                widget.clear()
                widget.add_data(name, list(get_named_colors_mapping().values())[index], data)
    
    def get_percentage_attendance(self, attendance: list[AttendanceEntry], valid_attendance_days: list[str], interval: tuple[int, int]):
        remainder_days_amt = sum([day in valid_attendance_days for day in DAYS_OF_THE_WEEK[:interval[1] + 1]])
        max_attendance = (len(valid_attendance_days) * interval[0]) + remainder_days_amt
        
        percentage_attendance = sum(1 for entry in attendance if entry.day in valid_attendance_days) * 100 / (max_attendance if max_attendance else 1)
        
        return percentage_attendance


class PunctualityGraphWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        self.prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        
        _checked_departments = []
        for teacher in self.data.teachers.values():
            if teacher.department.id not in _checked_departments:
                dep_name = teacher.department.name
                
                dep_info_widget = GraphWidget(f"{dep_name} Department Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                
                dtd_layout.addWidget(dep_info_widget)
                
                _checked_departments.append(teacher.department.id)
        
        self.widgets = {
            "Prefects": LabeledField("Prefect Punctuality", self.prefect_info_widget),
            "Teachers": LabeledField("Departmental Punctuality", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            # "Both": boths_widget
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(i == 0)
            self.main_layout.addWidget(staff_widget)
        
        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(index == i)
    
    def prefect_data_changed(self):
        prefects_data = {}
        self.prefect_info_widget.clear()
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Prefect):
                prefects_data[staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        
        if prefects_data:
            for index, (name, prefect_data) in enumerate(prefects_data.values()):
                self.prefect_info_widget.plot(None, prefect_data, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def teacher_data_changed(self):
        teacher_data = {}
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Teacher):
                teacher_data[staff_attendance_data.staff.department.id][1][staff_attendance_data.staff.IUD] = self.get_punctuality_data(staff_attendance_data.staff)
        
        if teacher_data:
            dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
            
            for _, (dep_name, dep_data) in teacher_data.items():
                dep_info_widget = GraphWidget(f"{dep_name} Department Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                
                for index, (_, (name, info)) in enumerate(dep_data.items()):
                    dep_info_widget.plot(None, info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
                
                dtd_layout.addWidget(dep_info_widget)
            
            self.teacher_punctuality_widget = LabeledField("Departmental Punctuality", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        return self.teacher_punctuality_widget
    
    def get_punctuality_data(self, staff: Staff):
        prefects_plot_data: list[float] = []
        
        # weeks: list[list[Time]] = []
        
        # prev_day = DAYS_OF_THE_WEEK[0]
        # prev_dt = 1
        
        # for attendance in staff.attendance:
        #     if attendance.is_check_in:
        #         if ((DAYS_OF_THE_WEEK.index(attendance.period.day) > DAYS_OF_THE_WEEK.index(prev_day)) or
        #             (prev_dt != attendance.period.date and
        #             DAYS_OF_THE_WEEK.index(attendance.period.day) == DAYS_OF_THE_WEEK.index(prev_day))
        #             ):
        #             weeks.append([attendance.period.time])
        #         else:
        #             weeks[-1].append(attendance.period.time)
                
        #         prev_day = attendance.period.day
        #         prev_dt = attendance.period.date
        
        # for week_time in weeks:
        #     all_puncuality_in_week = [(self.data.prefect_cit.hour - t.hour) * 60 + (self.data.prefect_cit.min - t.min) + (self.data.prefect_cit.sec - t.sec) * (1/60) for t in week_time]
        #     weekly_punctuality = (sum(all_puncuality_in_week) if len(all_puncuality_in_week) else 0) / (len(all_puncuality_in_week) if len(all_puncuality_in_week) else 1)
        #     prefects_plot_data.append(weekly_punctuality)
        
        for attendance in staff.attendance:
            if attendance.is_check_in:
                prefects_plot_data.append(self.data.prefect_cit.in_minutes())
        
        return staff.name.abrev, prefects_plot_data


