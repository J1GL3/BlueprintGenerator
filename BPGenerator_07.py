import unreal
import sys
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy, QGroupBox, QToolButton, QComboBox
)

DESTINATION_FOLDER = "/Game/GeneratedBlueprints"
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 450

# Ensure folder exists
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
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("""
            QWidget {
                background: #e7ecef;
                font-family: "Courier New", monospace;
                font-size: 13px;
            }
            #Header {
                background-color: #6096ba;
                border: none;
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
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #0b2540;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #6096ba;
                border: 2px solid #0b2540;
            }
        """)

        main_layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(100)
        header_layout = QVBoxLayout(header)
        title = QLabel("Batch Blueprint\nCreator")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        main_layout.addWidget(header)

        # Content layout
        content = QVBoxLayout()
        content.setContentsMargins(24, 16, 24, 16)
        content.setSpacing(12)

        # Gravity
        self.gravity_cb = self._add_option(content, "Enable Gravity")

        # Collision Settings
        collision_box = CollapsibleBox("Collision settings")
        inner = QVBoxLayout()
        inner.setSpacing(6)
        self.simple_collision_cb = self._add_option(inner, "Simple or Complex as Simple", inside=True)
        self.gen_overlap_cb = self._add_option(inner, "Generate overlap events", inside=True)

        # Collision Preset Dropdown
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

        # CCD
        self.ccd_cb = self._add_option(content, "Continuous Collision Detection (CCD)")

        # Spacer
        content.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Info + Generate
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

        # Live selection count
        self._last_asset_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_selected_count)
        self.timer.start(500)

        for cb in [self.gravity_cb, self.simple_collision_cb, self.gen_overlap_cb, self.ccd_cb]:
            cb.setCheckState(Qt.Unchecked)

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
        count = len(assets)
        if count != self._last_asset_count:
            self._last_asset_count = count
            self.info_label.setText(f"Selected assets: {count}")

    def on_generate(self):
        assets = unreal.EditorUtilityLibrary.get_selected_assets()
        if not assets:
            unreal.log_warning("⚠️ No assets selected.")
            return

        unreal.log(f"🛠 Generating blueprints for {len(assets)} assets...")
        
        for asset in assets:
            try:
                if not isinstance(asset, unreal.StaticMesh):
                    unreal.log_warning(f"Skipping {asset.get_name()} (not a StaticMesh).")
                    continue

                # Create blueprint using the working SCS method
                self.create_blueprint_with_scs(asset)

            except Exception as e:
                unreal.log_warning(f"⚠️ Error creating BP for {asset.get_name()}: {e}")

    def create_blueprint_with_scs(self, static_mesh):
        """Create blueprint with static mesh using SCS (Simple Construction Script)"""
        try:
            bp_name = f"{static_mesh.get_name()}_BP"
            
            # Create unique asset name
            tools = unreal.AssetToolsHelpers.get_asset_tools()
            unique_name = tools.create_unique_asset_name(f"{DESTINATION_FOLDER}/{bp_name}", "")
            bp_name = unique_name[1] if isinstance(unique_name, (list, tuple)) else unique_name

            # Create Blueprint Actor asset
            factory = unreal.BlueprintFactory()
            factory.set_editor_property("ParentClass", unreal.Actor)
            blueprint = tools.create_asset(bp_name, DESTINATION_FOLDER, unreal.Blueprint, factory)
            
            if not blueprint:
                unreal.log_warning(f"❌ Failed to create blueprint for {static_mesh.get_name()}")
                return

            # Access the Simple Construction Script (SCS)
            skeleton = blueprint.simple_construction_script
            
            # Get root nodes
            root_nodes = skeleton.get_root_nodes()
            if not root_nodes:
                unreal.log_warning("No root nodes found in the Blueprint's SCS")
                return
            
            root_node = root_nodes[0]

            # Add StaticMeshComponent node
            component_name = f"{static_mesh.get_name()}_Mesh"
            smc_node = skeleton.create_node(unreal.StaticMeshComponent, component_name)
            
            if not smc_node:
                unreal.log_warning("Failed to create StaticMeshComponent node")
                return

            # Attach to root node
            smc_node.attach_to(root_node)
            skeleton.add_node(smc_node)

            # Get the component template to set its properties
            smc_template = smc_node.component_template
            if smc_template:
                # Set the static mesh
                smc_template.set_editor_property("StaticMesh", static_mesh)
                
                # Apply physics settings
                smc_template.set_editor_property("bEnableGravity", self.gravity_cb.isChecked())
                smc_template.set_editor_property("bGenerateOverlapEvents", self.gen_overlap_cb.isChecked())
                smc_template.set_editor_property("bUseCCD", self.ccd_cb.isChecked())

                # Apply collision settings
                if self.simple_collision_cb.isChecked():
                    smc_template.set_editor_property("CollisionComplexity", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                else:
                    smc_template.set_editor_property("CollisionComplexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)

                # Apply collision preset
                preset = self.collision_combo.currentText()
                smc_template.set_editor_property("CollisionProfileName", unreal.Name(preset))
                
                unreal.log(f"✅ Successfully set static mesh and properties for {component_name}")
            else:
                unreal.log_warning("Failed to get Static Mesh Component template from node")
                return

            # Save and compile Blueprint
            unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
            blueprint.mark_package_dirty()
            
            # Open in editor
            editor_subsystem = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
            editor_subsystem.open_editor_for_assets([blueprint])
            
            unreal.log(f"✅ Successfully created blueprint with static mesh: {blueprint.get_name()}")

        except Exception as e:
            unreal.log_warning(f"❌ Error creating blueprint: {e}")


# ---------------- Launcher ---------------- #
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
    window.show()
    window.raise_()
    window.activateWindow()

    try:
        unreal.parent_external_window_to_slate(window.winId())
    except Exception as e:
        unreal.log_warning(f"Could not parent to slate: {e}")

    _global_window_ref = window
    unreal.log("✅ Batch Blueprint Creator running.")


if __name__ == "__main__":
    launch_window()