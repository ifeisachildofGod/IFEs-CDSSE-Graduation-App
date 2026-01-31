
from widgets.extra_widgets import *
from data.time_data_objects import positionify

class BaseStaffListWidget(QWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, staff: Staff, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__()
        
        self.data = data
        self.staff = staff
        self.comm_system = comm_system
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        layout.addWidget(self.container)
        
        self.staff_data_index = staff_data_index
        self.card_scanner_index = card_scanner_index
        
        self.parent_widget = parent_widget
        
        _, main_info_layout = create_widget(self.main_layout, QHBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=200)
        
        main_info_layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignLeft)
        main_info_layout.addStretch()
        
        name_label = QLabel(self.staff.name.full_name())
        
        name_label.setStyleSheet("font-size: 50px")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_info_layout.addWidget(name_label, Qt.AlignmentFlag.AlignRight)
        
        self.options_button = QPushButton("☰")
        self.options_button.setProperty("class", "options-button")
        self.options_button.setFixedSize(40, 40)
        self.options_button.clicked.connect(self.toogle_options)
        
        self.options_menu = OptionsMenu({"Set IUD": self.set_iud, "View Punctuality Data": self.view_punctuality_data})
        self.options_menu.setProperty("class", "option-menu")
        
        main_info_layout.addWidget(self.options_button, alignment=Qt.AlignmentFlag.AlignTop)
        
        _, self.sub_info_layout = create_widget(self.main_layout, QHBoxLayout)
        
        self.iud_label = QLabel(self.staff.IUD if self.staff.IUD is not None else "No set IUD")
        self.iud_label.setStyleSheet("font-weight: bold;")
        
        self.sub_info_layout.addWidget(LabeledField("IUD", self.iud_label), alignment=Qt.AlignmentFlag.AlignLeft)
    
    def set_iud(self):
        if not self.comm_system.connected:
            QMessageBox.warning(self.parentWidget(), "Not Connected", "No device connected")
        else:
            card_scanner_widget: CardScanScreenWidget = self.parent_widget.stack.widget(self.card_scanner_index)
            card_scanner_widget.set_self(self.staff, self.iud_label)
            
            self.parent_widget.stack.setCurrentIndex(self.card_scanner_index)
            self.comm_system.send_message("SCANNING")
    
    def view_punctuality_data(self):
        self.comm_system.send_message(f"staffPreformance:{self.staff.name.abrev}")
        staff_data_widget: StaffDataWidget = self.parent_widget.stack.widget(self.staff_data_index)
        staff_data_widget.set_self(self.staff)
        
        self.parent_widget.set_tab(self.staff_data_index)
    
    def toogle_options(self):
        if self.options_menu.isVisible():
            self.options_menu.hide()
        else:
            # Position below the options button
            button_pos = self.options_button.mapToGlobal(QPoint(-130, self.options_button.height()))
            self.options_menu.move(button_pos)
            self.options_menu.show()

class BaseAttendanceWidget(QWidget):
    def __init__(self, name: str, data: AttendanceEntry, layout_type: type[QHBoxLayout] | type[QVBoxLayout] = QHBoxLayout):
        super().__init__()
        
        self.data = data
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        
        self.main_layout = layout_type()
        self.container.setLayout(self.main_layout)
        
        self.labeled_container = LabeledField(name, self.container, height_size_policy=QSizePolicy.Policy.Maximum, width_size_policy=QSizePolicy.Policy.Maximum)
        
        layout.addWidget(self.labeled_container)
    
class AttendanceTeacherWidget(BaseAttendanceWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Teacher", data)
        
        self.labeled_container.setProperty("class", "AttendanceTeacherWidget")
        
        self.teacher = self.data.staff
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.teacher.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_size_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.min < 10 else "") + str(self.data.period.time.min))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.sec < 10 else "") + str(self.data.period.time.sec))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_size_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = CharacterNameWidget(self.teacher.name)
        layout_2.addWidget(name_widget)
        
        _, layout_2_2 = create_widget(layout_2, QVBoxLayout)
        
        widget_2_2_2, layout_2_2_2 = create_scrollable_widget(None, QVBoxLayout)
        
        layout_2_2.addWidget(LabeledField("Subjects", widget_2_2_2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        periods_data: dict[tuple[str, str], dict[tuple[str, str], list[int]]] = {}
        
        for subject in self.teacher.subjects:
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

class AttendancePrefectWidget(BaseAttendanceWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Prefect", data)
        
        self.labeled_container.setProperty("class", "AttendancePrefectWidget")
        
        self.prefect = self.data.staff
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.prefect.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_size_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.min < 10 else "") + str(self.data.period.time.min))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.sec < 10 else "") + str(self.data.period.time.sec))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_size_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = CharacterNameWidget(self.prefect.name)
        layout_2.addWidget(name_widget)
        
        widget_2_2, layout_2_2 = create_widget(None, QHBoxLayout)
        
        layout_2_2.addWidget(LabeledField("Class", QLabel(self.prefect.cls.name), height_size_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_3_1, layout_1_3_1 = create_scrollable_widget(None, QVBoxLayout)
        
        for index, duty in enumerate(self.prefect.duties.get(self.data.period.day, [])):
            layout_1_3_1.addWidget(QLabel(f"{index + 1}. {duty}"))
        
        layout_2_2.addWidget(LabeledField("Duties", widget_1_3_1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        layout_2.addWidget(widget_2_2)


class StaffListPrefectEntryWidget(BaseStaffListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, prefect: Prefect, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, prefect, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListPrefectEntryWidget")
        
        self.sub_info_layout.addWidget(LabeledField("Post", QLabel(self.staff.post_name)))
        self.sub_info_layout.addWidget(LabeledField("Class", QLabel(self.staff.cls.name)))

class StaffListTeacherEntryWidget(BaseStaffListWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, teacher: Teacher, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, teacher, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListTeacherEntryWidget")
        
        self.sub_info_layout.addWidget(LabeledField("Dept", QLabel(self.staff.department.name), QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))


