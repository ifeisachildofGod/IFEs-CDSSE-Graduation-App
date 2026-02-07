from itertools import product

from theme import THEME_MANAGER

from widgets.base_widgets import *
from widgets.staff.entry_widgets import *
from widgets.data_display_widgets import *


class AttendanceWidget(BaseScrollListWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, parent_widget: TabViewWidget, data: AppData, attendance_chart_widget: "AttendanceBarWidget", punctuality_graph_widget: "PunctualityGraphWidget", comm_system: BaseCommSystem, saved_state_changed: pyBoundSignal, file_manager: FileManager, card_scanner_index: int):
        super().__init__()
        
        self.data = data
        self.comm_system = comm_system
        self.parent_widget = parent_widget
        self.saved_state_changed = saved_state_changed
        self.file_manager = file_manager
        self.card_scanner_index = card_scanner_index
        
        self.attendance_chart_widget = attendance_chart_widget
        self.punctuality_graph_widget = punctuality_graph_widget
        
        self.attendance_dict = {}
        
        self.create_time_labels()
        
        self.stack = QStackedWidget()
        
        cperiod = Period.str_to_period(time.ctime())
        self.other_years = sorted(set([str(att.period.year) for att in self.data.attendance_data if att.period.year not in (cperiod.year, cperiod.year - 1)]))
        
        self.filter_views = {}
        
        self.filter_data = [
            ["All (Staff)", "Prefects", "Teachers"],
            ["All (Timelines)", "Today", "This week", "This month", "This year", "Last year", "Last 5 years", "Last decade"] + self.other_years,
            ["Default (Display Format)", "Daily", "Weekly", "Monthly", "Yearly", "Dates (Categorised)", "Daily (Categorised)", "Monthly (Categorised)", "Yearly (Categorised)"]
        ]
        
        filter_combinations = [tuple(reversed(p)) for p in product(*reversed([range(len(l)) for l in self.filter_data]))]
        
        for index, comb in enumerate(filter_combinations):
            widget = self._determine_filter_widget_type(comb)
            
            self.stack.addWidget(widget)
            
            self.filter_views[comb] = [widget, len(self.data.attendance_data)]
        
        self.main_layout.addWidget(self.stack)
        
        self.main_layout.addStretch()
        
        self.comm_signal.connect(self.add_new_attendance_log)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.filter_widget, filter_layout = create_widget(None, QHBoxLayout)
        
        self.search_edit = SearchEdit(self._get_search_scope, self._goto_search)
        
        self.find_pb = QPushButton("Search Staff")
        self.find_pb.setFixedWidth(500)
        self.find_pb.setStyleSheet(f"background-color: {THEME_MANAGER.pallete_get("bg2")}; border: 1px solid {THEME_MANAGER.pallete_get("border")};")
        self.find_pb.clicked.connect(self._open_search_edit)
        
        filter_layout.addWidget(self.find_pb, alignment=Qt.AlignmentFlag.AlignLeft)
        filter_layout.addStretch()
        
        self.filter_comboboxes = []
        
        for index, f_data in enumerate(self.filter_data):
            filter = QComboBox()
            
            filter.addItems(f_data)
            filter.currentIndexChanged.connect(self._make_c_change_func(index))
            
            filter_layout.addWidget(filter, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.filter_comboboxes.append(filter)
        
        self.filter_comboboxes[0].setCurrentIndex(0)
        
        for attendance in self.data.attendance_data:
            self._add_attendance_log(attendance)
        
        self._layout.insertWidget(0, self.filter_widget)
    
    def _goto_search(self, sw: AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget | tuple[DropdownLabeledField, AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget]):
        if isinstance(sw, tuple):
            pass
        else:
            self.scroll_widget.verticalScrollBar().setValue(sw.y())
    
    def _get_search_scope(self):
        parent_widget: BaseListWidget | BaseFilterCategoriesWidget = self.stack.currentWidget()
        
        if isinstance(parent_widget, BaseListWidget):
            widgets: list[AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget] = parent_widget.get_widgets()
            
            return (
                sorted(
                    [
                        (sw, sw.staff.name.full_name(), (sw.data.period.to_str(), f"{f"{sw.staff.IUD} ° " if sw.staff.IUD else ""}{sw.staff.name.abrev}", "Prefect" if sw.staff.id in self.data.prefects else "Teacher"))
                        for sw in
                        widgets
                        ],
                    key=lambda params: params[1]
                    )
                )
        else:
            return []  # Sort out later
    
    def _open_search_edit(self):
        self.search_edit.move(self.filter_widget.mapToGlobal(QPoint(self.find_pb.x(), self.find_pb.y())))
        self.search_edit.search_le.setFocus()
        
        self.search_edit.show()
    
    def _determine_filter_widget_type(self, comb: tuple[int, ...]):
        return BaseListWidget(self.scroll_widget) if comb[1] in (0, 1) and comb[2] in (0, ) else BaseFilterCategoriesWidget(self.scroll_widget)
    
    def _add_attendance_entry(self, comb: tuple[int, ...], t_widget_entry: AttendanceEntry):
        if isinstance(t_widget_entry.staff, Teacher):
            t_widget = AttendanceTeacherEntryWidget(t_widget_entry)
        elif isinstance(t_widget_entry.staff, Prefect):
            t_widget = AttendancePrefectEntryWidget(t_widget_entry)
        else:
            raise TypeError(f"Type: {type(t_widget_entry.staff)} is not supported")
        
        parent_widg, _ = self.filter_views[comb]
        
        accepted, cls = self.filter(t_widget, comb)
        
        if accepted:
            parent_widg.addWidget(t_widget, cls)
    
    def _make_c_change_func(self, index: int):
        def func(i):
            comb = tuple((c.currentIndex() if c_i != index else i) for c_i, c in enumerate(self.filter_comboboxes))
            widg, att_i = self.filter_views[comb]
            
            for att_entry in self.data.attendance_data[att_i:]:
                self._add_attendance_entry(comb, att_entry)
            
            self.filter_views[comb][1] = len(self.data.attendance_data)

            self.stack.setCurrentWidget(widg)
        
        return func
    
    def _filter_category_fmt(self, entry_obj: BaseAttendanceEntryWidget, index: int, default: str | tuple[str, ...] | None):
        entry = entry_obj.data
        
        match index:
            case 0:
                return default
            case 1:
                return entry.period.day
            case 2:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                month_index = list(MONTHS_OF_THE_YEAR).index(entry.period.month)
                
                start_date = entry.period.date - day_index
                end_date = start_date + 6
                
                start_month = entry.period.month
                end_month = entry.period.month
                
                start_year = entry.period.year
                end_year = entry.period.year
                
                if start_date < 1:
                    if not month_index:
                        start_year -= 1
                    
                    start_month = list(MONTHS_OF_THE_YEAR)[month_index - 1]
                    start_date += MONTHS_OF_THE_YEAR[start_month]
                
                if end_date > MONTHS_OF_THE_YEAR[entry.period.month]:
                    if month_index == len(MONTHS_OF_THE_YEAR) - 1:
                        end_year += 1
                    
                    end_date = end_date % MONTHS_OF_THE_YEAR[entry.period.month]
                    end_month = list(MONTHS_OF_THE_YEAR)[(month_index + 1) % len(MONTHS_OF_THE_YEAR)]
                
                return f"{positionify(start_date)} {start_month} {start_year} - {positionify(end_date)} {end_month} {end_year}"
            case 3:
                return entry.period.month
            case 4:
                return entry.period.year
            case 5:
                return positionify(entry.period.date), entry.period.year, entry.period.month, entry.period.day
            case 6:
                return entry.period.day, entry.period.year, entry.period.month, positionify(entry.period.date)
            case 7:
                return entry.period.month, entry.period.year, entry.period.day, positionify(entry.period.date)
            case 8:
                return entry.period.year, entry.period.month, entry.period.day, positionify(entry.period.date)
        
        raise Exception()
    
    def _add_attendance_log(self, attendance_entry: AttendanceEntry, index=None):
        if isinstance(attendance_entry.staff, Teacher):
            self.attendance_chart_widget.teacher_data_changed()
            self.punctuality_graph_widget.teacher_data_changed()
        elif isinstance(attendance_entry.staff, Prefect):
            self.attendance_chart_widget.prefect_data_changed()
            self.punctuality_graph_widget.prefect_data_changed()
        else:
            raise TypeError(f"Type: {type(attendance_entry.staff)} is not supported")
        
        self.saved_state_changed.emit(False)
        
        curr_widget = self.stack.currentWidget()
        
        if index is not None:
            widg_comb = None
            
            for comb, (widget, _) in self.filter_views.items():
                if widget == curr_widget:
                    widg_comb = comb
                elif index < self.filter_views[comb][1]:
                    self.filter_views[comb][1] = index
            
            assert widg_comb
            
            self._add_attendance_entry(widg_comb, attendance_entry)
        else:
            for comb, (widget, _) in self.filter_views.items():
                self._add_attendance_entry(comb, attendance_entry)
    
    def filter(self, entry_obj: BaseAttendanceEntryWidget, comb: tuple[int, ...]):
        i1, i2, i3 = comb
        
        curr_period = Period.str_to_period(time.ctime())
        
        a_types = [(AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget), AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget]
        
        if isinstance(entry_obj, a_types[i1]):
            entry = entry_obj.data
            
            if i2 == 0:
                return True, self._filter_category_fmt(entry_obj, i3, None)
            elif i2 == 1:
                return (
                    entry_obj.data.period.date == curr_period.date and entry_obj.data.period.month == curr_period.month and entry_obj.data.period.year == curr_period.year,
                    self._filter_category_fmt(entry_obj, i3, None)
                )
            elif i2 == 2:
                obj_day_index = DAYS_OF_THE_WEEK.index(entry_obj.data.period.day)
                cur_day_index = DAYS_OF_THE_WEEK.index(curr_period.day)
                
                return (
                    cur_day_index - obj_day_index == curr_period.date - entry_obj.data.period.date and abs(entry_obj.data.period.in_days() - curr_period.in_days()) < 7,
                    self._filter_category_fmt(entry_obj, i3, entry.period.day)
                )
            elif i2 == 3:
                return (
                    curr_period.month == entry_obj.data.period.month and entry_obj.data.period.year == curr_period.year,
                    self._filter_category_fmt(entry_obj, i3, f"{entry.period.day}, {positionify(entry.period.date)} {entry.period.month}")
                )
            elif i2 == 4:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 5:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 1 == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 6:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 5 <= entry_obj.data.period.year <= curr_period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            curr_period.year,
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 7:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 10 <= entry_obj.data.period.year <= curr_period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            curr_period.year,
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            
            if 8 <= i2 <= 8 + len(self.other_years):
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    int(self.other_years[i2 - 8]) == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
        
        return False, None
    
    def current_period(self):
        period = Period.str_to_period(time.ctime())
        
        # period.time.hour = random.randint(0, 24)
        # period.time.min = random.randint(0, 60)
        # period.time.sec = random.randint(0, 60)
        
        # period.month = random.choice(list(MONTHS_OF_THE_YEAR))
        
        # prev_date = period.date % MONTHS_OF_THE_YEAR[period.month]
        # period.date = random.randint(1, MONTHS_OF_THE_YEAR[period.month])
        # period.day = DAYS_OF_THE_WEEK[(DAYS_OF_THE_WEEK.index(period.day) + period.date - prev_date) % 7]
        
        return period
    
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
        if self.parent_widget.stack.currentIndex() != self.card_scanner_index:
            staff = next((prefect for _, prefect in self.data.prefects.items() if prefect.IUD == IUD), None)
            
            if staff is None:
                staff = next((teacher for _, teacher in self.data.teachers.items() if teacher.IUD == IUD), None)
                
                if staff is None:
                    self.comm_system.send_message(f"UNREGISTERED {IUD}")
                    QMessageBox.warning(self.parent_widget, "CardScannerError", f"No staff is linked to this card (IUD: {IUD})")
                    
                    return
            
            period = self.current_period()
            
            another_present = next((True for entry in staff.attendance if entry.period.date == period.date and entry.period.month == period.month and entry.period.year == period.year), False)
            ct_data = (self.data.prefect_cit, self.data.prefect_cot) if isinstance(staff, Prefect) else (self.data.teacher_cit, self.data.teacher_cot)
            
            is_ci = is_check_in(period.time, ct_data[0], ct_data[1])
            
            if another_present and is_ci:
                return
            
            entry = AttendanceEntry(period, staff, is_ci)
            
            self.data.attendance_data.append(entry)
            staff.attendance.append(entry)
            
            self._add_attendance_log(entry, len(self.data.attendance_data) - 1)
            
            self.comm_system.send_message(f"LCD:{("Welcome" if not another_present else "Goodbye")} {staff.name.abrev}_-_{entry.period.time.hour}:{entry.period.time.min}:{entry.period.time.sec}")
            
            if self.file_manager.current_path is not None:
                self.file_manager.save()
    
    def keyPressEvent(self, a0):
        if a0.text() == "a":
            self.add_new_attendance_log("51232123A")
        elif a0.text() == "b":
            self.add_new_attendance_log("6999BDB2")
        elif a0.text() == "c":
            self.add_new_attendance_log("637B910C")
        elif a0.text() == "d":
            self.add_new_attendance_log("A3DEB30C")
        elif a0.text() == "e":
            self.add_new_attendance_log("B3A6DE0C")
        elif a0.text() == "f":
            self.add_new_attendance_log("89A2A1B4")
        
        return super().keyPressEvent(a0)

class StaffListWidget(BaseScrollListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__()
        
        self.data = data
        
        prefects = sorted([(k, v) for k, v in self.data.prefects.items()], key=lambda params: params[1].name.full_name())
        teachers = sorted([(k, v) for k, v in self.data.teachers.items()], key=lambda params: params[1].name.full_name())
        boths = sorted(prefects + teachers, key=lambda params: params[1].name.full_name())
        
        self._staffs_viewed: dict[str, StaffListPrefectEntryWidget | StaffListTeacherEntryWidget] = {}
        
        prefects_widget = QWidget()
        prefects_layout = QVBoxLayout()
        prefects_widget.setLayout(prefects_layout)
        
        for _, prefect in prefects:
            widget = StaffListPrefectEntryWidget(parent_widget, self.data, prefect, comm_system, card_scanner_index, staff_data_index)
            
            prefects_layout.addWidget(widget)
            self._staffs_viewed[widget.staff.id] = widget
        
        teachers_widget = QWidget()
        teachers_layout = QVBoxLayout()
        teachers_widget.setLayout(teachers_layout)
        
        for _, teacher in teachers:
            widget = StaffListTeacherEntryWidget(parent_widget, self.data, teacher, comm_system, card_scanner_index, staff_data_index)
            
            teachers_layout.addWidget(widget)
            self._staffs_viewed[widget.staff.id] = widget
        
        boths_widget = QWidget()
        boths_layout = QVBoxLayout()
        boths_widget.setLayout(boths_layout)
        
        for _, both in boths:
            widget = (
                StaffListTeacherEntryWidget(parent_widget, self.data, both, comm_system, card_scanner_index, staff_data_index)
                if isinstance(both, Teacher) else
                StaffListPrefectEntryWidget(parent_widget, self.data, both, comm_system, card_scanner_index, staff_data_index)
            )
            
            boths_layout.addWidget(widget)
            self._staffs_viewed[widget.staff.id] = widget
        
        self.widgets = {
            "All": boths_widget,
            "Prefects": prefects_widget,
            "Teachers": teachers_widget,
        }
        
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(i == 0)
            self.main_layout.addWidget(staff_widget)
        
        self.filter_widget, filter_layout = create_widget(None, QHBoxLayout)
        
        self.filter_cb = QComboBox()
        self.filter_cb.addItems(list(self.widgets))
        self.filter_cb.currentIndexChanged.connect(self.filter)
        
        self.search_edit = SearchEdit(self._get_search_scope, lambda sw: self.scroll_widget.verticalScrollBar().setValue(sw.y()))
        
        self.find_pb = QPushButton("Search Staff")
        self.find_pb.setFixedWidth(500)
        self.find_pb.setStyleSheet(f"background-color: {THEME_MANAGER.pallete_get("bg2")}; border: 1px solid {THEME_MANAGER.pallete_get("border")};")
        self.find_pb.clicked.connect(self._open_search_edit)
        
        filter_layout.addWidget(self.find_pb, alignment=Qt.AlignmentFlag.AlignLeft)
        filter_layout.addWidget(self.filter_cb, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._layout.insertWidget(0, self.filter_widget)
    
    def _get_search_scope(self):
        return (
            sorted(
                [
                    (sw, sw.staff.name.full_name(), (sw.staff.name.abrev, sw.staff.IUD, "Prefect" if sw.staff.id in self.data.prefects else "Teacher"))
                    for sw in
                    self._staffs_viewed.values()
                    if (
                        self.filter_cb.currentIndex() == 0 or
                        (sw.staff.id in self.data.prefects and self.filter_cb.currentIndex() == 1) or
                        (sw.staff.id in self.data.teachers and self.filter_cb.currentIndex() == 2)
                        )
                    ],
                key=lambda params: params[1]
                )
            )
    
    def _open_search_edit(self):
        self.search_edit.move(self.filter_widget.mapToGlobal(QPoint(self.find_pb.x(), self.find_pb.y())))
        self.search_edit.search_le.setFocus()
        
        self.search_edit.show()
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            staff_widget.setVisible(index == i)



class AttendanceBarWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.data = data
        
        self.prefect_info_widget = BarWidget("Cummulative School Prefect Attendance", "School Prefects", "Yearly Attendance (%)")
        self.prefect_info_widget.bar_canvas.axes.set_ylim(top=100)
        
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        self.teacher_dep_widgets = {}
        
        for teacher in self.data.teachers.values():
            if teacher.department.id not in self.teacher_dep_widgets:
                self.teacher_dep_widgets[teacher.department.id] = BarWidget(f"Cummulative {teacher.department.name} Department Attendance", f"{teacher.department.name} Department Teachers", "Yearly Attendance (%)")
                self.teacher_dep_widgets[teacher.department.id].bar_canvas.axes.set_ylim(top=100)
                
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
            if isinstance(staff_widget, tuple) and index == i:
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
            else:
                staff_widget.setVisible(index == i)
    
    def prefect_data_changed(self):
        self.prefect_info_widget.clear()
        
        prefect_data = {}
        
        for prefect in self.data.prefects.values():
            valid_days = list(prefect.duties)
            latest_attendance_period = next((p.period for p in reversed(prefect.attendance) if p.is_check_in), None)
            
            if latest_attendance_period:
                percentage_attendance = self.get_percentage_attendance(prefect.attendance, valid_days, latest_attendance_period)
                
                if percentage_attendance:
                    prefect_data[prefect.id] = prefect.name.abrev, percentage_attendance
        
        for index, (name, data) in enumerate(prefect_data.values()):
            self.prefect_info_widget.add_data(name, list(get_named_colors_mapping().values())[index], ([name], [data]))
    
    def teacher_data_changed(self):
        teacher_data: dict[tuple[str, str], list[tuple[list[str], list[int]]]] = {}
        
        for teacher in self.data.teachers.values():
            valid_days = list(set(flatten([[day for day, _ in s.periods] for s in teacher.subjects])))
            latest_attendance_period = next((t.period for t in reversed(teacher.attendance) if t.is_check_in and t.period.day in valid_days), None)
            
            if latest_attendance_period:
                percentage_attendance = self.get_percentage_attendance(teacher.attendance, valid_days, latest_attendance_period)
                
                if percentage_attendance:
                    key = teacher.department.id, teacher.department.name
                    t_data = [teacher.name.full_name()], [percentage_attendance]
                    
                    if teacher.department.id not in teacher_data:
                        teacher_data[key] = [t_data]
                    
                    teacher_data[key].append(t_data)
        
        if teacher_data:
            index = 0
            
            for (dep_id, dep_name), total_teacher_data in teacher_data.items():
                widget = self.teacher_dep_widgets[dep_id]
                widget.clear()
                
                for t_data in total_teacher_data:
                    index += 1
                    widget.add_data(dep_name, list(get_named_colors_mapping().values())[index], t_data)
    
    def get_percentage_attendance(self, attendance: list[AttendanceEntry], valid_attendance_days: list[str], latest_attendance_period: Period):
        months = list(MONTHS_OF_THE_YEAR)
        
        prefect_timeline_period_sp = self.data.prefect_timeline_dates[0].copy()
        prefect_timeline_period_sp.date += 7 - DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day)
        if prefect_timeline_period_sp.date > MONTHS_OF_THE_YEAR[prefect_timeline_period_sp.month]:
            new_month_index = months.index(prefect_timeline_period_sp.month) + 1
            
            prefect_timeline_period_sp.date = MONTHS_OF_THE_YEAR[prefect_timeline_period_sp.month] - prefect_timeline_period_sp.date
            prefect_timeline_period_sp.month = months[new_month_index % len(months)]
            
            prefect_timeline_period_sp.year += new_month_index // len(months)
        
        latest_attendance_period_ep = latest_attendance_period.copy()
        latest_attendance_period_ep.date -= DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day) + 1
        if latest_attendance_period_ep.date < 1:
            new_month_index = months.index(latest_attendance_period_ep.month) - 1
            
            latest_attendance_period_ep.month = months[new_month_index % len(months)]
            latest_attendance_period_ep.date += MONTHS_OF_THE_YEAR[latest_attendance_period_ep.month]
            
            latest_attendance_period_ep.year += new_month_index // len(months)
        
        interval = abs(
            len([day for day in valid_attendance_days if DAYS_OF_THE_WEEK.index(day) >= DAYS_OF_THE_WEEK.index(self.data.prefect_timeline_dates[0].day)]) +
            len(valid_attendance_days) * int(latest_attendance_period_ep.in_weeks() - prefect_timeline_period_sp.in_weeks()) +
            len([day for day in valid_attendance_days if DAYS_OF_THE_WEEK.index(day) <= DAYS_OF_THE_WEEK.index(latest_attendance_period.day)])
        )
        
        attendance_amt = len([a for a in attendance if a.period.day in valid_attendance_days and a.is_check_in])
        
        return int(100 * attendance_amt / interval) if interval else None

class PunctualityGraphWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
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
            if isinstance(staff_widget, tuple) and index == i:
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
            else:
                staff_widget.setVisible(index == i)
    
    def prefect_data_changed(self):
        prefects_data = []
        self.prefect_info_widget.clear()
        
        for prefect in self.data.prefects.values():
            prefects_data.append(self.get_punctuality_data(prefect))
        
        if prefects_data:
            for index, (name, prefect_data) in enumerate(prefects_data):
                self.prefect_info_widget.plot(None, prefect_data, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def teacher_data_changed(self):
        teacher_data = {}
        
        for teacher in self.data.teachers.values():
            s_id = teacher.department.id
            
            teacher_data[s_id] = self.get_punctuality_data(teacher)
            self.teacher_info_widgets[s_id].clear()
        
        if teacher_data:
            for index, (dep_id, (name, info)) in enumerate(teacher_data.items()):
                self.teacher_info_widgets[dep_id].plot(None, info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def get_punctuality_data(self, staff: Staff):
        prefects_plot_data: list[float] = []
        
        for attendance in staff.attendance:
            if attendance.is_check_in:
                prefects_plot_data.append(len(prefects_plot_data) + self.data.prefect_cit.in_minutes() - attendance.period.time.in_minutes())
        
        return staff.name.abrev, prefects_plot_data


