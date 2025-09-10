
from imports import *

stylesheet = '''
  QWidget {{
    background-color: {bg};
    color: {text};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    margin: 0px
  }}
  
  QLabel:disabled {{
    color: {disabled};
  }}
  
  QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {input_border};
    border-radius: 5px;
    padding: 5px;
  }}
  
  QSlider {{
    color: {primary};
  }}
  
  QPushButton {{
    background-color: {primary};
    color: {primary_text};
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
  }}
  
  QPushButton:hover {{
    background-color: {primary_hover};
  }}

  QPushButton:pressed {{
    background-color: {primary_pressed};
  }}
  
  QPushButton:disabled {{
    background-color: {disabled};
  }}
  
  QComboBox {{
      background-color: {input_bg};
      color: {text};
      border: 1px solid {border};
      border-radius: 8px;
      padding: 6px;
      min-width: 120px;
  }}
  
  QComboBox::drop-down {{
      border: none;
      padding-right: 6px;
  }}
  
  QComboBox::down-arrow {{
      image: none;
      border: none;
      width: 12px;
      height: 12px;
      background-color: {primary};
      border-radius: 100%;
  }}
  
  QComboBox::down-arrow:hover {{
      background-color: {primary_hover};
  }}
  
  QComboBox QAbstractItemView {{
      background-color: {bg};
      border: 1px solid {border};
      selection-background-color: {primary};
      selection-color: {text};
  }}
  
  QCheckBox, QRadioButton {{
    spacing: 6px;
  }}
  
  QMenuBar {{
    background-color: {primary};
    color: {primary_text};
  }}

  QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
  }}

  QMenuBar::item:selected {{
    background: {primary_hover};
  }}
  
  QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 4px;
  }}

  QScrollBar {{
    background-color: {bg};
    border: none;
  }}

  QScrollBar:vertical, QScrollBar:horizontal {{
    background: {bg};
    border: none;
    width: 10px;
  }}

  QScrollBar::handle {{
    background: {scrollbar};
    border-radius: 4px;
    min-height: 20px;
  }}

  QToolTip {{
    background-color: {tooltip_bg};
    color: {tooltip_text};
    border: 1px solid {border};
    padding: 5px;
    border-radius: 3px;
  }}

  QTabWidget::pane {{
    border: 1px solid {border};
  }}

  QTabBar::tab {{
    background: {secondary};
    color: {text};
    padding: 6px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }}

  QTabBar::tab:selected {{
    background: {input_bg};
    font-weight: bold;
  }}
  
  QMenu, .option-menu {{
    background-color: {input_bg};
    color: {primary_text};
    border: 1px solid {border};
    padding: 0px
  }}
  
  QMenu::item:selected {{
    background-color: {highlight};
  }}
  
  .option-menu QPushButton {{
    border-radius: 0px;
    margin: 0px;
    border: none;
    background-color: {input_bg};
  }}
  
  .option-menu QPushButton:hover {{
    color: {primary_text};
    background-color: {primary};
  }}

  QTableView {{
    background-color: {bg};
    color: {text};
    gridline-color: {border};
    selection-background-color: {highlight};
  }}
  
  QPushButton.VerticalTab {{
      width: 100%;
      height: 50px;
      border-radius: 0px;
      border-right: 3px solid {bg2};
      background-color: {bg2};
      color: {text};
      margin: 0px;
  }}
  
  QPushButton.VerticalTab:hover {{
    border-right-color: {hover2};
    background-color: {hover2};
  }}
  
  QPushButton.VerticalTab:checked {{
    border-right-color: {primary};
    background-color: {secondary};
  }}
  
  QPushButton.VerticalTab:checked:hover {{
      background-color: {hover3};
  }}
  
  QPushButton.HorizontalTab {{
      width: 100%;
      height: 30px;
      border-top: 3px solid {bg2};
      background-color: {bg2};
      color: {text};
      border-radius: 0px;
      margin: 0px;
  }}
  
  QPushButton.HorizontalTab:hover {{
    border-top-color: {hover2};
    background-color: {hover2};
  }}
  
  QPushButton.HorizontalTab:checked {{
      border-top-color: {primary};
      background-color: {secondary};
  }}
  
  QPushButton.HorizontalTab:checked:hover {{
      background-color: {hover3};
  }}
  
  QCheckBox {{
      color: {text};
      spacing: 8px;
      padding: 4px;
  }}
  
  QCheckBox::indicator {{
      width: 18px;
      height: 18px;
      border-radius: 3px;
      border: 1px solid {border};
  }}
  
  QCheckBox::indicator:unchecked {{
      background-color: {bg};
  }}
  
  QCheckBox::indicator:checked {{
      background-color: {primary};
      border-color: {primary};
  }}
  
  QCheckBox::indicator:hover {{
      border-color: {primary_hover};
  }}

  .labeled-widget {{
    border: 1px solid {hover3};
  }}
  .labeled-widget:disabled {{
    border: 1px solid {disabled};
  }}
  
  .labeled-title {{
		color: {hover3};
  }}
  .labeled-title:disabled {{
		color: {disabled};
  }}
  
  .options-button {{
    font-size: 25px;
  }}
  
  QWidget.AttendanceTeacherWidget *, QWidget.StaffListTeacherWidget * {{
      background-color: {teacher};
  }}
  
  QWidget.AttendancePrefectWidget *, QWidget.StaffListPrefectWidget * {{
    background-color: {prefect};
  }}
  
  QWidget.StaffListTeacherWidget,
  QWidget.StaffListPrefectWidget,
  QWidget.AttendanceTeacherWidget,
  QWidget.AttendancePrefectWidget
  {{
    border-radius: 25px;
    padding: 50px;
    border: 2px solid grey;
  }}
  
  QWidget.StaffListTeacherWidget * QLabel,
	QWidget.AttendanceTeacherWidget * QLabel
  {{
		color: {text_teacher};
    font-weight: bold;
	}}
  
  QWidget.StaffListPrefectWidget * QLabel,
  QWidget.AttendancePrefectWidget * QLabel
  {{
		color: {text_prefect};
    font-weight: bold;
	}}
 
  QWidget.StaffListTeacherWidget * .labeled-title,
  QWidget.StaffListTeacherWidget * .options-button,
  QWidget.AttendanceTeacherWidget * .labeled-title,
  QWidget.AttendanceTeacherWidget * .options-button
  {{
		color: {title_text_teacher};
	}}
 
  QWidget.StaffListPrefectWidget * .labeled-title,
  QWidget.StaffListPrefectWidget * .options-button,
  QWidget.AttendancePrefectWidget * .labeled-title,
  QWidget.AttendancePrefectWidget * .options-button
  {{
		color: {title_text_prefect};
	}}
  
  QWidget.AttendanceTeacherWidget * .labeled-widget,
  QWidget.StaffListTeacherWidget * .labeled-widget
  {{
    border: 1px solid {title_text_teacher};
  }}
  
  QWidget.AttendancePrefectWidget * .labeled-widget,
  QWidget.StaffListPrefectWidget * .labeled-widget
  {{
    border: 1px solid {title_text_prefect};
  }}
  
  .labeled-title {{
    font-size: 11px;
    padding: 0 4px;
    padding-bottom: 0px;
  }}
  
  .labeled-widget {{
    border-radius: 6px;
  }}

'''

class ThemeManager:
    def __init__(self):
        self.themes: dict[str, dict[str, dict[str, str] | str]] = {}
        self.current_theme = None
        self.name = None

    def add_theme(self, name: str, theme_dict: dict):
        """Add a theme directly from a dict"""
        self.themes[name] = theme_dict

    def load_theme_from_file(self, file_path: str):
        """Load theme from a JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Theme file not found: {file_path}")
        with open(file_path, 'r') as f:
            theme = json.load(f)
            
            self.name = theme["$$theme$$"]
            general = theme["general"]
            
            for name1, theme_palette in theme["theme"].items():
                for name2, color_palette in theme["color"].items():
                    palette = deepcopy(theme_palette)
                    palette.update(color_palette)
                    palette.update(general)
                    
                    self.add_theme(f"{name1}-{name2}", {"palette": palette, "stylesheet": stylesheet})

    def apply_theme(self, app: QApplication):
        """Apply a stylesheet-only theme using values from JSON"""
        if self.name not in self.themes:
            raise ValueError(f"Theme '{self.name}' not loaded.")
        
        theme = self.themes[self.name]
        self.current_theme = self.name

        palette_vars = theme.get("palette")
        stylesheet_template = theme.get("stylesheet")

        # Inject palette variables into stylesheet using string formatting
        try:
            applied_stylesheet = stylesheet_template.format(**palette_vars)
        except KeyError as e:
            raise KeyError(f"Missing color value for: {e} on line {stylesheet_template[:stylesheet_template.find(str(e))].count("\n") + 1}")
        
        app.theme = theme
        app.setStyleSheet(applied_stylesheet)

    def get_current_theme(self):
        theme: dict[str, dict[str, str] | str] = self.themes.get(self.current_theme, None)
        
        return theme
    
    def get_current_palette(self):
      theme = self.get_current_theme()
      
      if theme is not None:
        return theme["palette"]

    def get_theme_names(self):
        return list(self.themes.keys())

THEME_MANAGER = ThemeManager()
THEME_MANAGER.load_theme_from_file("src/themes.json")

