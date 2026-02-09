from imports import *

def check_states(t: Time, cin: Time, cout: Time, data: AppData, focus_type: Literal["Prefect", "Teacher"]):
    cin_interval = data.prefect_cin_border_interval_minutes if focus_type == "Prefect" else data.teacher_cin_border_interval_minutes
    cout_interval = data.prefect_cout_border_interval_minutes if focus_type == "Prefect" else data.teacher_cout_border_interval_minutes
    
    is_cin = cin.in_minutes() - cin_interval <= t.in_minutes() <= cin.in_minutes() + cin_interval
    is_cout = cout.in_minutes() - cout_interval <= t.in_minutes() <= cout.in_minutes() + cout_interval
    
    return is_cin, is_cout

def process_from_data(data, data_class_mapping: dict[str, type] | None = None, class_mapping: dict[str, type] | None = None):
    class_mapping = class_mapping if class_mapping is not None else {}
    data_class_mapping = data_class_mapping if data_class_mapping is not None else {}
    
    if isinstance(data, dict):
        return_value = {key: process_from_data(value, data_class_mapping, class_mapping) for key, value in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return_value = data.__class__([process_from_data(value, data_class_mapping, class_mapping) for value in data])
        
        if len(data) == 2 and isinstance(data[0], str):
            if data[0].startswith("$$") and data[0].endswith("$$"):
                return_value = data_class_mapping[data[0].removeprefix("$$").removesuffix("$$")](**process_from_data(data[1], data_class_mapping, class_mapping))
            elif data[0].startswith("@@") and data[0].endswith("@@"):
                return_value = class_mapping[data[0].removeprefix("@@").removesuffix("@@")](**process_from_data(data[1], data_class_mapping, class_mapping))
    else:
        return_value = data
    
    return return_value


def create_widget(parent_layout: QLayout | None, layout_type: type[QHBoxLayout] | type[QVBoxLayout] | type[QGridLayout]):
    widget = QWidget()
    layout = layout_type()
    widget.setLayout(layout)
    
    if parent_layout is not None:
        parent_layout.addWidget(widget)
    
    return widget, layout

def create_scrollable_widget(parent_layout: QLayout | None, layout_type: type[QHBoxLayout] | type[QVBoxLayout]):
    scroll_widget = QScrollArea()
    scroll_widget.setWidgetResizable(True)
    
    widget = QWidget()
    scroll_widget.setWidget(widget)
    layout = layout_type(widget)
    
    if parent_layout is not None:
        parent_layout.addWidget(scroll_widget)
    
    return scroll_widget, layout

def clear_layout(layout: QLayout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()
        layout_item = item.layout()

        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()

        elif layout_item is not None:
            clear_layout(layout_item)


class Thread(QThread):
    crashed = pySignal(Exception)
    
    def __init__(self, func: Callable):
        super().__init__()
        self.func = func
    
    def run(self):
        try:
            self.func()
        except Exception as e:
            self.crashed.emit(e)
            self.exit(-1)


class FileManager:
    def __init__(self, parent: QWidget, current_path: Optional[str] = None, file_filter="Text Files (*.txt);;All Files (*)"):
        self.parent = parent
        self.file_filter = file_filter
        self.current_path = current_path

        # Hooks: user-defined callbacks for file read/write
        self.save_callback: Optional[Callable[[str | None], str]] = None
        self.open_callback: Optional[Callable[[], None] | Callable[[str, Any], None]] = None
        self.load_callback: Optional[Callable[[str], Any]] = None

    def set_callbacks(self, save: Callable[[str | None], None], open_: Callable[[], None] | Callable[[str, Any], None], load: Callable[[], Any]):
        self.save_callback = save
        self.open_callback = open_
        self.load_callback = load
    
    def get_file_data(self):
        assert self.current_path
        
        return self.load_callback(self.current_path)
    
    def new(self):
        self.current_path = None
        
        if self.open_callback:
            self.open_callback()
    
    def open(self):
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Open File", "", self.file_filter)
        if file_path:
            try:
                if self.open_callback:
                    self.open_callback(file_path)
            except Exception as e:
                QMessageBox.critical(self.parent, "Open Error", str(e))

    def save(self):
        if self.current_path:
            try:
                if self.save_callback:
                    self.save_callback(self.current_path)
            except Exception as e:
                QMessageBox.critical(self.parent, "Save Error", str(e))
        else:
            self.save_as()

    def save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Save File As", "", self.file_filter)
        
        if file_path:
            try:
                if self.save_callback:
                    self.current_path = file_path
                    self.save_callback(self.current_path)
            except Exception as e:
                QMessageBox.critical(self.parent, "Save As Error", str(e))


