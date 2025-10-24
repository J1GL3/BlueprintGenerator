import unreal
import sys
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QFrame, QSpacerItem, QSizePolicy, QGroupBox, QToolButton, QComboBox
)

DestinationFolder = "/Game/GeneratedBlueprints"
WindowWidth = 450
WindowHeight = 450

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
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
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

        #creating main layout and setting it to verticle 
        #applying it to the main window as it refers it "self"
        main_layout = QVBoxLayout(self)





        #header --------------------------------------------------------------------------------------
        #creating the rectangular header frame
        header = QFrame()
        header.setFixedHeight(100)
        #making the header title go in a verticle way
        header_layout = QVBoxLayout(header)
        title = QLabel("Batch Blueprint Creator")
        #creating a class for the title so I can refer back to it when creating buttons
        title.setProperty("class", "title")
        #centers the text
        title.setAlignment(Qt.AlignCenter)
        #putting the title inside the header
        header_layout.addWidget(title)
        #add the header and everything inside it to the main window
        main_layout.addWidget(header)




        #content layout -----------------------------------------------------------------------------
        #creating a verticle layout
        content = QVBoxLayout()
        #creating empty space to leave betwen the edges of the contianer and the widgets
        content.setContentsMargins(16, 24, 16, 24)
        #setting the space between each widget inside
        content.setSpacing(12)


        

        #Gravity Button -----------------------------------------------------------------------------
        #creatin the check box, defining where to put it and keeping a reference for it
        self.gravity_checkbox = self._add_option(content, "Enable Gravity")




        #collision settings Box -------------------------------------------------------------------------
        #calling the defined "CollapsableBox" and giving it a title
        collision_box = CollapsibleBox("Collision settings")
        #creating a new verticle layout for new widgets
        inner = QVBoxLayout()
        #sets the verticle spacing of these new widgets
        inner.setSpacing(6)
        #creating 2 buttons and specifiying to put them in the inner layout
        self.simple_collision_checkbox = self._add_option(inner, "Simple or Complex as Simple", inside=True)
        self.gen_overlap_checkbox = self._add_option(inner, "Generate overlap events", inside=True)




        #collision preset dropdown ----------------------------------------------------------------------
        #creating a horizontal layout so the drop down is next to the title
        row = QHBoxLayout()
        #creating a title
        label = QLabel("Collision Presets")
        #creating a class name for the style sheet so we can style all options in the same way
        label.setProperty("classs","option")
        #creating a variable inside this class that makes a drop down menu widget
        self.collision_drop = QComboBox()
        #limiting its width
        self.collision_drop.setFixedWidth(180)
        #filling the dropdown with all the options
        self.collision_drop.addItems([
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
        #putting the title to the left
        row.addWidget(label)
        #stretching the row so the drop down is on the far right
        row.addStretch()
        #adding the dropdown itself to the row
        row.addWidget(self.collision_drop)
        #movong this row to the inner part of the Collision settings
        inner.addLayout(row)
        #moving the inner part into the content area 
        collision_box.content.setLayout(inner)
        #adding the collapsable "Collision Settings" into the main paige
        content.addWidget(collision_box)





        #CCD ------------------------------------------------------------------------------------------
        #adding in a check box for CCD, asigning it to the content part and keeping a reference for it
        self.ccd_checkbox = self._add_option(content, "Continuous Collision Detection")





        #Spacer ---------------------------------------------------------------------------------------- 
        #forcing the UI to the top by making an invisible flexible spacer to the bottom it
        content.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))




        #selected assets and Generate -----------------------------------------------------------------------------
        #creating a label for the selected assets and sotring it for later use/ updateabilty
        self.selected_assets = QLabel("Selected Assets")
        #creating a layout for the buttons at the bottom
        bottom_button_row = QHBoxLayout()
        #adds the selected assets label to the left of the row
        bottom_button_row.addWidget(self.selected_assets)
        #adding in space to push the generate button to the right
        bottom_button_row.addStretch()
        #creating a button, giving it a label and referencing it
        self.generate_button = QPushButton("Generate Blueprints")
        #gives it the QT style sheet class and labels it "generate" to style later
        self.generate_button.setProperty("class", "generate")
        # setting the width of the button for consistancy
        self.generate_button.setFixedWidth(180)
        #maikling it so when the button is clicked it calls the function "on generate"
        self.generate_button.clicked.connect(self.on_generate)
        #adding the button to the layout
        bottom_button_row.addWidget(self.generate_button)
        #adding the bottom button row to the content section and automatically puts it at the bottom
        content.addLayout(bottom_button_row)
        



        #putting everything we have so far into the main layout ---------------------------------------------------
        main_layout.addLayout(content)




        #live selected count -------------------------------------------------------------------------------------
        #creating a variable to remember last number of selected assets to detect if anything has changed
        self._last_asset_count = 0
        #creating a timer
        self.timer = QTimer()
        #conection the timers timeout signal to the "update_selected_count" function
        self.timer.timeout.connect(self.update_selected_count)
        #setting it so the timer starts every 0.5 seconds
        self.timer.start(500)




        #loop to uncheck boxes -----------------------------------------------------------------------------------
        for cb in [self.gravity_checkbox, self.simple_collision_checkbox, self.gen_overlap_checkbox, self.ccd_checkbox]:
            #make sure unchecked
            cb.setCheckState(Qt.Unchecked)




    #creating a private function that takes 4 arguments self, parent_layout, text, inside ------------------------
    #self - the instance of the class
    #parent_layout - the layout this row should be added to
    #text - the text for the label
    #inside - optional flag that controls whether the row should be indented slightly
    def _add_option(self, parent_layout, text, inside=False):
        #creating a horizontal row layout
        row = QHBoxLayout()
        #makes a text label using whatever text is passed in e.g (Enable Gravity, Collision settings)
        label = QLabel(text)
        #gives the QSS class name "option" for reference later
        label.setProperty("class", "option")
        #creating the checkbox widget
        checkbox = QCheckBox()
        #determining their position.
        #adding the label to the left of the row
        #stretching the space to push the check box to the right 
        #adding in the check box
        row.addWidget(label)
        row.addStretch()
        row.addWidget(checkbox)
        #if it is inside a collapsable box it will indent the row a bit so it alligns nicer 
        if inside:
            row.setContentsMargins(20, 0, 0, 0)
        #adds the horizontal row (the label and the check box) into the verticle row it belongs to   
        parent_layout.addLayout(row)
        #returning the checkbox object
        return checkbox
    



    #creating the function to call every 0.5 seconds to check for selceted assets ----------------------------
    def update_selected_count(self):
        #get all asset objects that are selected by calling UE's Python API
        assets = unreal.EditorUtilityLibrary.get_selected_assets()
        #counting how many were slected and returns the length of a list in python
        count = len(assets)
        #check if number of selected assets has changed
        if count != self._last_asset_count:
            #updates stored count to new count
            self._last_asset_count = count
            #updates the label at the bottom of the UI so the user can see
            self.selected_assets.setText(f"Selected assets: {count}")    

        


    #creating the function that runs when we click "generate blueprints" -------------------------------------
    def on_generate(self):
        #get all asset objects that are selected by calling UE's Python API
        assets = unreal.EditorUtilityLibrary.get_selected_assets()
        #if list is empty it returns a warning and stops running
        if not assets:
            unreal.log_warning("WARNING, No assets selected.")
            return

        #logs how many assets are selected
        unreal.log(f"Generating blueprints for {len(assets)} assets...")
        

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        #creating a loop to itterate through each individual asset
        for asset in assets:
            #checking if the selected asset is a static mesh if not it jsut skips it doesnt break
            try:
                if not isinstance(asset, unreal.StaticMesh):
                    unreal.log_warning(f"Skipping {asset.get_name()} (not a StaticMesh).")
                    continue

                # Define asset name & path
                bp_name = f"BP_{asset.get_name()}"
                bp_path = f"{DestinationFolder}/{bp_name}"

                # Check if BP already exists
                if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
                    unreal.log_warning(f"Blueprint {bp_name} already exists. Skipping.")
                    continue

                # Create the Blueprint asset
                bp_factory = unreal.BlueprintFactory()
                bp_factory.set_editor_property("ParentClass", unreal.Actor)
                new_bp = asset_tools.create_asset(bp_name, DestinationFolder, unreal.Blueprint, bp_factory)

                if not new_bp:
                    unreal.log_warning(f"❌ Failed to create Blueprint for {asset.get_name()}")
                    continue

                unreal.log(f"✅ Created empty Blueprint: {bp_name}")
                
                 # --- Add StaticMeshComponent using SubobjectDataSubsystem ---
                subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
                handles = subsystem.k2_gather_subobject_data_for_blueprint(context=new_bp)
                if not handles:
                    unreal.log_warning(f"Could not gather subobject data for {bp_name}")
                    continue

                root_handle = handles[0]  # Root is usually DefaultSceneRoot

                params = unreal.AddNewSubobjectParams(
                    parent_handle=root_handle,
                    new_class=unreal.StaticMeshComponent,
                    blueprint_context=new_bp
                )

                sub_handle, fail_reason = subsystem.add_new_subobject(params=params)
                if fail_reason != unreal.AddNewSubobjectFailureReason.NONE:
                    unreal.log_warning(f"❌ Failed to add StaticMeshComponent to {bp_name}: {fail_reason}")
                    continue

                # Rename component
                subsystem.rename_subobject(handle=sub_handle, new_name=unreal.Text("StaticMeshComp"))

                # --- Assign the StaticMesh to that component ---
                static_mesh_comp = subsystem.get_object_from_handle(sub_handle)
                static_mesh_comp.set_editor_property("StaticMesh", asset)

                # --- Save the Blueprint ---
                unreal.EditorAssetLibrary.save_loaded_asset(new_bp)
                unreal.log(f"💾 Saved Blueprint: {bp_name}")

            except Exception as e:
                unreal.log_warning(f"⚠️ Error creating BP for {asset.get_name()}: {e}")
        




#Launcher ----------------------------------------------------------------------------------------------------------------------
#making sure the window stays open and python doesnt close the window 
_global_window_ref = None

#creating a function that launches the tools window
def launch_window():
    #making sure we are modifying the correct variable not a new local one
    global _global_window_ref
    #checking if there is a "QApplication" already running
    app = QApplication.instance()
    #if it isnt it creates a new one
    if not app:
        app = QApplication(sys.argv)

    #checks if any instance of the tool is already open and if so it deletes/closes it
    for win in QApplication.allWindows():
        if isinstance(win, QWidget) and win.objectName() == "ToolWindow":
            try:
                win.close()
                win.deleteLater()
            except:
                pass

    #create and show the new window
    #creating an instance of the tool UI
    window = BatchBlueprintCreator()
    #actually displaying it
    window.show()
    #bringing it to the front
    window.raise_()
    #making sure it gets focused
    window.activateWindow()

    #parent the tool to unreals editor
    try:
        unreal.parent_external_window_to_slate(window.winId())
        #if it doesnt work it outputs an error
    except Exception as e:
        unreal.log_warning(f"Could not parent to slate: {e}")

    #making sure it doesnt get garbageed by python
    _global_window_ref = window
    #writes a message to output log so its clear it ran successfully
    unreal.log("YAY!!! Batch Blueprint Creator running.")

#run the script
if __name__ == "__main__":
    launch_window()