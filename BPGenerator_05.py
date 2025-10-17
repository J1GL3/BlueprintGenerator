import unreal
import sys
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy, QGroupBox, QToolButton, QComboBox
)

DestinationFolder = "/Game/GeneratedBlueprints"
WindowWidth = 450
WindowHeight = 700

# Ensure folder exists ------------------------------------------------------
if not unreal.EditorAssetLibrary.does_directory_exist(DestinationFolder):
    unreal.EditorAssetLibrary.make_directory(DestinationFolder)
    print ("GeneratedBlueprints, folder created")
# If not print, already exists ----------------------------------------------
else:
    print ("GeneratedBlueprints, folder already exists")



# Collapsible section ------------------------------------------------
class CollapsibleBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setTitle("")
        self.toggle_button = QToolButton(test=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        # Button Border ----------------------------------
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #808080;
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
            }
        """)
        # creates buttons, drop downs and layouts for buttons 
        self.toggle_button.toggled.connect(self.on_toggled)
        self.content = QWidget()
        self.content.setVisible(False)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(self.toggle_button)
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(self.content)

    #setting drop down section visible on toggled -----------
    def on_toggled(self, checked):
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.content.setVisible(checked)


# Main Window --------------------------------------------------------
class BatchBlueprintCreator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(WindowWidth, WindowHeight))
        self.setWindowTitle("Blueprint Generator")
        self.setObjectName("ToolWindow")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("""
            QWidget {
                background: #e7ecef;
                font-family: "Courier New", monospace;
                font-size: 13px;
            }
            #Header {
                background: #6096ba;
                color: #6096ba;
                border-bottom: 2px solid #0b2540;
            }
            QLabel.title {
                font-size: 30px;
                font-weight: 900;
            }
            QLabel.option {
                font-weight: bold;
            }
            QPushButton.generate {
                background: #0b2540;
                color: white;
                font-weight: 700;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton.generate:pressed {
                background: #6096ba;
            }
            QGroupBox { border: none; }
        """)
        