
from imports import *
from theme import THEME_MANAGER
from functions_and_uncategorized import *

class SearchEdit[T](QFrame):
    def __init__(
        self,
        get_search_scope_callback: Callable[[], list[tuple[T, str, tuple[Optional[str], Optional[str], Optional[str]], list[Optional[str]]]]],
        goto_search_callback: Optional[Callable[[T], None]] = None, unallowed_characters: Optional[list[str]] = None
    ):
        super().__init__(None)
        
        self.get_search_scope_callback = get_search_scope_callback
        self.goto_search_callback = goto_search_callback
        self.unallowed_characters = unallowed_characters or []
        
        self.setProperty("class", "option-menu")
        
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        
        self.setFixedWidth(500)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("Search")
        self.search_le.setFixedWidth(500 - 4)
        self.search_le.textChanged.connect(self._make_find_dp)
        self.search_le.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        self.search_options_widget, self.search_options_layout = create_scrollable_widget(None, QVBoxLayout)
        self.search_options_widget.setProperty("class", "option-menu")
        self.search_options_widget.setFixedWidth(500 - 4)
        self.search_options_widget.setFixedHeight(220)
        
        self.main_layout.addWidget(self.search_le, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.search_options_widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
    
    def _make_find_dp(self, text: str):
        if next((False for c in self.unallowed_characters if c in text), True):
            score_data = sorted(
                [
                    (data_point, (search_name, right_text, bottom_text, end_text), self._get_find_score(text, search_name, (right_text, bottom_text, end_text), backgrounds_texts))
                    for data_point, search_name, (right_text, bottom_text, end_text), backgrounds_texts in
                    self.get_search_scope_callback()
                ],
                key=lambda params: params[2][0],
                reverse=True
            )
            
            options = [
                (self._stylize_text_indices(text, f"color: {THEME_MANAGER.pallete_get("primary")}; font-weight: bold;", right_text, bottom_text, end_text, indices), self._make_find_func(data_point))
                for data_point, (text, right_text, bottom_text, end_text), (score, indices) in
                score_data
                if score != -1
                ]
            
            if options:
                clear_layout(self.search_options_layout)
                
                self.search_options_layout.addStretch()
                
                for option_index, (option_name, option_func) in enumerate(options):
                    btn = QLabel(option_name)
                    btn.setProperty("class", "QPushButton")
                    btn.mousePressEvent = self._make_option_clicked_func(option_func)
                    
                    self.search_options_layout.insertWidget(option_index, btn, alignment=Qt.AlignmentFlag.AlignTop)
                
                if not self.search_options_widget.isVisible():
                    self.search_options_widget.setVisible(True)
            elif self.search_options_widget.isVisible():
                    self.search_options_widget.setVisible(False)
        else:
            self.search_le.setText("".join([c for c in text if c not in self.unallowed_characters]))
        
    def _make_find_func(self, data_point: T):
        def func():
            if self.goto_search_callback:
                self.goto_search_callback(data_point)
        
        return func
    
    def _get_find_score(
        self,
        text: str,
        potential_match: str,
        extra_text_data: Optional[tuple[Optional[str], Optional[str], Optional[str]]] = None,
        backgrounds_texts: Optional[list[Optional[str]]] = None
    ):
        l_text = text.lower()
        l_target = potential_match.lower()
        
        space_amt = 0
        additions = 0
        
        text_len = len(l_text)
        target_len = len(l_target)
        
        index = 0
        
        bg_data = []
        
        score_indices = []
        right_indices = []
        bottom_indices = []
        end_indices = []
        
        right_score = -1
        bottom_score = -1
        end_score = -1
        
        if extra_text_data:
            right_text, bottom_text, end_text = extra_text_data
            
            if right_text:
                right_score, right_indices = self._get_find_score(text, right_text)
                right_indices = right_indices[0]
            if bottom_text:
                bottom_score, bottom_indices = self._get_find_score(text, bottom_text)
                bottom_indices = bottom_indices[0]
            if end_text:
                end_score, end_indices = self._get_find_score(text, end_text)
                end_indices = end_indices[0]
        
        if backgrounds_texts:
            bg_data = [self._get_find_score(text, bg_text)[0] for bg_text in backgrounds_texts if bg_text is not None]
        
        for i, c in enumerate(l_text):
            f_index = l_target[index:].find(c)
            
            if f_index != -1 and text_len <= target_len:
                space_amt += f_index
                index += f_index + 1
                
                additions += text[i] == potential_match[index - 1]
                additions += f_index == 0
                
                score_indices.append(index - 1)
                
                continue
            break
        else:
            return (text_len / (target_len + space_amt)) + additions, (score_indices, [], [], [])
        
        if bottom_score == -1 and right_score != -1:
            return right_score / 20, ([], right_indices, [], [])
        elif right_score == -1 and bottom_score != -1:
            return bottom_score / 20, ([], [], bottom_indices, [])
        elif right_score != -1 and bottom_score != -1:
            return (right_score + bottom_score) / 20, ([], right_indices, bottom_indices, [])
        elif end_score != -1:
            return end_score / 20, ([], [], [], end_indices)
        elif bg_data:
            for bg_score in bg_data:
                if bg_score != -1:
                    return bg_score / 20, ([], [], [], [])
        
        return -1, ([], [], [], [])
    
    def _stylize_text_indices(self, main_text: str, style: str, right_text: Optional[str], bottom_text: Optional[str], end_text: Optional[str], indices: tuple[list[int], list[int], list[int]]):
        main_indices, right_indices, bottom_indices, end_indices = indices
        
        text = f"""
        <table width="100%">
        <tr>
            <td align="left">
            {"".join([f"<span style='font-size: 23px; {f"{style}" if i in main_indices else ""}'>{c}</span>" for i, c in enumerate(main_text)])}
            <span>    </span>
            {"".join([f"<span style='color: grey; font-size: 18px; font-weight: 300; {f"{style}" if i in right_indices else ""}'>{c}</span>" for i, c in enumerate(right_text)]) if right_text else ""}
            <br>
            {"".join([f"<span style='color: grey; font-size: 15px; font-weight: 500; {f"{style}" if i in bottom_indices else ""}'>{c}</span>" for i, c in enumerate(bottom_text)]) if bottom_text else ""}
            </td>
            <td align="right">
            {"".join([f"<span style='color: lightgrey; font-size: 10px; font-weight: 300; {f"{style}" if i in end_indices else ""}'>{c}</span>" for i, c in enumerate(end_text)]) if end_text else ""}
            </td>
            <br>
        </tr>
        </table>
        """
        return text
    
    def _make_option_clicked_func(self, option_func: Callable[[], None]):
        def func(_):
            self.hide()
            
            self.search_le.setText("")
            
            option_func()
        
        return func

    def show(self):
        self._make_find_dp("")
        
        return super().show()

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
    
    def set_options(self, options: dict[str, Callable]):
        clear_layout(self.main_layout)
        
        self.add_options(options)
    
    def add_options(self, options: dict[str, Callable]):
        for option_name, option_func in options.items():
            btn = QLabel(option_name)
            btn.setProperty("class", "QPushButton")
            btn.mousePressEvent = self._option_selected(option_func)
            
            self.main_layout.addWidget(btn)
    
    def _option_selected(self, option_func: Callable):
        def func(a0):
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
    """
    A container widget that displays a floating-style label
    above an inner widget (e.g. QLineEdit, QComboBox, custom form widget).
    """

    def __init__(
        self,
        title: str,
        inner_widget: QWidget,
        width_policy: QSizePolicy.Policy | None = None,
        height_policy: QSizePolicy.Policy | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.inner_widget = inner_widget

        # -----------------------
        # Size policy (optional)
        # -----------------------
        if width_policy or height_policy:
            self.setSizePolicy(
                width_policy or QSizePolicy.Policy.Preferred,
                height_policy or QSizePolicy.Policy.Preferred,
            )

        # -----------------------
        # Floating label
        # -----------------------
        self.label = QLabel(title, self)
        self.label.setProperty("class", "labeled-title")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # -----------------------
        # Frame container
        # -----------------------
        self.container = QWidget(self)
        self.container.setProperty("class", "labeled-container")

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(8, 10, 8, 8)
        container_layout.setSpacing(6)
        container_layout.addWidget(self.label)
        container_layout.addWidget(self.inner_widget)

        # -----------------------
        # Main layout
        # -----------------------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
    
    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag | None = None):
        if alignment is not None:
            self.inner_widget.layout().addWidget(widget, stretch, alignment)
        else:
            self.inner_widget.layout().addWidget(widget, stretch)
    
    def setTitle(self, text: str):
        self.label.setText(text)

class DropdownLabeledField(QWidget):
    def __init__(
        self,
        title: str,
        content: QWidget,
        expanded: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.setStyleSheet("""
            /* Header */
            QFrame.dropdown-header {
                /*background-color: #252526;*/
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }

            QFrame.dropdown-header:hover {
                /*background-color: #2a2d2e;*/
            }

            /* Title */
            QLabel.dropdown-title {
                color: #d4d4d4;
                font-size: 13px;
                font-weight: 500;
            }

            /* Arrow */
            QLabel.dropdown-arrow {
                color: #9cdcfe;
                font-size: 12px;
            }

            /* Content */
            QFrame.dropdown-container {
                border: 1px solid white;
                border-top: none;
                border-radius: 0 0 8px 8px;
                /*background-color: #1e1e1e;*/
            }

                           """)
        
        self._expanded = expanded
        self.content = content

        # -----------------------
        # Header
        # -----------------------
        self.header = QFrame()
        self.header.setProperty("class", "dropdown-header")
        self.header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "dropdown-title")

        self.arrow = QLabel("▶")
        self.arrow.setProperty("class", "dropdown-arrow")
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.arrow)

        # -----------------------
        # Content container
        # -----------------------
        self.container = QFrame()
        self.container.setProperty("class", "dropdown-container")

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 8, 10, 10)
        container_layout.addWidget(self.content)

        # Animation
        self.anim = QPropertyAnimation(self.container, b"maximumHeight")
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # -----------------------
        # Main layout
        # -----------------------
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.header)
        layout.addWidget(self.container)

        self.container.setMaximumHeight(0 if not expanded else 1_000_000)
        self._update_arrow()

        # Click handling
        self.header.mousePressEvent = self._toggle  # type: ignore

    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag | None = None):
        if alignment is not None:
            self.content.layout().addWidget(widget, stretch, alignment)
        else:
            self.content.layout().addWidget(widget, stretch)
    
    # -----------------------
    # Logic
    # -----------------------
    def _toggle(self, event):
        self.setExpanded(not self._expanded)

    def setExpanded(self, value: bool):
        if self._expanded == value:
            return

        self._expanded = value
        self._update_arrow()

        start = self.container.maximumHeight()
        end = self.container.sizeHint().height() if value else 0

        self.anim.stop()
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def _update_arrow(self):
        self.arrow.setText("▼" if self._expanded else "▶")

    def isExpanded(self) -> bool:
        return self._expanded


