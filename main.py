
from widgets.section_widgets import *

class Window(QMainWindow):
    comm_signal = pySignal(dict)
    connection_changed = pySignal(bool)
    saved_state_changed = pySignal(bool)
    
    def __init__(self, file_path: str | None = None) -> None:
        super().__init__()
        self.title = "CDSSE School Manager"
        
        self.file_path = file_path
        
        self.target_connector = BaseCommSystem(CommDevice(self.comm_signal, self.connection_changed, "", None, None), self.connection_error_func)
        self.connection_set_up_screen = SetupScreen(self, self.target_connector)
        self.file_manager = FileManager(self, "CDSSE Management Files (*.cdmanage)")
        self.file_manager.set_callbacks(self.save_callback, self.open_callback, self.load_callback)
        
        self.create_menu_bar()
        
        # Create main container
        container = QWidget()
        main_layout = QHBoxLayout()
        
        container.setLayout(main_layout)
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        data_class_mapping = {"CharacterName": CharacterName, "Class": Class, "Subject": Subject, "Department": Department, "Teacher": Teacher, "Prefect": Prefect, "AttendanceEntry": AttendanceEntry, "Time": Time}
        
        with open("src/default-data/default-app-data.json") as file:
            app_data = process_from_data(json.load(file), data_class_mapping)
        with open("src/default-data/default-staff.json") as file:
            app_data.update(process_from_data(json.load(file), data_class_mapping))
            app_data["attendance_data"] = []
        
        self.data = AppData(**app_data) if not self.file_path else self.file_manager.get_file_data()
        
        # Create stacked widget for content
        staff_widget = TabViewWidget("vertical")
        staff_widget.add("Attendance", AttendanceWidget(staff_widget, self.data, "Attendance Chart", "Punctuality Chart", self.target_connector, self.saved_state_changed))
        staff_widget.add("Teachers", TeacherStaffListWidget(staff_widget, self.data, "Teachers", self.target_connector, 5, 6))
        staff_widget.add("Prefects", PrefectStaffListWidget(staff_widget, self.data, "Prefects", self.target_connector, 5, 6))
        staff_widget.add("Attendance Chart", AttendanceBarWidget(self.data))
        staff_widget.add("Punctuality Graph", AttendanceBarWidget(self.data))
        staff_widget.stack.addWidget(CardScanScreenWidget(self.target_connector, staff_widget, self.saved_state_changed))
        staff_widget.stack.addWidget(StaffDataWidget(self.data, staff_widget))
        
        security_widget = UltrasonicSonarWidget(self, self.data, Sensor(SensorMeta("Ultrasonic", "Floating bird", "8.9.1", "Arduino inc"), "src/sensor-images/sonar.png", self.target_connector), self.saved_state_changed)
        
        gas_widget = SensorWidget(self, self.data, Sensor(SensorMeta("Gas", "Flying fish", "13.1.0.1", "Arduino inc"), "src/sensor-images/gas.png", self.target_connector), self.saved_state_changed)
        flame_widget = SensorWidget(self, self.data, Sensor(SensorMeta("Fire", "Fire free", "10.0.0.1", "Arduino inc"), "src/sensor-images/fire.png", self.target_connector), self.saved_state_changed)
        
        safety_widget, safety_layout = create_scrollable_widget(None, QVBoxLayout)
        
        safety_layout.addWidget(gas_widget)
        safety_layout.addWidget(flame_widget)
        
        main_screen_widget = TabViewWidget()
        main_screen_widget.add("Staff", staff_widget, self.comm_send_screen_changed("STAFF"))
        main_screen_widget.add("Security", security_widget, self.comm_send_screen_changed("SECURITY"))
        main_screen_widget.add("Safety", safety_widget, self.comm_send_screen_changed("SAFETY"))
        
        def conn_changed(connected):
            if not connected:
                self.connection_set_up_screen.comm_disconnect()
            else:
                main_screen_widget.tab_src_changed_func_mapping.get(main_screen_widget.current_tab, lambda _: ())(list(main_screen_widget.tab_src_changed_func_mapping.keys()).index(main_screen_widget.current_tab))
        
        self.connection_set_up_screen.disconnect_button.clicked.connect(self.disconnect_connection)
        self.target_connector.device.connection_changed.connect(conn_changed)
        self.saved_state_changed.connect(self.saved_state_changed_func)
        self.target_connector.device.connection_changed.emit(False)
        
        main_layout.addWidget(main_screen_widget)
        
        self.setCentralWidget(container)
        
        self.saved_state_changed.emit(True)
    
    def saved_state_changed_func(self, value: bool):
        suffix = f" - {self.file_path}" + ("" if value else " *Unsaved")
        self.data.variables["saved"] = value
        
        self.setWindowTitle(self.title + (suffix if self.file_path is not None else ""))
    
    def disconnect_connection(self):
        self.target_connector.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
    
    def comm_send_screen_changed(self, message: str):
        def scr_changed(_):
            if self.target_connector.connected:
                self.target_connector.send_message(message)
        
        return scr_changed
    
    def activate_connection_screen(self):
        self.connection_set_up_screen.exec()
    
    def connection_error_func(self, e: Exception, conn_error: bool = True):
        self.target_connector.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
        
        if conn_error:
            response = QMessageBox.warning(self, type(e).__name__, str(e) + "\n\nTry again?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            response = QMessageBox.warning(self, type(e).__name__, str(e))
        
        if isinstance(e, OSError):
            self.connection_set_up_screen.bluetooth_state_signal.emit(False)
        
        if not self.connection_set_up_screen.isActiveWindow() and response == QMessageBox.StandardButton.Yes:
            self.activate_connection_screen()
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        # Connection Menu
        connection_menu = menubar.addMenu("Connection")
        
        # Add all actions
        file_menu.addAction("New", "Ctrl+N", self.file_manager.new)
        file_menu.addAction("Open", "Ctrl+O", self.file_manager.open)
        file_menu.addAction("Save", "Ctrl+S", self.file_manager.save)
        file_menu.addAction("Save As", "Ctrl+Shift+S", self.file_manager.save_as)
        file_menu.addAction("Close", self.close)
        
        connection_menu.addAction("Set Connection", "Ctrl+F", self.activate_connection_screen)
    
    def save_callback(self, file_path: str):
        self.file_path = file_path
        
        self.saved_state_changed.emit(True)
        
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)
    
    def open_callback(self, file_path: str | None = None, content: str | None = None):
        new_window = Window(file_path, content)
        new_window.show()
        
        if not hasattr(self, '_windows'):
            self._windows = []
        self._windows.append(new_window)
    
    def load_callback(self, file_path: str):
        with open(self.file_path, "rb") as f:
            return pickle.load(f)
    
    def closeEvent(self, a0):
        if not self.data.variables["saved"]:
            reply = QMessageBox.question(self, "Save", "Save before quitting?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.file_manager.save()
            elif reply == QMessageBox.StandardButton.Cancel:
                a0.ignore()
                return
        
        a0.accept()
        
        return super().closeEvent(a0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # app.setWindowIcon(QIcon("src/icons-and-images/logo.png"))
    
    THEME_MANAGER.apply_theme(app)
    
    file_path = None
    if len(app.arguments()) > 1:
        file_path = app.arguments()[1]
    
    window = Window(file_path)
    window.showMaximized()
    
    sys.exit(app.exec())
    

