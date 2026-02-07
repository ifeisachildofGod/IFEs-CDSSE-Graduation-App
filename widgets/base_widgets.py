
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
        
        self.scroll_area.verticalScrollBar().setValue(widget.y())
    
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
                
                self.category_widgets[category_name] = DropdownLabeledField(category_name, cat_widg, True)
                
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
                    
                    widgs[name] = [DropdownLabeledField(name, cat_widg, True), {}]
                    
                    parent.addWidget(widgs[name][0])
                
                if i != len(category_name) - 1:
                    parent = widgs[name][0]
                    widgs = widgs[name][1]
                    
                    self.category_widgets_tracker[-1].append(parent)
                else:
                    if alignment is not None:
                        widgs[name][0].addWidget(widget, stretch, alignment)
                    else:
                        widgs[name][0].addWidget(widget, stretch)
                    
                    self.category_widgets_tracker[-1].append(widget)
    
    def get_widgets(self):
        return self.category_widgets_tracker




class BaseStaffListEntryWidget(QWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, staff: Staff, comm_system: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
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
            card_scanner_widget = self.parent_widget.stack.widget(self.card_scanner_index)
            card_scanner_widget.set_self(self.staff, self.iud_label)
            
            self.parent_widget.stack.setCurrentIndex(self.card_scanner_index)
            self.comm_system.send_message("SCANNING")
    
    def view_data(self):
        self.comm_system.send_message(f"LCD:{self.staff.name.abrev}'s_-_Performance Data")
        
        staff_data_widget = self.parent_widget.stack.widget(self.staff_data_index)
        staff_data_widget.set_self(self.staff)
        
        self.parent_widget.set_tab(self.staff_data_index)
    
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
        
        self.labeled_container = LabeledField(name, self.container, height_policy=QSizePolicy.Policy.Maximum)
        
        layout.addWidget(self.labeled_container)




