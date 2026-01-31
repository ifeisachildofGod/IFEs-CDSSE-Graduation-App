
from others import *
from imports import *
from communication import *

from theme import THEME_MANAGER

class TabViewWidget(QWidget):
    def __init__(self, bar_orientation: Literal["vertical", "horizontal"] = "horizontal"):
        super().__init__()
        self.bar_orientation = bar_orientation
        
        assert self.bar_orientation in ("vertical", "horizontal"), f"Invalid orientation: {self.bar_orientation}"
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        tab_layout_type = QHBoxLayout if self.bar_orientation == "horizontal" else QVBoxLayout
        main_layout_type = QHBoxLayout if self.bar_orientation == "vertical" else QVBoxLayout
        
        container = QWidget()
        layout = main_layout_type()
        container.setLayout(layout)
        
        self.current_tab = None
        self.tab_src_changed_func_mapping = {}
        
        self.tab_buttons: list[QPushButton] = []
        
        tab_widget = QWidget()
        tab_widget.setContentsMargins(0, 0, 0, 0)
        
        self.tab_layout = tab_layout_type()
        tab_widget.setLayout(self.tab_layout)
        
        self.stack = QStackedWidget()
        
        if self.bar_orientation == "vertical":
            self.tab_layout.addStretch()
        
        self.setContentsMargins(0, 0, 0, 0)
        tab_widget.setContentsMargins(0, 0, 0, 0)
        self.stack.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(tab_widget)
        layout.addWidget(self.stack)
        
        main_layout.addWidget(container)
    
    def add(self, tab_name: str, widget: QWidget, func: Callable[[int, ], None] = None):
        tab_button = QPushButton(tab_name)
        
        self.tab_buttons.append(tab_button)
        
        tab_button.setCheckable(True)
        tab_button.clicked.connect(self._make_tab_clicked_func(len(self.tab_buttons) - 1, func))
        tab_button.setProperty("class", "HorizontalTab" if self.bar_orientation == "horizontal" else "VerticalTab")
        tab_button.setContentsMargins(0, 0, 0, 0)
        
        self.tab_layout.insertWidget(len(self.tab_buttons) - 1, tab_button)
        self.stack.insertWidget(len(self.tab_buttons), widget)
        widget.setContentsMargins(0, 0, 0, 0)
        
        self.tab_buttons[0].click()
    
    def get(self, tab_name: str, default: Any = ...):
        tab_widget = (self.stack.children() + [default])[next((i for i, b in enumerate(self.tab_buttons) if b.text() == tab_name), len(self.stack.children()))]
        
        if type(tab_widget) == type(Ellipsis):
            raise KeyError(f'There is no tab named: "{tab_name}"')
        return tab_widget
    
    def index(self, widget: QWidget):
        return next(i for i, w in enumerate(self.stack.children()) if w == widget)
    
    def set_tab(self, tab: int | str):
        if isinstance(tab, int) and tab >= len(self.tab_buttons):
            self.stack.setCurrentIndex(tab)
        else:
            self.tab_buttons[self.index(self.get(tab)) if isinstance(tab, str) else tab].click()
    
    def _make_tab_clicked_func(self, index: int, clicked_func: Callable[[int, ], None] | None):
        self.tab_src_changed_func_mapping[self.tab_buttons[index].text()] = clicked_func
        
        def func():
            if clicked_func is not None:
                clicked_func(index)
            
            self.stack.setCurrentIndex(index)
            self.current_tab = self.tab_buttons[index].text()
            
            for i, button in enumerate(self.tab_buttons):
                button.setChecked(i == index)
            
            child: QWidget = self.stack.children()[index]
            if child.isWidgetType():
                child.setFocus()
        
        return func



class OptionsMenu(QFrame):
    def __init__(self, options: dict[str, Callable], parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        for option_name, option_func in options.items():
            btn = QPushButton(option_name)
            btn.clicked.connect(self.option_selected(option_func))
            layout.addWidget(btn)

    def option_selected(self, option_func: Callable):
        def func():
            option_func()
            self.hide()
        
        return func

class Image(QLabel):
    def __init__(self, path: str, parent=None, width: int | None = None, height: int | None = None):
        super().__init__(parent)
        
        pixmap = QPixmap(path)
        
        if width is not None or height is not None:
            if height is not None and width is None:
                self.setFixedSize(int(height * pixmap.size().width() / pixmap.size().height()), height)
            elif width is not None and height is None:
                self.setFixedSize(width, int(width * pixmap.size().height() / pixmap.size().width()))
            else:
                self.setFixedSize(width, height)
        
        self.setScaledContents(True)  # Optional: scale image to fit self
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

class LabeledField(QWidget):
    def __init__(self, title: str, inner_widget: QWidget, width_size_policy: QSizePolicy.Policy | None = None, height_size_policy: QSizePolicy.Policy | None = None, parent=None):
        super().__init__(parent)
        
        self.inner_widget = inner_widget
        
        if (width_size_policy, height_size_policy).count(None) != 2 :
            self.setSizePolicy(width_size_policy if width_size_policy is not None else QSizePolicy.Policy.Preferred,
                               height_size_policy if height_size_policy is not None else QSizePolicy.Policy.Preferred)
        
        # Title Label (floating effect)
        self.label = QLabel(title)
        self.label.setProperty("class", "labeled-title")
        
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Frame to wrap the actual widget with border
        self.widget = QWidget()
        self.widget.setProperty("class", "labeled-widget")
        
        widget_layout = QVBoxLayout(self.widget)
        # widget_layout.setContentsMargins(5, 0, 5, 5)  # leave space for label
        widget_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignLeft)
        widget_layout.addWidget(self.inner_widget)
        
        # Stack label over the widget
        main_layout = QVBoxLayout(self)
        # main_layout.setContentsMargins(4, 10, 4, 4)
        main_layout.setSpacing(0)
        # main_layout.addWidget(self.label)
        main_layout.addWidget(self.widget)
        
        self.setLayout(main_layout)

    def get_widget(self):
        return self.widget.findChild(QWidget)
    
    def addWidget(self, widget: QWidget, stretch: int = ..., alignment: Qt.AlignmentFlag = ...):
        self.inner_widget.layout().addWidget(widget, stretch, alignment)

class CharacterNameWidget(QWidget):
    def __init__(self, name: CharacterName):
        super().__init__()
        self.name = name
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        widget_2_1 = QWidget()
        layout_2_1 = QVBoxLayout()
        widget_2_1.setLayout(layout_2_1)
        
        widget_2_1_1 = QWidget()
        layout_2_1_1 = QHBoxLayout()
        widget_2_1_1.setLayout(layout_2_1_1)
        layout_2_1.addWidget(widget_2_1_1)
        
        name_1 = LabeledField("Surname", QLabel(self.name.sur))
        name_2 = LabeledField("First name", QLabel(self.name.first))
        name_3 = LabeledField("Middle name", QLabel(self.name.middle))
        
        layout_2_1_1.addWidget(name_1)
        layout_2_1_1.addWidget(name_2)
        layout_2_1_1.addWidget(name_3)
        
        widget_2_1_2 = QWidget()
        layout_2_1_2 = QHBoxLayout()
        widget_2_1_2.setLayout(layout_2_1_2)
        layout_2_1.addWidget(widget_2_1_2)
        
        name_4 = LabeledField("Other name", QLabel(self.name.other if self.name.other is not None else "No other name"))
        name_5 = LabeledField("Abbreviation", QLabel(self.name.abrev))
        
        layout_2_1_2.addWidget(name_4)
        layout_2_1_2.addWidget(name_5, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(LabeledField("Names", widget_2_1, height_size_policy=QSizePolicy.Policy.Maximum))



class BarChartCanvas(FigureCanvas):
    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(6, 5), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
    
    def bar(self, x_values, y_values, display_values = False, **kwargs):
        bars = self.axes.bar(x_values, y_values, **kwargs)
        
        # Optional: add value labels on top of each bar
        if display_values:
            for bar in bars:
                height = bar.get_height()
                self.axes.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height}', 
                                      ha='center', va='bottom')
        
        self.draw()

class GraphCanvas(FigureCanvas):
    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
    
    def plot(self, x, y, **kwargs):
        if x is not None:
            self.axes.plot(x, y, **kwargs)
        else:
            self.axes.plot(y, **kwargs)
        
        if y:
            self.axes.legend()
        self.draw()



class BarWidget(QWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        layout.addWidget(self.container)
        
        main_keys_widget = QWidget()
        self.main_keys_layout = QHBoxLayout()
        main_keys_widget.setLayout(self.main_keys_layout)
        
        self.bar_canvas = BarChartCanvas(title, x_label, y_label)
        
        self.main_layout.addWidget(main_keys_widget)
        self.main_layout.addWidget(self.bar_canvas)
    
    def add_data(self, name: str, color, data: tuple[list, list]):
        keys_widget, keys_layout = create_widget(None, QHBoxLayout)
        
        keys_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        key_frame = QFrame()
        key_frame.setStyleSheet(f"""
            background-color: {color};
            border: 1px solid black;
        """)
        key_frame.setFixedSize(20, 20)
        
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        keys_layout.addWidget(key_frame)
        keys_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.bar_canvas.bar(data[0], data[1], display_values=True, color=color, edgecolor="black")
        
        self.main_keys_layout.addWidget(keys_widget, alignment=Qt.AlignmentFlag.AlignLeft)
    
    def clear(self):
        self.bar_canvas.axes.clear()

class GraphWidget(QWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        layout.addWidget(self.container)
        
        self.graph = GraphCanvas(title, x_label, y_label)
        self.main_layout.addWidget(self.graph)
    
    def plot(self, x, y, **kwargs):
        self.graph.plot(x, y, **kwargs)
    
    def clear(self):
        self.graph.axes.clear()

