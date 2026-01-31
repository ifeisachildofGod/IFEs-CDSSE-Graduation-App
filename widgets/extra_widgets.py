
from widgets.base_widgets import *

class BaseExtraWidget(QWidget):
    def __init__(self, parent_widget: TabViewWidget, widget_type: Literal["scrollable", "static"]):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        self.container, self.main_layout = create_scrollable_widget(layout, QVBoxLayout) if widget_type == "scrollable" else (create_widget(layout, QVBoxLayout) if widget_type == "static" else None)
        
        self.parent_widget = parent_widget
        
        _, upper_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cancel_button = QPushButton("×")
        cancel_button.setFixedSize(30, 30)
        cancel_button.setStyleSheet("font-size: 25px; border-radius: 15px; padding: 0px")
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


class StaffDataWidget(BaseExtraWidget):
    def __init__(self, data: AppData, parent_widget: TabViewWidget):
        super().__init__(parent_widget, "scrollable")
        
        self.data = data
        
        self.staff_working_days = {}
        
        for prefect in self.data.prefects.values():
            self.staff_working_days[prefect.id] = list(prefect.duties)
        
        for teacher in self.data.teachers.values():
            self.staff_working_days[teacher.id] = list(set(flatten([[d for d, _ in s.periods] for s in teacher.subjects])))
        
        self.attendance_widget: BarWidget | None = None
        self.punctuality_widget: GraphWidget | None = None
    
    def set_self(self, staff):
        super().set_self(staff)
        
        if self.attendance_widget is not None:
            self.main_layout.removeWidget(self.attendance_widget)
            self.attendance_widget.deleteLater()
        
        if self.punctuality_widget is not None:
            self.main_layout.removeWidget(self.punctuality_widget)
            self.punctuality_widget.deleteLater()
        
        if isinstance(staff, Teacher):
            bar_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Punctuality Graph"
            # week_days = list(set(flatten([[day for day, _ in s.periods] for s in staff.subjects])))
            # timeline_dates = self.data.teacher_timeline_dates
            staff_list = list(self.data.teachers)
            cit = self.data.teacher_cit
        elif isinstance(staff, Prefect):
            bar_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Average Punctuality Graph"
            # week_days = list(staff.duties.keys())
            # timeline_dates = self.data.prefect_timeline_dates
            staff_list = list(self.data.prefects)
            cit = self.data.prefect_cit
        else:
            raise Exception()
        
        # months = []
        # percentile_values = []
        
        self.attendance_widget = BarWidget(bar_title, "Time (Weeks)", "Attendance (%)")
        self.attendance_widget.bar_canvas.axes.set_ylim(0, 110)
        
        self.punctuality_widget = GraphWidget(graph_title, "Time", "Punctuality (Minutes)")
        
        color = list(get_named_colors_mapping().values())[staff_list.index(staff.id) % len(list(get_named_colors_mapping().values()))]
            
        labels_data = []
        weeks_data = []
        
        for index, attendance in enumerate(staff.attendance):
            if index:
                if attendance.is_check_in and attendance.period.day in self.staff_working_days[attendance.staff.id]:
                    curr_index = DAYS_OF_THE_WEEK.index(attendance.period.day)
                    prev_index = DAYS_OF_THE_WEEK.index(staff.attendance[index - 1].period.day)
                    
                    if curr_index - prev_index == attendance.period.date - staff.attendance[index - 1].period.date:
                        
                        labels_data.append(f"{attendance.period.month} {attendance.period.year}\n{attendance.period.date - curr_index} to {attendance.period.date + (6 - curr_index)}")
                        weeks_data.append(0)
                    
                    weeks_data[-1] += 1
            else:
                labels_data.append(f"{attendance.period.month} {attendance.period.year}\n{attendance.period.date - curr_index} to {attendance.period.date + (6 - curr_index)}")
                weeks_data.append(1)
            
            # monthly_attendance_data[f"{attendance.month} {attendance.year}"] = monthly_attendance_data.get(f"{attendance.month} {attendance.year}", 0) + 1
        
        weeks_data = [dt / self.staff_working_days[staff.id] * 100 for dt in weeks_data]
        self.attendance_widget.add_data(f"{staff.name.full_name()} Attendance Data", color, (labels_data, weeks_data))
        
        y_plot_points = [index + (cit.in_minutes() - attendance.period.in_minutes()) for index, attendance in enumerate(staff.attendance) if attendance.is_check_in]
        
        self.punctuality_widget.plot(None, y_plot_points, marker='o', color=color)
        
        stats_widget, stats_layout = create_widget(None, QVBoxLayout)
        chart_widget, chart_layout = create_widget(None, QVBoxLayout)
        
        stats_layout.addWidget(QLabel(f"<span style='font-weight: 500; color: #eeeeee;'>Attendance</span><b>:</b><span style='font-weight: 900; color: #ffffff;'> {str(int(sum(weeks_data) / (self.staff_working_days[staff.id] * len(weeks_data)) * 100)) + "%" if weeks_data else "No Data"}</span>"))
        
        chart_layout.addWidget(self.attendance_widget)
        chart_layout.addWidget(self.punctuality_widget)
        
        self.main_layout.addWidget(LabeledField("Stats", stats_widget))
        self.main_layout.addWidget(LabeledField("Graphs and Charts", chart_widget))
        

class CardScanScreenWidget(BaseExtraWidget):
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
        
        scan_img = Image("src/icons-and-images/scan.png", height=330)
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
    
    def set_self(self, staff: Staff, staff_index: int, iud_label: QLabel):
        super().set_self(staff, staff_index)
        
        self.iud_label = iud_label
        
        self.info_label.setText(f"To link an IUD to {self.staff.name.sur} {self.staff.name.first} (ID: {self.staff.id})")
    
    def finished(self):
        self.iud_label = None
        if not self.iud_changed:
            self.comm_system.send_message("NOT SCANNING")
        return super().finished()
    
    def connection_changed(self, state: bool):
        if not state and self.parent_widget.stack.indexOf(self) == self.parent_widget.stack.currentIndex():
            self.finished()
    
    def scanned(self, data: str):
        if self.parent_widget.stack.indexOf(self) == self.parent_widget.stack.currentIndex():
            self.staff.IUD = data
            self.iud_label.setText(self.staff.IUD)
            
            self.saved_state_changed.emit(False)
            self.comm_system.send_message(f"setId:{self.staff.name.abrev},0,{time.ctime()}")
            
            self.iud_changed = True
            self.finished()
            self.iud_changed = False



class SetupScreen(QDialog):
    update_signal = pySignal(dict, list)
    bluetooth_state_signal = pySignal(bool)
    
    def __init__(self, parent: QMainWindow, connector: BaseCommSystem):
        super().__init__(parent=parent)
        
        self.connector = connector
        
        self.setFocus()
        self.setModal(True)
        self.setWindowTitle("Connection Config")
        self.setFixedWidth(700)
        self.setFixedHeight(500)
        
        self.connected = False
        self.connect_clicked = False
        self.connect_only_widgets = []
        self.data: dict[str, str | int | Literal["bt", "ser"]] = {}
        
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container, self.main_layout = create_widget(layout, QVBoxLayout)
        
        
        serial_widget, serial_layout = create_widget(None, QVBoxLayout)
        serial_widget.setProperty("class", "labeled-widget")
        bluetooth_widget, bluetooth_layout = create_widget(None, QVBoxLayout)
        bluetooth_widget.setProperty("class", "labeled-widget")
        
        self.main_widget = TabViewWidget()
        self.main_widget.add("Serial Connection", serial_widget)
        self.main_widget.add("BLE Connection", bluetooth_widget)
        
        _, serial_upper_buttons_layout = create_widget(serial_layout, QHBoxLayout)
        
        def bt_state_signal():
            self.refresh("ser", self.serial_refresh_button)
            self.bluetooth_state_signal.emit(True)
        
        self.serial_refresh_button = QPushButton("Refresh")
        self.serial_refresh_button.clicked.connect(bt_state_signal)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.serial_connect_clicked(-1))
        self.connect_only_widgets.append(connect_button)
        
        serial_upper_buttons_layout.addWidget(self.serial_refresh_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        serial_upper_buttons_layout.addWidget(connect_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        self.port_options = []
        
        serial_ports_widget, serial_ports_layout = create_widget(None, QHBoxLayout)
        serial_layout.addWidget(serial_ports_widget)
        
        self.port_selector_widget = QComboBox()
        self.port_selector_widget.addItems(self.port_options)
        
        serial_ports_layout.addWidget(QLabel("Ports"))
        serial_ports_layout.addWidget(self.port_selector_widget)
        
        baud_rate_options = ["300", "1200", "2400", "4800", "9600", "19200",
                             "38400", "57600", "74880", "115200", "230400",
                             "250000", "500000", "1000000", "2000000"]
        
        serial_baud_rate_widget, serial_baud_rate_layout = create_widget(None, QHBoxLayout)
        serial_layout.addWidget(serial_baud_rate_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.baud_rate_selector_widget = QComboBox()
        self.baud_rate_selector_widget.addItems(baud_rate_options)
        
        serial_baud_rate_layout.addWidget(QLabel("Baud rate"))
        serial_baud_rate_layout.addWidget(self.baud_rate_selector_widget)
        
        self.bluetooth_refesh_button = QPushButton("Refresh")
        self.bluetooth_refesh_button.clicked.connect(lambda: self.refresh("bt", self.bluetooth_refesh_button))
        
        bluetooth_layout.addWidget(self.bluetooth_refesh_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.bluetooth_devices = []
        
        bluetooth_devices_widget, self.bluetooth_devices_layout = create_scrollable_widget(None, QVBoxLayout)
        
        bt_port_edit_widget, bt_port_edit_layout = create_widget(bluetooth_layout, QHBoxLayout)
        
        self.connect_only_widgets.append(bt_port_edit_widget)
        
        for index, (addr, name) in enumerate(self.bluetooth_devices):
            self.add_bt_device(name, addr, index)
        
        self.bt_port_edit = QLineEdit()
        self.bt_port_edit.setValidator(QIntValidator())
        
        bt_port_edit_layout.addWidget(QLabel("Port"))
        bt_port_edit_layout.addWidget(self.bt_port_edit)
        
        bluetooth_layout.addWidget(LabeledField("Bluetooth Low Energy Devices", bluetooth_devices_widget, height_size_policy=QSizePolicy.Policy.Minimum))
        bluetooth_layout.addWidget(bt_port_edit_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        self.main_layout.addWidget(self.main_widget)
        
        self.disconnect_button = QPushButton("Disconnect")
        
        self.main_layout.addWidget(self.disconnect_button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        def bt_state_signal_func(value):
            bluetooth_widget.setDisabled(not value)
            self.bluetooth_refesh_button.setDisabled(False)
        
        self.update_signal.connect(self._update_scan_timeout)
        self.bluetooth_state_signal.connect(bt_state_signal_func)
        
        self.refresh_tracker = {}
    
    def comm_disconnect(self):
        self.data = {}
        self.connected = False
        
        for widget in self.connect_only_widgets:
            widget.setDisabled(False)
        
        self.disconnect_button.setDisabled(True)
    
    def refresh(self, refresh_type: str, refresh_button: QPushButton):
        if self.refresh_tracker.get(refresh_type, [True, None])[0]:
            if not self.refresh_tracker.get(refresh_type, False):
                self.refresh_tracker[refresh_type] = [False, None]
            
            self.refresh_tracker[refresh_type][0] = False
            refresh_button.setDisabled(True)
            
            self.refresh_tracker[refresh_type][1] = Thread(lambda: self.update_scans(refresh_type, refresh_type, refresh_button))
            self.refresh_tracker[refresh_type][1].crashed.connect(self.parent().connection_error_func)
            self.refresh_tracker[refresh_type][1].start()
    
    def exec(self):
        self.serial_refresh_button.click()
        self.bluetooth_refesh_button.click()
        
        initial_exec_val = super().exec()
        
        if not self.connector.connected:
            self.connector.device.port = self.data.get("port", "")
            self.connector.device.addr = self.data.get("addr", None)
            self.connector.device.baud_rate = self.data.get("baud_rate", None)
            
            if self.data.get("connection-type", None) is not None:
                self.connector.set_bluetooth(self.data["connection-type"] == "bt")
                self.connector.set_serial(self.data["connection-type"] == "ser")
                
                self.connector.start_connection()
        
        return initial_exec_val
    
    def _update_scan_timeout(self, data: dict[str, list[tuple[str, str]] | list[str]], args: list):
        if not args:
            refresh_type = None
            refresh_button = None
        else:
            refresh_type, refresh_button = args
        
        if data.get("ser", None) is not None and self.port_options != data["ser"]:
            self.port_options = data["ser"]
            
            for _ in range(self.port_selector_widget.count()):
                self.port_selector_widget.removeItem(0)
            
            if self.port_selector_widget.currentText() in self.port_options:
                self.port_options.insert(0, self.port_options.pop(self.port_options.index(self.port_selector_widget.currentText())))
            
            self.port_selector_widget.addItems(self.port_options)
            if self.port_options:
                self.port_selector_widget.setCurrentIndex(0)
        
        if data.get("bt", None) is not None and dict(self.bluetooth_devices) != dict(data["bt"]):
            for _ in range(len(self.bluetooth_devices)):
                prev_widget = self.bluetooth_devices_layout.itemAt(0).widget()
                self.bluetooth_devices_layout.removeWidget(prev_widget)
                prev_widget.deleteLater()
                
                for widget in self.connect_only_widgets[2:]:
                    widget.deleteLater()
                
                self.connect_only_widgets[2:] = []
            
            self.bluetooth_devices = data["bt"]
            
            for index, (addr, name) in enumerate(self.bluetooth_devices):
                self.add_bt_device(name, addr, index)
        
        if refresh_button is not None:
            refresh_button.setDisabled(False)
        if refresh_type is not None:
            self.refresh_tracker[refresh_type][0] = True
    
    def update_scans(self, send_type: str | None = None, *args):
        data = {}
        
        if send_type == "bt" or send_type is None:
            bt_data = self.connector.find_devices("bt")
            data["bt"] = bt_data
        elif send_type == "ser" or send_type is None:
            ser_data = self.connector.find_devices("ser")
            data["ser"] = ser_data
        
        self.update_signal.emit(data, args)
    
    def add_bt_device(self, name: str, addr: str, index: int):
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.serial_connect_clicked(index))
        self.connect_only_widgets.append(connect_button)
        
        _, bt_device_layout = create_widget(self.bluetooth_devices_layout, QHBoxLayout)
            
        _, info_layout = create_widget(bt_device_layout, QVBoxLayout)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 30px; font-weight: 900;")
        addr_label = QLabel(addr)
        addr_label.setStyleSheet("font-size: 20px; font-weight: 100;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(addr_label)
        
        bt_device_layout.addWidget(connect_button, alignment=Qt.AlignmentFlag.AlignRight)
    
    def serial_connect_clicked(self, a0: int):
        def func():
            self.connect_clicked = True
            self.connected = True
                
            if a0 == -1:
                self.data["connection-type"] = "ser"
                self.data["port"] = self.port_selector_widget.currentText()
                self.data["baud_rate"] = int(self.baud_rate_selector_widget.currentText())
            elif isinstance(a0, int) and a0 >= 0:
                self.data["connection-type"] = "bt"
                self.data["addr"] = self.bluetooth_devices[a0][0]
                try:
                    self.data["port"] = int(self.bt_port_edit.text())
                except ValueError:
                    self.connector.error_func(ValueError(f'Invalid port value: "{self.bt_port_edit.text()}"'), False)
                    return
            
            self.close()
        
        return func
    
    def closeEvent(self, a0):
        if self.connect_clicked:
            self.connect_clicked = False
            
            response = QMessageBox.question(self, "Connection mode", "Are you want to continue with these settings",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if response == QMessageBox.StandardButton.Yes:
                a0.accept()
                
                for widget in self.connect_only_widgets:
                    widget.setDisabled(True)
                self.disconnect_button.setDisabled(False)
            else:
                self.comm_disconnect()
                
                a0.ignore()
                return
            
        return super().closeEvent(a0)



