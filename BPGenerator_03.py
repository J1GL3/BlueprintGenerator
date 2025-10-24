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

    # ------------- Main logic (UE5.6 Fixed, robust) ------------- #
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

                # === Attempt 1: Use SubobjectDataSubsystem (editor's Add Component flow) ===
                try:
                    subsystem = None
                    try:
                        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
                    except Exception:
                        subsystem = None

                    if subsystem:
                        try:
                            BFL = unreal.SubobjectDataBlueprintFunctionLibrary

                            # Gather root subobject data handles for this blueprint
                            handles = subsystem.k2_gather_subobject_data_for_blueprint(context=bp)
                            if not handles:
                                unreal.log_warning(f"Could not gather root subobject data for {bp.get_name()}")
                                # fallthrough to SCS approach below
                                raise RuntimeError("no_handles")

                            root_handle = handles[0]
                            # Prepare AddNewSubobjectParams. If AddNewSubobjectParams is not available, construct via kwargs
                            try:
                                params = unreal.AddNewSubobjectParams(
                                    parent_handle=root_handle,
                                    new_class=unreal.StaticMeshComponent,
                                    blueprint_context=bp,
                                    conform_transform_to_parent=False,
                                    skip_mark_blueprint_modified=False
                                )
                                sub_handle, fail_reason = subsystem.add_new_subobject(params=params)
                            except Exception:
                                # fallback: older signature
                                sub_handle, fail_reason = subsystem.add_new_subobject(
                                    parent_handle=root_handle,
                                    new_class=unreal.StaticMeshComponent,
                                    blueprint_context=bp
                                )

                            # Check fail_reason if present
                            if hasattr(fail_reason, "is_empty"):
                                if not fail_reason.is_empty():
                                    unreal.log_warning(f"Failed to add subobject to {bp.get_name()}: {fail_reason}")
                                    raise RuntimeError("add_failed")
                            elif fail_reason:
                                unreal.log_warning(f"Failed to add subobject to {bp.get_name()}: {fail_reason}")
                                raise RuntimeError("add_failed")

                            # Rename the created subobject
                            try:
                                subsystem.rename_subobject(handle=sub_handle, new_name=unreal.Text(asset.get_name() + "_SM"))
                            except Exception:
                                # some engine builds use a string parameter rename method
                                try:
                                    subsystem.rename_subobject(handle=sub_handle, new_name=asset.get_name() + "_SM")
                                except Exception:
                                    pass

                            # Attach to root (best-effort)
                            try:
                                attached = subsystem.attach_subobject(owner_handle=root_handle, child_to_add_handle=sub_handle)
                                if attached is False:
                                    # log but continue
                                    unreal.log_warning(f"attach_subobject returned False for {bp.get_name()}")
                            except Exception:
                                # Some engine builds may have different method name
                                pass

                            # Resolve the actual UObject for the created subobject
                            data = BFL.get_data(sub_handle)
                            comp_obj = BFL.get_object(data)
                            if not comp_obj:
                                unreal.log_warning(f"Could not resolve created subobject to object for {bp.get_name()}")
                                raise RuntimeError("resolve_failed")

                            # Set the static mesh on the component
                            comp_obj.set_editor_property("static_mesh", asset)

                            # Apply UI toggles to component object
                            if hasattr(comp_obj, "enable_gravity"):
                                comp_obj.set_editor_property("enable_gravity", self.gravity_cb.isChecked())
                            if hasattr(comp_obj, "generate_overlap_events"):
                                comp_obj.set_editor_property("generate_overlap_events", self.gen_overlap_cb.isChecked())
                            if hasattr(comp_obj, "use_continuous_collision_detection"):
                                comp_obj.set_editor_property("use_continuous_collision_detection", self.ccd_cb.isChecked())
                            if hasattr(comp_obj, "collision_complexity"):
                                if self.complex_simple_cb.isChecked():
                                    comp_obj.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                                else:
                                    comp_obj.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
                            selected_preset = self.collision_combo.currentText()
                            comp_obj.set_editor_property("collision_profile_name", unreal.Name(selected_preset))

                            # Save blueprint after changes
                            bp.modify(True)
                            unreal.EditorAssetLibrary.save_loaded_asset(bp)
                            unreal.log(f"✅ Added StaticMeshComponent '{asset.get_name()}' to Blueprint '{bp.get_name()}' (subsystem)")
                            # Success; continue to next asset
                            continue

                        except Exception as sub_err:
                            # Subsystem attempt failed — fall back to SCS method below
                            unreal.log_warning(f"Subobject subsystem path failed for {bp.get_name()}: {sub_err}")
                            # do not continue; go to fallback SCS
                    else:
                        unreal.log("SubobjectDataSubsystem not available; falling back to SCS approach.")

                except Exception as e_sub_top:
                    unreal.log_warning(f"Subobject attempt top-level error for {bp.get_name()}: {e_sub_top}")
                    # fall through to SCS below

                # === Fallback: Simple Construction Script approach ===
                try:
                    # Load blueprint asset (ensure loaded)
                    bp_path = bp.get_path_name()
                    loaded_bp = unreal.EditorAssetLibrary.load_asset(bp_path)
                    # Try property names commonly present in different builds
                    scs = None
                    # Try lower-case property (some builds expose property)
                    try:
                        scs = loaded_bp.get_editor_property("simple_construction_script")
                    except Exception:
                        scs = None
                    # Try capitalized property (some other builds)
                    if not scs:
                        try:
                            scs = loaded_bp.get_editor_property("SimpleConstructionScript")
                        except Exception:
                            scs = None

                    if not scs:
                        unreal.log_warning(f"{bp.get_name()} has no accessible SCS; cannot attach StaticMeshComponent via fallback.")
                        continue

                    new_node = scs.create_node(unreal.StaticMeshComponent, asset.get_name() + "_SM")
                    new_node.set_editor_property("static_mesh", asset)

                    root_nodes = scs.get_root_nodes()
                    if root_nodes:
                        new_node.attach_to(root_nodes[0])
                    else:
                        scs.add_node(new_node)

                    # If possible, update the component template properties
                    try:
                        template = new_node.get_component_template()
                        if template:
                            if hasattr(template, "enable_gravity"):
                                template.set_editor_property("enable_gravity", self.gravity_cb.isChecked())
                            if hasattr(template, "generate_overlap_events"):
                                template.set_editor_property("generate_overlap_events", self.gen_overlap_cb.isChecked())
                            if hasattr(template, "use_continuous_collision_detection"):
                                template.set_editor_property("use_continuous_collision_detection", self.ccd_cb.isChecked())
                            if hasattr(template, "collision_complexity"):
                                if self.complex_simple_cb.isChecked():
                                    template.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                                else:
                                    template.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
                            selected_preset = self.collision_combo.currentText()
                            template.set_editor_property("collision_profile_name", unreal.Name(selected_preset))
                    except Exception:
                        pass

                    loaded_bp.modify(True)
                    unreal.EditorAssetLibrary.save_loaded_asset(loaded_bp)
                    unreal.log(f"✅ Added StaticMeshComponent '{asset.get_name()}' to Blueprint '{bp.get_name()}' (SCS fallback)")

                except Exception as scs_err:
                    unreal.log_warning(f"Fallback SCS approach failed for {bp.get_name()}: {scs_err}")
                    continue

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
