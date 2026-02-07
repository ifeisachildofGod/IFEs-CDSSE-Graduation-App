
from widgets.base_widgets import *
from widgets.data_display_widgets import *


class BaseOptionsWidget(QWidget):
    def __init__(self, parent_widget: TabViewWidget, widget_type: Literal["scrollable", "static"]):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        self.container, self.main_layout = create_scrollable_widget(layout, QVBoxLayout) if widget_type == "scrollable" else (create_widget(layout, QVBoxLayout) if widget_type == "static" else None)
        
        self.parent_widget = parent_widget
        
        _, upper_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cancel_button = QPushButton("×")
        cancel_button.setFixedSize(30, 30)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                font-size: 30px;
                border-radius: 15px;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: {THEME_MANAGER.pallete_get("hover3")};
            }}
        """)
        cancel_button.clicked.connect(self.finished)
        
        upper_layout.addStretch()
        upper_layout.addWidget(cancel_button, Qt.AlignmentFlag.AlignRight)
        
        self.staff: Staff | None = None
        self.staff_index: int | None = None
    
    def set_self(self, staff: Staff):
        self.staff = staff
    
    def finished(self):
        self.parent_widget.set_tab("Staff")
        
        self.staff = None
        self.staff_index = None


class StaffDataWidget(BaseOptionsWidget):
    def __init__(self, data: AppData, parent_widget: TabViewWidget):
        super().__init__(parent_widget, "scrollable")
        
        self.data = data
        
        self.staff_working_days = {}
        
        for prefect in self.data.prefects.values():
            self.staff_working_days[prefect.id] = list(prefect.duties)
        
        for teacher in self.data.teachers.values():
            self.staff_working_days[teacher.id] = list(set(flatten([[d for d, _ in s.periods] for s in teacher.subjects])))
        
        self.attendance_amt_widget = QLabel()
        
        self.punctuality_widget: GraphWidget | None = None
        
        self.attendance_widget = BarWidget("", "Time (Weeks)", "Attendance (%)")
        self.attendance_widget.bar_canvas.axes.set_ylim(0, 110)
        
        self.punctuality_widget = GraphWidget("", "Scan Interval", "Punctuality (Minutes)")
        
        stats_widget, stats_layout = create_widget(None, QVBoxLayout)
        chart_widget, chart_layout = create_widget(None, QVBoxLayout)
        
        stats_layout.addWidget(self.attendance_amt_widget)
        
        chart_layout.addWidget(self.attendance_widget)
        chart_layout.addWidget(self.punctuality_widget)
        
        self.main_layout.addWidget(LabeledField("Stats", stats_widget))
        self.main_layout.addWidget(LabeledField("Graphs and Charts", chart_widget))
    
    def set_self(self, staff):
        super().set_self(staff)
        
        if isinstance(staff, Teacher):
            bar_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Punctuality Graph"
            staff_list = list(self.data.teachers)
            cit = self.data.teacher_cit
        elif isinstance(staff, Prefect):
            bar_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Average Punctuality Graph"
            staff_list = list(self.data.prefects)
            cit = self.data.prefect_cit
        else:
            raise Exception()
        
        self.attendance_widget.clear()
        self.punctuality_widget.clear()
        
        self.attendance_widget.set_title(bar_title)
        self.punctuality_widget.set_title(graph_title)
        
        color = list(get_named_colors_mapping().values())[staff_list.index(staff.id) % len(list(get_named_colors_mapping().values()))]
        
        weeks_data = {}
        
        for attendance in staff.attendance:
            if attendance.is_check_in and attendance.period.day in self.staff_working_days[attendance.staff.id]:
                curr_index = DAYS_OF_THE_WEEK.index(attendance.period.day)
                
                days = self.staff_working_days[staff.id]
                
                if attendance.period.date - curr_index < 1:
                    start_date = 1
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) < abs(attendance.period.date - curr_index) + 1)]
                else:
                    start_date = attendance.period.date - curr_index
                
                if attendance.period.date - curr_index + 6 > MONTHS_OF_THE_YEAR[attendance.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[attendance.period.month]
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) > MONTHS_OF_THE_YEAR[attendance.period.month] - (attendance.period.date - curr_index))]
                else:
                    end_date = attendance.period.date - curr_index + 6
                
                name_key = f"{attendance.period.month} {attendance.period.year}\n{positionify(start_date)} to {positionify(end_date)}"
                
                if days:
                    if name_key not in weeks_data:
                        weeks_data[name_key] = [0, len(days)]
                    
                    weeks_data[name_key][0] += 1
        
        weeks_data = {key: amt_attended / total * 100 for key, (amt_attended, total) in weeks_data.items()}
        self.attendance_widget.add_data(f"{staff.name.full_name()} Attendance Data", color, weeks_data)
        
        y_plot_points = [cit.in_minutes() - attendance.period.time.in_minutes() for attendance in staff.attendance if attendance.is_check_in and attendance.period.day in self.staff_working_days[staff.id]]
        
        self.punctuality_widget.plot(None, y_plot_points, marker='o', color=color)
        
        self.attendance_amt_widget.setText(f"<span style='font-weight: 500; color: #eeeeee;'>Attendance</span><b>:</b><span style='font-weight: 900; color: #ffffff;'> {str(int(sum(list(weeks_data.values())) / len(weeks_data))) + "%" if weeks_data else "No Data"}</span>")

class CardScanScreenWidget(BaseOptionsWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, comm_system: BaseCommSystem, parent_widget: TabViewWidget, saved_state_changed: pyBoundSignal):
        super().__init__(parent_widget, "static")
        self.comm_system = comm_system
        self.saved_state_changed = saved_state_changed
        
        self.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: bold;
            }
        """)
        
        scan_img = Image("src/images/scan.png", height=330)
        scan_img.setStyleSheet("margin-bottom: 20px;")
        self.main_layout.addWidget(scan_img, alignment=Qt.AlignmentFlag.AlignCenter)
        
        info = QLabel("Please scan RFID card")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_label, Qt.AlignmentFlag.AlignCenter)
        
        self.comm_signal.connect(self.scanned)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.iud_label = None
        
        self.comm_system.connection_changed_signal.connect(self.connection_changed)
        self.iud_changed = False
    
    def set_self(self, staff: Staff, iud_label: QLabel):
        super().set_self(staff)
        
        self.iud_label = iud_label
        
        self.info_label.setText(f"To link an IUD to {self.staff.name.sur} {self.staff.name.first} (ID: {self.staff.id})")
    
    def finished(self):
        self.iud_label = None
        if self.iud_changed:
            self.comm_system.send_message(f"LCD:{self.staff.name.abrev} IUD_-_set to {self.staff.IUD}")
        return super().finished()
    
    def connection_changed(self, state: bool):
        if not state and self.parent_widget.stack.indexOf(self) == self.parent_widget.stack.currentIndex():
            self.finished()
    
    def scanned(self, data: str):
        if self.parent_widget.stack.currentIndex() == self.parent_widget.stack.indexOf(self):
            self.staff.IUD = data
            self.iud_label.setText(self.staff.IUD)
            
            self.saved_state_changed.emit(False)
            
            self.iud_changed = True
            self.finished()
            self.iud_changed = False

