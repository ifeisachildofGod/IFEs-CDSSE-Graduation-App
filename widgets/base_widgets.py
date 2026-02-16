
from imports import *
from communication import *
from functions_and_uncategorized import *

from widgets.extra_widgets import *


class BaseListWidget(QWidget):
    def __init__(self, scroll_area: QScrollArea) -> None:
        super().__init__()
        
        self.widgets: list[BaseAttendanceEntryWidget] = []
        self.scroll_area = scroll_area
        
        self.container = QWidget(self)          # ✅ keep reference + parent
        self.main_layout = QVBoxLayout(self.container)
        self.container.setLayout(self.main_layout)
        
        self.main_layout.addStretch()
        
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.container)  # ✅ add to visible hierarchy
        self.setLayout(self._layout)
    
    # Category name is here to avoid edge cases
    def addWidget(self, widget: "BaseAttendanceEntryWidget", category_name: str | None = None, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch, alignment)
        else:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch)
        
        widget.show()
        widget.adjustSize()
        
        self.widgets.append(widget)
    
    def get_widgets(self):
        return self.widgets

class BaseScrollListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        self.widgets: list[BaseAttendanceEntryWidget] = []
        
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        widget = QWidget()
        self.scroll_widget.setWidget(widget)
        self.main_layout = QVBoxLayout(widget)
        
        self.main_layout.addStretch()
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._layout.addWidget(self.scroll_widget)
    
    def _scroll_to(self, widget: QWidget):
        widget.ensurePolished()
        self.scroll_widget.ensureWidgetVisible(widget)
    
    def scroll_to(self, widget: QWidget, msec: Optional[int] = None):
        QTimer.singleShot(
            msec or 0,
            lambda: self._scroll_to(widget)
        )
    
    def addWidget(self, widget: "BaseAttendanceEntryWidget", stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch, alignment)
        else:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch)
        
        self.widgets.append(widget)
    
    def get_widgets(self):
        return self.widgets

class BaseFilterCategoriesWidget(BaseListWidget):
    def __init__(self, scroll_area: QScrollArea):
        super().__init__(scroll_area)
        
        self.category_widgets = {}
        self.category_widgets_tracker = []
    
    def addWidget(self, widget: "BaseAttendanceEntryWidget", category_name: str | tuple[str, ...] | int, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if isinstance(category_name, (str, int)):
            category_name = str(category_name)
            
            if category_name not in self.category_widgets:
                cat_widg = QWidget()
                cat_layout = QVBoxLayout()
                cat_widg.setLayout(cat_layout)
                
                self.category_widgets[category_name] = DropdownLabeledField(category_name, cat_widg)
                
                super().addWidget(self.category_widgets[category_name])
            
            if alignment is not None:
                self.category_widgets[category_name].addWidget(widget, stretch, alignment)
            else:
                self.category_widgets[category_name].addWidget(widget, stretch)
            
            self.category_widgets_tracker.append([self.category_widgets[category_name], widget])
        else:
            parent = super()
            widgs = self.category_widgets
            
            self.category_widgets_tracker.append([])
            
            for i, name in enumerate(category_name):
                name = str(name)
                
                if name not in widgs:
                    cat_widg = QWidget()
                    cat_layout = QVBoxLayout()
                    cat_widg.setLayout(cat_layout)
                    
                    widgs[name] = [DropdownLabeledField(name, cat_widg), {}]
                    
                    parent.addWidget(widgs[name][0], alignment=alignment)
                
                self.category_widgets_tracker[-1].append(widgs[name][0])
                
                if i != len(category_name) - 1:
                    parent = widgs[name][0]
                    widgs = widgs[name][1]
                else:
                    if alignment is not None:
                        widgs[name][0].addWidget(widget, stretch, alignment)
                    else:
                        widgs[name][0].addWidget(widget, stretch)
            
            self.category_widgets_tracker[-1].append(widget)
    
    def get_widgets(self):
        return self.category_widgets_tracker



class BaseDataDisplayWidget(BaseScrollListWidget):
    def __init__(self, data: AppData):
        super().__init__()
        
        self.scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.data = data
        
        self.widgets = self._get_filter_widgets()
        
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
    
    def _get_filter_widgets(self):
        pass
    
    @staticmethod
    def is_entry_countable(entry: AttendanceEntry, valid_days: list[str], timeline_dates: list[tuple[Period, Period]]):
        time_line_index = next((i for i, t_d in enumerate(timeline_dates) if t_d[0].in_minutes() <= entry.period.in_minutes() <= t_d[1].in_minutes()), None)
        
        if (
            entry.is_check_in and
            entry.period.day in valid_days and
            time_line_index is not None
            ):
            return time_line_index
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            if isinstance(staff_widget, tuple) and index == i:
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
            else:
                staff_widget.setVisible(index == i)




class BaseStaffListEntryWidget(QWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, staff: Staff, comm_system: BaseCommSystem, card_scanner_widget: QWidget, staff_data_widget: QWidget):
        super().__init__()
        
        self.data = data
        self.staff = staff
        self.comm_system = comm_system
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.container.setLayout(self.main_layout)
        
        self.container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        layout.addWidget(self.container)
        
        self.staff_data_widget = staff_data_widget
        self.card_scanner_widget = card_scanner_widget
        
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
        
        self.options_menu = OptionsMenu()
        self.options_menu.add_options({"Set IUD": self.set_iud, "View Data": self.view_data})
        self.options_menu.setProperty("class", "option-menu")
        
        main_info_layout.addWidget(self.options_button, alignment=Qt.AlignmentFlag.AlignTop)
        
        _, self.sub_info_layout = create_widget(self.main_layout, QHBoxLayout)
        
        self.iud_label = QLabel(self.staff.IUD if self.staff.IUD is not None else "No IUD set")
        self.iud_label.setStyleSheet("font-weight: bold;")
        
        self.sub_info_layout.addWidget(LabeledField("IUD", self.iud_label), alignment=Qt.AlignmentFlag.AlignLeft)
    
    def set_iud(self):
        if not self.comm_system.connected:
            QMessageBox.warning(self.parentWidget(), "Not Connected", "No device connected")
        else:
            self.card_scanner_widget.set_self(self.staff, self.iud_label)
            
            self.parent_widget.stack.setCurrentWidget(self.card_scanner_widget)
            self.comm_system.send_message("SCANNING")
    
    def view_data(self):
        self.comm_system.send_message((" " * int(8 - (len(self.staff.name.abrev) / 2))) + f"{self.staff.name.abrev}'s_Performance Data")
        
        self.staff_data_widget.set_self(self.staff)
        
        self.parent_widget.stack.setCurrentWidget(self.staff_data_widget)
    
    def toogle_options(self):
        if self.options_menu.isVisible():
            self.options_menu.hide()
        else:
            # Position below the options button
            button_pos = self.options_button.mapToGlobal(QPoint(-65, self.options_button.height() - 5))
            self.options_menu.move(button_pos)
            self.options_menu.show()

class BaseAttendanceEntryWidget(QWidget):
    def __init__(self, name: str, data: AttendanceEntry, layout_type: type[QHBoxLayout] | type[QVBoxLayout] = QHBoxLayout):
        super().__init__()
        
        self.data = data
        self.staff = self.data.staff
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.container = QWidget()
        
        self.main_layout = layout_type()
        self.container.setLayout(self.main_layout)
        
        self.labeled_container = LabeledField(f"{name} - Check {"IN" if data.is_check_in else "OUT"}", self.container, height_policy=QSizePolicy.Policy.Maximum)
        
        layout.addWidget(self.labeled_container)




