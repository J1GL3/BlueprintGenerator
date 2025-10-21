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
  



















def ListMenu(num = 1000):
    menuList = set()

    for i in range (num):
        #try to find unreal objects at a specific "path" in memory
        object = unreal.find_object(None, "/Engine/Transient.ToolMenu_0:RegisteredMenu_%s" % i)

        if not obj:
            #legacy path used fpr tje transent tool menu objects <-- only adding this for backards compatibility
            obj = unreal.find_object(None, f"/Engine/Transient.ToolsMenu_0:ToolMenu_{i}")
            if not obj:
                continue
        menuName = str(obj.menu_name)
        if menuName == "None":
            continue

        menuList.add(menuName)
        print(menuList)

#ListMenu()

tool_menus = unreal.ToolMenus.get()

def createNewMainMenu():
    mainMenu = tool_menus.find_menu("LevelEditor.MainMenu")
    #New Menu -> Section Name
    #Python Tool -> ID, Key used in the code internally
    #Menu Name -> Name of menu used for identification
    #Menu Label -> What we see in the UI
    newMenu = mainMenu.add_sub_menu("New Menu", "Python Tool", "Menu Name", "Menu Label")
    tool_menus.refresh_all_widgets()

#createNewMainMenu()

@unreal.uclass()
class MyEditActionScript(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        print ("M Edit Action Executed")


def createEditAction():
    editMenu = tool_menus.find_menu("LevelEditor.MainMenu.Edit")
    #we need to create a scriptable object
    MyEditAcionScriptObject = MyEditActionScript()
    MyEditAcionScriptObject.init_entry(
        owner_name=editMenu.menu_name,
        menu = editMenu.menu_name,
        section="EditMain",
        name = "MyEditCustomName",
        label = "My Edit Action",
        tool_tips= "this is my Edit Acion!"

    )

    MyEditAcionScriptObject.register_menu_entry()
    tool_menus.refresh_all_widgets

createEditAction()