import unreal
import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy, QGroupBox, QToolButton, QComboBox
)

DESTINATION_FOLDER = "/Game/GeneratedBlueprints"
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 700

# Ensure destination folder exists
if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION_FOLDER):
    unreal.EditorAssetLibrary.make_directory(DESTINATION_FOLDER)

# ---------------- Collapsible Section ---------------- #
class CollapsibleBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setTitle("")
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setStyleSheet("QToolButton { border: none; font-weight: bold; }")
        self.toggle_button.toggled.connect(self.on_toggled)
        self.content = QWidget()
        self.content.setVisible(False)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(self.toggle_button)
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(self.content)

    def on_toggled(self, checked):
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.content.setVisible(checked)


# ---------------- Main Window ---------------- #
class BatchBlueprintCreator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.setWindowTitle("Blueprint Generator")
        self.setObjectName("ToolWindow")

        self.setStyleSheet("""
            QWidget {
                background: #f0f1f2;
                font-family: "Courier New", monospace;
                font-size: 13px;
            }
            #Header {
                background: #6ea6e6;
                color: #0b2540;
                border-bottom: 2px solid #0b2540;
            }
            QLabel.title {
                font-size: 24px;
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
                background: #08304a;
            }
            QGroupBox { border: none; }
        """)

        main_layout = QVBoxLayout(self)
        # Header
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(100)
        hl = QVBoxLayout(header)
        t = QLabel("Batch Blueprint\nCreator")
        t.setProperty("class", "title")
        t.setAlignment(Qt.AlignCenter)
        hl.addWidget(t)
        main_layout.addWidget(header)

        # Content
        content = QVBoxLayout()
        content.setContentsMargins(24, 16, 24, 16)
        content.setSpacing(12)

        # ---- Gravity ----
        self.gravity_cb = self._add_option(content, "Gravity")

        # ---- Collision settings ----
        collision_box = CollapsibleBox("Collision settings")
        inner = QVBoxLayout()
        inner.setSpacing(6)
        self.complex_simple_cb = self._add_option(inner, "Simple or Complex as Simple", inside=True)
        self.gen_overlap_cb = self._add_option(inner, "Generate overlap events", inside=True)

        # --- Collision Preset Dropdown ---
        row = QHBoxLayout()
        label = QLabel("Collision preset")
        label.setProperty("class", "option")
        self.collision_combo = QComboBox()
        self.collision_combo.setFixedWidth(180)
        self.collision_combo.addItems([
            "BlockAll",
            "BlockAllDynamic",
            "OverlapAll",
            "OverlapAllDynamic",
            "NoCollision",
            "PhysicsActor",
            "Pawn",
            "Spectator",
            "Custom"
        ])
        row.addWidget(label)
        row.addStretch()
        row.addWidget(self.collision_combo)
        row.setContentsMargins(20, 0, 0, 0)
        inner.addLayout(row)

        collision_box.content.setLayout(inner)
        content.addWidget(collision_box)

        # ---- CCD ----
        self.ccd_cb = self._add_option(content, "Continuous Collision Detection (CCD)")

        # Spacer
        content.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Info + Generate button
        self.info_label = QLabel("Selected assets: 0")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.info_label)
        btn_row.addStretch()
        self.generate_btn = QPushButton("Generate Blueprints")
        self.generate_btn.setProperty("class", "generate")
        self.generate_btn.setFixedWidth(180)
        self.generate_btn.clicked.connect(self.on_generate)
        btn_row.addWidget(self.generate_btn)
        content.addLayout(btn_row)

        main_layout.addLayout(content)
        self.update_selected_count()

    # ------------- Helper for making labeled checkbox rows ------------- #
    def _add_option(self, parent_layout, text, inside=False):
        row = QHBoxLayout()
        label = QLabel(text)
        label.setProperty("class", "option")
        checkbox = QCheckBox()
        row.addWidget(label)
        row.addStretch()
        row.addWidget(checkbox)
        if inside:
            row.setContentsMargins(20, 0, 0, 0)
        parent_layout.addLayout(row)
        return checkbox

    def update_selected_count(self):
        assets = unreal.EditorUtilityLibrary.get_selected_assets()
        self.info_label.setText(f"Selected assets: {len(assets)}")

    # ------------- Main logic ------------- #
    def on_generate(self):
        assets = unreal.EditorUtilityLibrary.get_selected_assets()
        self.update_selected_count()
        if not assets:
            unreal.log_warning("No assets selected.")
            return

        unreal.log(f"Generating blueprints for {len(assets)} assets.")
        tools = unreal.AssetToolsHelpers.get_asset_tools()

        for asset in assets:
            try:
                base_name = asset.get_name() + "_BP"
                unique_name = tools.create_unique_asset_name(f"{DESTINATION_FOLDER}/{base_name}", "")
                bp_name = unique_name[1] if isinstance(unique_name, (list, tuple)) else unique_name
                factory = unreal.BlueprintFactory()
                factory.set_editor_property("ParentClass", unreal.Actor)
                bp = tools.create_asset(bp_name, DESTINATION_FOLDER, unreal.Blueprint, factory)
                if not bp:
                    unreal.log_warning(f"Failed to create blueprint for {asset.get_name()}")
                    continue

                component = None
                if isinstance(asset, unreal.StaticMesh):
                    component = unreal.EditorUtilities.add_component_to_blueprint(bp, unreal.StaticMeshComponent, "StaticMeshComponent")
                    if component:
                        component.set_editor_property("static_mesh", asset)
                elif isinstance(asset, unreal.SkeletalMesh):
                    component = unreal.EditorUtilities.add_component_to_blueprint(bp, unreal.SkeletalMeshComponent, "SkeletalMeshComponent")
                    if component:
                        component.set_editor_property("skeletal_mesh", asset)
                else:
                    component = unreal.EditorUtilities.add_component_to_blueprint(bp, unreal.SceneComponent, "SceneRoot")

                # ---- Apply UI settings ----
                if component:
                    component.set_editor_property("enable_gravity", self.gravity_cb.isChecked())
                    component.set_editor_property("generate_overlap_events", self.gen_overlap_cb.isChecked())

                    if hasattr(component, "use_continuous_collision_detection"):
                        component.set_editor_property(
                            "use_continuous_collision_detection",
                            self.ccd_cb.isChecked()
                        )

                    if hasattr(component, "collision_complexity"):
                        if self.complex_simple_cb.isChecked():
                            component.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                        else:
                            component.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)

                    # Collision preset from dropdown
                    selected_preset = self.collision_combo.currentText()
                    component.set_editor_property("collision_profile_name", unreal.Name(selected_preset))

                unreal.EditorAssetLibrary.save_loaded_asset(bp)
                unreal.log(f"✅ Created Blueprint '{bp.get_name()}' with preset '{self.collision_combo.currentText()}'")

            except Exception as e:
                unreal.log_warning(f"Error creating BP for {asset.get_name()}: {e}")

        self.update_selected_count()


# ---------------- Launcher (UE5.6 Safe) ---------------- #
_global_window_ref = None

def launch_window():
    global _global_window_ref
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    for win in QApplication.allWindows():
        if isinstance(win, QWidget) and win.objectName() == "ToolWindow":
            try:
                win.close()
                win.deleteLater()
            except:
                pass

    window = BatchBlueprintCreator()
    window.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    window.show()
    window.raise_()
    window.activateWindow()

    try:
        unreal.parent_external_window_to_slate(window.winId())
    except Exception as e:
        unreal.log_warning(f"Could not parent to slate: {e}")

    _global_window_ref = window
    unreal.log("✅ Batch Blueprint Creator running (UE5.6 safe).")


if __name__ == "__main__":
    launch_window()
