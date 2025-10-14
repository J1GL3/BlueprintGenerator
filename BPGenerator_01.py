import unreal

folder_path = "/Game/GeneratedBlueprints"

# Check if folder already exists
# Create folder
# Output message
if not unreal.EditorAssetLibrary.does_directory_exist(folder_path):
    success = unreal.EditorAssetLibrary.make_directory(folder_path)
    if success:
        unreal.log(f"Folder '{folder_path}' created successfully.")
    else:
        unreal.log_warning(f"Failed to create folder '{folder_path}'.")
else:
    unreal.log(f"Folder '{folder_path}' already exists.")


#get asset and name
#selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()

#if selected_assets:
    #asset = selected_assets[0]
    #asset_path = asset.get_path_name()
    #print(f"Selected asset: {asset_path}")
#else:
    #print("No assets selected.")



#UI --------------------------------------------------------------

import sys
from functools import partial  # if you want to include args with UI method calls
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLineEdit, QLabel, QVBoxLayout, QSlider, QRadioButton, QButtonGroup, QComboBox, QDial



# Subclass QMainWindow to customize your application's main window
class UnrealWindow(QWidget):
    def __init__(self, parent = None):
        super(UnrealWindow, self).__init__(parent)

        self.mainWindow= QMainWindow()
        self.mainWindow.setParent(self)

        self.button = QPushButton("Press Me!")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.buttonClicked)
        self.mainWindow.setFixedSize(QSize(450, 700))

        # Set the central widget of the Window.
        self.mainWindow.setCentralWidget(self.button)


    def buttonClicked(self, checked):
        unreal.log('BUTTON CLICKED')
        unreal.log('Checked: '+ str(checked))


        if checked:
            self.button.setText('You already pressed me!')
# Create Blueprint for selected asset ------------------------------------------------------------------------           
        # Get selected assets in Content Browser
            selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()

        # Destination folder for new Blueprints
            destination_path = "/Game/GeneratedBlueprints"

            for asset in selected_assets:
                # Example: process only Static Mesh assets (adapt as needed)
                if isinstance(asset, unreal.StaticMesh):
                    bp_name = asset.get_name() + "_BP"

                    # Create BlueprintFactory with Actor as parent
                    factory = unreal.BlueprintFactory()
                    factory.set_editor_property("ParentClass", unreal.Actor)

                    # Create the Blueprint asset
                    blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                        bp_name, destination_path, unreal.Blueprint, factory)

                    if blueprint:
                        # Add StaticMeshComponent to the Blueprint and assign mesh
                        sm_component = unreal.EditorUtilities.add_component_to_blueprint(
                            blueprint, unreal.StaticMeshComponent, "StaticMeshComponent")

                        if sm_component:
                            sm_component.set_editor_property("static_mesh", asset)

                        # Save the Blueprint asset
                        unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
                        print(f'Created Blueprint "{bp_name}" from asset "{asset.get_name()}"')
                    else:
                        print(f"Failed to create Blueprint for asset {asset.get_name()}")
                else:
                    print(f"Skipping asset {asset.get_name()} (not a Static Mesh)")
        else:
            self.button.setText('Press Me! (again)')
#----------------------------------------------------------------------------------------------------------------------------

    

def launchWindow():
    if QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QApplication.allWindows()):
            if 'toolWindow' in win.objectName(): # update this name to match name below
                win.destroy()
    else:
        QApplication(sys.argv)

    UnrealWindow.window = UnrealWindow()
    UnrealWindow.window.show()
    UnrealWindow.window.setWindowTitle("Blueprint Generator")
    UnrealWindow.window.setObjectName("ToolWindow")
    unreal.parent_external_window_to_slate(UnrealWindow.window.winId())



launchWindow()
