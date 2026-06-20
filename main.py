
from widgets.dialog_widgets import *
from widgets.staff.option_widgets import *
from widgets.staff.list_widgets import *

from theme import THEME_MANAGER

import csv
from io import StringIO
from typing import List

class Window(QMainWindow):
    comm_signal = pySignal(dict)
    connection_changed = pySignal(bool)
    saved_state_changed = pySignal(bool)
    
    def __init__(self, arguments: list[str]) -> None:
        super().__init__()
        self.title = "Command Day Secondary School Enugu Attendance Manager"
        
        self.flag_mapping = {
            "-d": self._default_flag,
            "-default": self._default_flag,
            
            "--arg--": self._arg_flags
        }
        
        self.file_path = None
        self._default_file_path = None
        self.arguments = arguments
        
        for i, arg in enumerate(self.arguments):
            arg = arg.strip()
            
            if "=" in arg:
                n, v = arg.split("=")
                
                self.flag_mapping[n](v)
            elif arg.startswith("--") and not arg.endswith("--"):
                self.flag_mapping[arg[2:]]()
            elif i:
                self.flag_mapping["--arg--"](i, arg)
        
        self.target_connector = BaseCommSystem(CommDevice(self.comm_signal, self.connection_changed, "", None, None), self.connection_error_func)
        self.connection_set_up_screen = CommSetupDialog(self, self.target_connector)
        # self.management_set_up_screen = ManageSetupDialog(self)
        self.file_manager = FileManager(self, self.file_path, "CDSSE Attendance Files (*.cdat)")
        self.file_manager.set_callbacks(self.save_callback, self.open_callback, self.load_callback, self.csv_export_callback)
        
        self.create_menu_bar()
        
        # Create main container
        container = QWidget()
        main_layout = QHBoxLayout()
        
        container.setLayout(main_layout)
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        data_class_mapping = {
            "CharacterName": CharacterName,
            "Class": Class,
            "Subject": Subject,
            "Department": Department,
            "Teacher": Teacher,
            "Prefect": Prefect,
            "Period": Period,
            "AttendanceEntry": AttendanceEntry,
            "Time": Time
        }
        
        if not self.file_path:
            with open(self._default_file_path or "src/default-data.json") as file:
                self.data = AppData(**process_from_data(json.load(file), data_class_mapping))
        else:
            self.file_manager.current_path = self.file_path
            self.data = self.file_manager.get_file_data()
        
        # Create stacked widget for content
        main_widget = TabViewWidget("horizontal")
        
        card_scan_widget = CardScanScreenWidget(self.data, self.target_connector, main_widget, self.saved_state_changed)
        staff_data_widget = StaffDataWidget(self.data, main_widget)
        
        attendance_chart_widget = AttendanceBarWidget(self.data, staff_data_widget)
        punctuality_graph_widget = PunctualityGraphWidget(self.data, staff_data_widget)
        
        main_widget.add("Attendance", AttendanceWidget(main_widget, self.data, attendance_chart_widget, punctuality_graph_widget, self.target_connector, self.saved_state_changed, self.file_manager, card_scan_widget))
        main_widget.add("Staff", StaffListWidget(main_widget, self.data, self.target_connector, card_scan_widget, staff_data_widget))
        main_widget.add("Attendance Chart", attendance_chart_widget)
        main_widget.add("Punctuality Graph", punctuality_graph_widget)
        main_widget.stack.addWidget(card_scan_widget)
        main_widget.stack.addWidget(staff_data_widget)
        
        def conn_changed(connected):
            if not connected:
                self.connection_set_up_screen.comm_disconnect()
        
        self.connection_set_up_screen.disconnect_button.clicked.connect(self.disconnect_connection)
        self.target_connector.device.connection_changed.connect(conn_changed)
        self.saved_state_changed.connect(self.saved_state_changed_func)
        self.target_connector.device.connection_changed.emit(False)
        
        main_layout.addWidget(main_widget)
        
        self.setCentralWidget(container)
        
        self.saved_state_changed.emit(True)
    
    def _arg_flags(self, index: int, arg: str):
        assert index == len(self.arguments) - 1
        
        self.file_path = arg
    
    def _default_flag(self, arg: str):
        self._default_file_path = arg
    
    def saved_state_changed_func(self, value: bool):
        suffix = f" - {self.file_path}" + ("" if value else " *Unsaved")
        self.data.variables["saved"] = value
        
        self.setWindowTitle(self.title + (suffix if self.file_path is not None else ""))
    
    def disconnect_connection(self):
        self.target_connector.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
    
    # def comm_send_screen_changed(self, message: str):
    #     def scr_changed(_):
    #         if self.target_connector.connected:
    #             pass
    #             # self.target_connector.send_message(message)
        
    #     return scr_changed
    
    def activate_connection_screen(self):
        self.connection_set_up_screen.exec()
    
    # def activate_management_screen(self):
    #     self.management_set_up_screen.exec()
    
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
        connection_menu = menubar.addMenu("Set")
        
        # Palette Menu
        palette_menu = menubar.addMenu("Palette")
        
        # Add all actions
        file_menu.addAction("New", "Ctrl+N", self.file_manager.new)
        file_menu.addAction("Open", "Ctrl+O", self.file_manager.open)
        file_menu.addAction("Save", "Ctrl+S", self.file_manager.save)
        file_menu.addAction("Save As", "Ctrl+Shift+S", self.file_manager.save_as)
        file_menu.addSeparator()
        file_menu.addAction("Export to CSV", "Ctrl+Shift+E", self.file_manager.csv_export)
        file_menu.addSeparator()
        file_menu.addAction("Close", self.close)
        
        m_type_group = QActionGroup(self)
        m_type_group.setExclusive(True)
        
        connection_menu.addAction("Device Connection", "Ctrl+D", self.activate_connection_screen)
        connection_menu.addSeparator()
        
        c_sa_action = QAction("School Attendance", self)
        c_tr_action = QAction("Teacher Registry", self)
        
        c_sa_action.setCheckable(True)
        c_tr_action.setCheckable(True)
        
        # c_sa_action.triggerd.connect(print)     TBD
        # c_tr_action.triggerd.connect(print)     TBD
        
        m_type_group.addAction(c_sa_action)
        m_type_group.addAction(c_tr_action)
        
        connection_menu.addAction(c_sa_action)
        connection_menu.addAction(c_tr_action)
        
        c_sa_action.setChecked(True)
        
        
        palette_action_group = QActionGroup(self)
        palette_action_group.setExclusive(True)
        
        palette_dict: dict[str, QMenu] = {}
        for name in THEME_MANAGER.themes:
            main, accent = name.split("-")
            
            if main not in palette_dict:
                palette_dict[main] = palette_menu.addMenu(main.title())
            
            accent_action = QAction(accent.title(), self)
            accent_action.setCheckable(True)
            accent_action.triggered.connect(self._create_palette_action_func(main, accent))
            
            palette_action_group.addAction(accent_action)
            palette_dict[main].addAction(accent_action)
        
        first_action = list(palette_dict.values())[0].actions()[0]
        
        first_action.setChecked(True)
        first_action.triggered.emit()
        
        c_sa_action.setDisabled(True)
        c_tr_action.setDisabled(True)
    
    def _create_palette_action_func(self, main_color: str, accent_color: str):
        def func():
            THEME_MANAGER.apply_theme(f"{main_color}-{accent_color}")
        
        return func
    
    def csv_export_callback(self, file_path: str):
        output = StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Name",
            "Role",
            "Day",
            "Date",
            "Month",
            "Year",
            "Time",
            "Check Type",
            "Has Duties"
        ])

        for entry in self.data.attendance_data:
            writer.writerow([
                entry.staff.name.full(),
                "Prefect" if isinstance(entry.staff, Prefect) else "Teacher",
                entry.period.day,
                entry.period.date,
                entry.period.month,
                entry.period.year,
                str(entry.period.time),
                "Check In" if entry.is_check_in else "Check Out",
                ("Yes" if entry.period.day in entry.staff.duties else "No") if isinstance(entry.staff, Prefect) else next(("Yes" for s in entry.staff.subjects if next((True for d, _ in s.periods if d == entry.period.day), False)), "No")
            ])
        
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            file.write(output.getvalue().strip())
    
    def save_callback(self, file_path: str):
        self.file_path = file_path
        
        self.saved_state_changed.emit(True)
        
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)
    
    def open_callback(self, file_path: str | None = None):
        new_window = Window(["", file_path])
        new_window.show()
        
        if not hasattr(self, '_windows'):
            self._windows = []
        self._windows.append(new_window)
    
    def load_callback(self, file_path):
        with open(file_path, "rb") as f:
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
    
    app.setWindowIcon(QIcon("src/images/logo.ico"))
    
    THEME_MANAGER.set_application(app)
    
    window = Window(app.arguments())
    window.showMaximized()
    
    sys.exit(app.exec())
    

