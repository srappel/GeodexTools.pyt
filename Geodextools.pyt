# -*- coding: utf-8 -*-
import arcpy

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "GeodexTools"
        self.alias = "geodextools"
        self.tools = [LoadData]  # Add new tools here


class LoadData:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Load Data"
        self.description = "Load the Geodex database into the current project."

    def getParameterInfo(self):
        """Define the tool parameters."""

        # First parameter
        param0 = arcpy.Parameter(
            displayName="Server Connection",
            name="ServerConnection",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        
        server_connection = parameters[0].valueAsText

        # Only check if a value has been entered for the server connection
        if server_connection and not arcpy.Exists(server_connection):
            parameters[0].setErrorMessage("The specified .sde file does not exist.")
        return


    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Get the server connection (the path to the .sde file)
        server_connection = parameters[0].valueAsText

        # Define the full path to the Geodex feature class
        geodex_layer_path = f"{server_connection}\\Geodex.DBO.Geodex"

        # Check if the feature class exists
        if not arcpy.Exists(geodex_layer_path):
            raise arcpy.ExecuteError(
                f"Geodex layer '{geodex_layer_path}' does not exist or cannot be found."
            )

        # Access the current project and the first map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.listMaps()[0]  # Access the first map in the project

        # Create a feature layer from the feature class
        arcpy.MakeFeatureLayer_management(geodex_layer_path, "Geodex")

        # Add the feature layer to the map
        geodex_layer = map.addDataFromPath(geodex_layer_path)

        # Provide feedback to the user
        arcpy.AddMessage(
            f"Successfully loaded the Geodex layer from: {geodex_layer_path}"
        )
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        try:
            # Access the current project and the first map
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            map = aprx.listMaps()[0]  # Access the first map in the project

            # Find the "GeodexLayer" that was added
            for lyr in map.listLayers():
                if lyr.name == "Geodex":  # Ensure the name matches the layer added
                    # Zoom to the extent of the layer
                    map.defaultView.zoomToLayer(lyr)
                    arcpy.AddMessage("Zoomed to the Geodex layer's extent.")
                    break
            else:
                # If no matching layer was found
                arcpy.AddWarningMessage("The Geodex layer was not found in the current map.")
            
        except Exception as e:
            arcpy.AddError(f"An error occurred: {str(e)}")
            raise arcpy.ExecuteError(f"Failed to zoom to the Geodex layer: {str(e)}")

        return


##### TEMPLATE #####
#  class Tool:
#     def __init__(self):
#         """Define the tool (tool name is the name of the class)."""
#         self.label = "Tool"
#         self.description = ""

#     def getParameterInfo(self):
#         """Define the tool parameters."""
#         params = None
#         return params

#     def isLicensed(self):
#         """Set whether the tool is licensed to execute."""
#         return True

#     def updateParameters(self, parameters):
#         """Modify the values and properties of parameters before internal
#         validation is performed.  This method is called whenever a parameter
#         has been changed."""
#         return

#     def updateMessages(self, parameters):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""
#         return

#     def execute(self, parameters, messages):
#         """The source code of the tool."""
#         return

#     def postExecute(self, parameters):
#         """This method takes place after outputs are processed and
#         added to the display."""
#         return
