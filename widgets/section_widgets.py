from itertools import product
import random
from PyQt6.QtWidgets import QComboBox
from theme import THEME_MANAGER
from widgets.section_sub_widgets import *
from data.time_data_objects import *


class BaseListWidget(QWidget):
    def __init__(self, scroll_area: QScrollArea) -> None:
        super().__init__()
        
        self.scroll_area = scroll_area
        
        self.container = QWidget(self)          # ✅ keep reference + parent
        self.main_layout = QVBoxLayout(self.container)
        self.container.setLayout(self.main_layout)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.container)  # ✅ add to visible hierarchy
        self.setLayout(self._layout)
    
    # Category name is here to avoid edge cases
    def addWidget(self, widget: QWidget, category_name: str | None = None, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.addWidget(widget, stretch, alignment)
        else:
            self.main_layout.addWidget(widget, stretch)
        
        widget.show()
        widget.adjustSize()
        
        self.scroll_area.ensureWidgetVisible(widget, xMargin=0, yMargin=10)

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
    
    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.addWidget(widget, stretch, alignment)
        else:
            self.main_layout.addWidget(widget, stretch)


class _FilterCategoriesWidget(BaseListWidget):
    def __init__(self, scroll_area: QScrollArea):
        super().__init__(scroll_area)
        
        self.category_widgets = {}
    
    def addWidget(self, widget: "AttendanceWidget", category_name: str, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if category_name not in self.category_widgets:
            cat_widg = QWidget()
            cat_layout = QVBoxLayout()
            cat_widg.setLayout(cat_layout)
            
            self.category_widgets[category_name] = DropdownLabeledField(category_name, cat_widg, True)
            
            super().addWidget(self.category_widgets[category_name])
        
        if alignment is not None:
            self.category_widgets[category_name].addWidget(widget, stretch, alignment)
        else:
            self.category_widgets[category_name].addWidget(widget, stretch)

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
        
        self.filter_data = [[["All", "Prefects", "Teachers"], 0], [["All", "Today", "This week", "This month", "This year"], 0]]
        
        filter_combinations = [tuple(reversed(p)) for p in product(*reversed([range(len(l)) for l, _ in self.filter_data]))]
        
        for comb in filter_combinations:
            widget = self._determine_filter_widget_type(comb)
            
            self.main_layout.addWidget(widget)
            
            self.filter_views[comb] = widget
        
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
            
            filter.setCurrentIndex(0)
            
            filter_layout.addWidget(filter, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._layout.insertWidget(0, filter_widget, alignment=Qt.AlignmentFlag.AlignRight)
    
    def _determine_category_name(self, comb: tuple[int, ...], entry: AttendanceEntry):
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
    
    def _determine_filter_widget_type(self, comb: tuple[int, ...]):
        return BaseListWidget(self.scroll_widget) if comb[1] in (0, 1) else _FilterCategoriesWidget(self.scroll_widget)
    
    def _make_c_change_func(self, index: int):
        def c_change(i):
            self.filter(*tuple((i if index == s_i else None) for s_i in range(len(self.filter_data))))
        
        return c_change
    
    def _assess_filter(self, a_obj: BaseAttendanceEntryWidget, comb: tuple[int, ...]):
        i1, i2 = comb
        
        curr_period = self.current_period()
        
        a_types = [(AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget), AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget]
        
        if isinstance(a_obj, a_types[i1]):
            if i2 == 0:
                return True
            elif i2 == 1:
                return a_obj.data.period.date == curr_period.date
            elif i2 == 2:
                obj_day_index = DAYS_OF_THE_WEEK.index(a_obj.data.period.day)
                cur_day_index = DAYS_OF_THE_WEEK.index(curr_period.day)
                
                return cur_day_index - obj_day_index == curr_period.date - a_obj.data.period.date
            elif i2 == 3:
                return curr_period.month == a_obj.data.period.month
            elif i2 == 4:
                return curr_period.year == a_obj.data.period.year
        
        return False
    
    def _add_attendance_log(self, attendance_entry: AttendanceEntry):
        if isinstance(attendance_entry.staff, Teacher):
            widget_class = AttendanceTeacherEntryWidget
            
            self.attendance_chart_widget.teacher_data_changed()
            self.punctuality_graph_widget.teacher_data_changed()
        elif isinstance(attendance_entry.staff, Prefect):
            widget_class = AttendancePrefectEntryWidget
            
            self.attendance_chart_widget.prefect_data_changed()
            self.punctuality_graph_widget.prefect_data_changed()
        else:
            raise TypeError(f"Type: {type(attendance_entry.staff)} is not supported")
        
        self.saved_state_changed.emit(False)
        
        for comb, m_widget in self.filter_views.items():
            widget = widget_class(attendance_entry)
            
            if self._assess_filter(widget, comb):
                m_widget.addWidget(widget, self._determine_category_name(comb, widget.data))
    
    def current_period(self):
        period = Period.str_to_period(time.ctime())
        
        period.time.hour = random.randint(1, 24)
        period.time.min = random.randint(1, 60)
        period.time.sec = random.randint(1, 60)
        
        period.month = random.choice(list(MONTHS_OF_THE_YEAR))
        
        prev_date = period.date % MONTHS_OF_THE_YEAR[period.month]
        period.date = random.randint(1, MONTHS_OF_THE_YEAR[period.month])
        period.day = DAYS_OF_THE_WEEK[(DAYS_OF_THE_WEEK.index(period.day) + period.date - prev_date) % 7]
        
        return period
    
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
    
    def add_new_attendance_log(self, IUD: str):
        staff = next((prefect for _, prefect in self.data.prefects.items() if prefect.IUD == IUD), None)
        
        if staff is None:
            staff = next((teacher for _, teacher in self.data.teachers.items() if teacher.IUD == IUD), None)
        
        if staff is not None:
            period = self.current_period()
            
            another_present = next((True for entry in staff.attendance if entry.period.date == period.date and entry.period.month == period.month and entry.period.year == period.year), False)
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
        
        self.prefect_info_widget = BarWidget("Cummulative School Prefect Attendance", "School Prefects", "Yearly Attendance (%)")
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        self.teacher_dep_widgets = {}
        
        for teacher in self.data.teachers.values():
            if teacher.department.id not in self.teacher_dep_widgets:
                self.teacher_dep_widgets[teacher.department.id] = BarWidget(f"Cummulative {teacher.department.name} Department Attendance", f"{teacher.department.name} Department Teachers", "Yearly Attendance (%)")
                
                dtd_layout.addWidget(self.teacher_dep_widgets[teacher.department.id])
        
        self.widgets = {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Attendance", self.prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            "Teachers": LabeledField("Departmental Attendance", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not isinstance(staff_widget, tuple):
                staff_widget.setVisible(i == 0)
                self.main_layout.addWidget(staff_widget)
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not i and isinstance(staff_widget, tuple):
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
        
        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            if isinstance(staff_widget, tuple):
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
            else:
                staff_widget.setVisible(index == i)
    
    def prefect_data_changed(self):
        self.prefect_info_widget.clear()
        
        prefect_names = []
        prefects_attendance_data = []
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Prefect):
                valid_days = list(staff_attendance_data.staff.duties)
                latest_attendance_period = next((p.period for p in reversed(staff_attendance_data.staff.attendance) if p.is_check_in), None)
                
                if latest_attendance_period:
                    percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, valid_days, latest_attendance_period)
                    
                    prefect_names.append(staff_attendance_data.staff.name.abrev)
                    prefects_attendance_data.append(percentage_attendance)
        
        if prefects_attendance_data:
            self.prefect_info_widget.add_data("Prefects", THEME_MANAGER.get_current_palette()["prefect"], (prefect_names, prefects_attendance_data))
    
    def teacher_data_changed(self):
        teacher_data: dict[str, tuple[str, tuple[list[str], list[int]]]] = {}
        
        for staff_attendance_data in self.data.attendance_data:
            if isinstance(staff_attendance_data.staff, Teacher):
                valid_days = list(set(flatten([[day for day, _ in s.periods] for s in staff_attendance_data.staff.subjects])))
                latest_attendance_period = next((t.period for t in reversed(staff_attendance_data.staff.attendance) if t.is_check_in), None)
                
                if latest_attendance_period:
                    percentage_attendance = self.get_percentage_attendance(staff_attendance_data.staff.attendance, valid_days, latest_attendance_period)
                    
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
    
    def get_percentage_attendance(self, attendance: list[AttendanceEntry], valid_attendance_days: list[str], latest_attendance_period: Period):
        prefect_timeline_period_sp = self.data.prefect_timeline_dates[0].copy()
        prefect_timeline_period_sp.time.hour += (7 - DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day)) * 24
        
        latest_attendance_period_ep = latest_attendance_period.copy()
        latest_attendance_period_ep.time.hour -= (DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day) + 1) * 24
        
        interval = (
            len([day for day in valid_attendance_days if DAYS_OF_THE_WEEK.index(day) >= DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day)]) +
            len(valid_attendance_days) * int(latest_attendance_period_ep.in_weeks() - prefect_timeline_period_sp.in_weeks()) +
            len([day for day in valid_attendance_days if DAYS_OF_THE_WEEK.index(day) <= DAYS_OF_THE_WEEK.index(latest_attendance_period.day)])
        )
        
        attendance_amt = len([a for a in attendance if a.period.day in valid_attendance_days and a.is_check_in])
        
        return int(attendance_amt / interval * 100)


class PunctualityGraphWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.data = data
        
        self.prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        
        self.teacher_info_widgets = {}
        for teacher in self.data.teachers.values():
            if teacher.department.id not in self.teacher_info_widgets:
                dep_name = teacher.department.name
                
                self.teacher_info_widgets[teacher.department.id] = GraphWidget(f"{dep_name} Department Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                
                dtd_layout.addWidget(self.teacher_info_widgets[teacher.department.id])
        
        self.widgets = {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Punctuality", self.prefect_info_widget),
            "Teachers": LabeledField("Departmental Punctuality", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not isinstance(staff_widget, tuple):
                staff_widget.setVisible(i == 0)
                self.main_layout.addWidget(staff_widget)
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not i and isinstance(staff_widget, tuple):
                for k in staff_widget:
                    self.widgets[k].setVisible(True)

        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            if isinstance(staff_widget, tuple):
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
            else:
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
                teacher_data[staff_attendance_data.staff.department.id] = self.get_punctuality_data(staff_attendance_data.staff)
        
        if teacher_data:
            for dep_id, dep_data in teacher_data.items():
                self.teacher_info_widgets[dep_id].clear()
                
                for index, (name, info) in enumerate(dep_data.items()):
                    self.teacher_info_widgets[dep_id].plot(None, info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def get_punctuality_data(self, staff: Staff):
        prefects_plot_data: list[float] = []
        
        for attendance in staff.attendance:
            if attendance.is_check_in:
                prefects_plot_data.append(len(prefects_plot_data) + self.data.prefect_cit.in_minutes() - attendance.period.time.in_minutes())
        
        return staff.name.abrev, prefects_plot_data


