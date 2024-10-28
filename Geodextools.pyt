# -*- coding: utf-8 -*-
import arcpy
import os
import json
from openindexmaps_py.oimpy import OpenIndexMap, Sheet
from openindexmaps_py.geodex import GeodexDictionary

# Initialize the GeodexDictionary for lookup purposes
geodex_dict = GeodexDictionary()

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "GeodexTools"
        self.alias = "geodextools"
        self.tools = [LoadData, ExportGeodexJSON]  # Add new tools here


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


class ExportGeodexJSON:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export Geodex JSON"
        self.description = "Export selected Geodex records to JSON format."

    def getParameterInfo(self):
        """Define parameter definitions."""
        params = []

        # Input Feature Layer: Select records from this layer
        param0 = arcpy.Parameter(
            displayName="Feature Layer",
            name="FeatureLayer",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input",
        )
        params.append(param0)

        # Output File: Specify the full path and filename of the output JSON
        param1 = arcpy.Parameter(
            displayName="Output JSON File",
            name="OutputJSON",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
        )
        params.append(param1)

        # FLIP: Boolean parameter to specify whether to flip RECORD and LOCATION
        param2 = arcpy.Parameter(
            displayName="Flip RECORD and LOCATION",
            name="flip",
            datatype="Boolean",
            parameterType="Optional",  # It's optional, default can be False
            direction="Input",
        )
        param2.value = False  # Set default value to False
        params.append(param2)

        return params

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal validation is performed."""
        
        # Check if the input Geodex layer is None and set a default
        if parameters[0].value is None:
            # Default feature layer: Geodex.DBO.Geodex
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            active_map = aprx.activeMap

            # Check if Geodex.DBO.Geodex is available in the active map layers
            for lyr in active_map.listLayers():
                if lyr.name == "Geodex.DBO.Geodex":
                    parameters[0].value = lyr
                    break

        # Check if the output JSON file path is None and set a default
        if parameters[1].value is None:
            # Set default output file relative to the project folder
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            project_folder = aprx.homeFolder

            parameters[1].value = os.path.join(project_folder, "output.json")

        # Ensure the FLIP parameter has a default value
        if parameters[2].value is None:
            # Set default value of FLIP to False if not specified
            parameters[2].value = False

        return

    def execute(self, parameters, messages):
        """Execute the tool."""
        input_layer = parameters[0].valueAsText
        output_json_path = parameters[1].valueAsText
        flip = parameters[2].value  # Get the FLIP value (True or False)
        
        # Define field mappings
        field_mapping = {
            "RECORD": "label",
            "LOCATION": "title",
            "PUBLISHER": "publisher",
            "X1": "west",
            "X2": "east",
            "Y1": "north",
            "Y2": "south",
            "CATLOC": "instCallNo",
            "EDITION_NO": "edition"
        }

        special_fields = {
            "DATE": "datePub",
            "PRODUCTION": "color",
            "PRIME_MER": "primeMer",
            "PROJECT": "projection",
            "ISO_TYPE": "isoType",
            "ISO_VAL": "isoVal",
            "SCALE": "scale"
        }

        # Date handling field mappings
        date_fields = ["YEAR1", "YEAR1_TYPE", "YEAR2", "YEAR2_TYPE", "YEAR3", "YEAR3_TYPE", "YEAR4", "YEAR4_TYPE"]

        # Initialize GeodexDictionary for lookups
        geodex_dict = GeodexDictionary()

        # Date classification for OIM
        oim_date_dict = {
            "datePub": [97, 98, 99, 113],
            "date": [100, 110, 114, 116, 118, 119],
            "dateSurvey": [102, 109, 115],
            "datePhoto": [103, 104, 105, 106, 120],
            "edition": [121]
        }

        # Create list to hold Sheet objects
        sheets = []

        # Start processing the selected features in the layer
        with arcpy.da.SearchCursor(
            input_layer,
            list(field_mapping.keys()) + list(special_fields.keys()) + date_fields
        ) as cursor:
            for row in cursor:
                sheet_dict = {}

                # Map basic fields directly
                for i, arcgis_field in enumerate(field_mapping.keys()):
                    oim_field = field_mapping[arcgis_field]
                    sheet_dict[oim_field] = row[i]

                # Handle special fields with lookups or transformations
                for i, arcgis_field in enumerate(special_fields.keys(), start=len(field_mapping)):
                    oim_field = special_fields[arcgis_field]
                    if arcgis_field == "PRODUCTION":
                        sheet_dict[oim_field] = geodex_dict.lookup("production", row[i])
                    elif arcgis_field == "PRIME_MER":
                        sheet_dict[oim_field] = geodex_dict.lookup("prime_meridian", row[i])
                    elif arcgis_field == "PROJECT":
                        sheet_dict[oim_field] = geodex_dict.lookup("projection", row[i])
                    elif arcgis_field == "ISO_TYPE":
                        sheet_dict["isoType"] = geodex_dict.lookup("iso_type", row[i])
                    elif arcgis_field == "ISO_VAL":
                        sheet_dict["isoVal"] = row[i]  # Same for isoVal
                    elif arcgis_field == "SCALE":
                        sheet_dict["scale"] = f"1:{row[i]}" if row[i] else None
                    elif arcgis_field == "DATE":
                        sheet_dict["date"] = str(row[i])


                # Handle FLIP logic (swapping RECORD and LOCATION if necessary)
                if flip:
                    sheet_dict["label"], sheet_dict["title"] = sheet_dict["title"], sheet_dict["label"]

                # Date Handling Logic
                years = [
                    {"year1": (row[-8], row[-7])},
                    {"year2": (row[-6], row[-5])},
                    {"year3": (row[-4], row[-3])},
                    {"year4": (row[-2], row[-1])}
                ]

                dates = {
                    "datePub": None,
                    "date": None,
                    "dateSurvey": None,
                    "datePhoto": None,
                    "edition": None,
                }

                # Iterate over the year fields and their types, applying OIM date grouping logic
                for year in years:
                    for year_key, (year_val, year_type) in year.items():
                        if year_val is None or year_type is None:
                            continue
                        for date_key, type_list in oim_date_dict.items():
                            if year_type in type_list:
                                # Assign the most recent valid date to the corresponding OIM field
                                if dates[date_key] is None or int(year_val) > int(dates[date_key]):
                                    dates[date_key] = str(year_val)

                # Update the sheet_dict with valid date fields
                sheet_dict.update({k: v for k, v in dates.items() if v is not None})

                # Debug: Print sheet_dict to ensure values are being captured correctly
                arcpy.AddMessage(f"Processing record: {sheet_dict}")

                # Create a Sheet object using the collected properties
                try:
                    sheet = Sheet(sheet_dict)
                    sheets.append(sheet)
                except Exception as e:
                    arcpy.AddWarning(f"Skipping record due to error: {e}")
                    continue

        # Step 8: Create an OpenIndexMap from the list of sheets
        oim = OpenIndexMap(sheets)

        # Step 9: Export the OpenIndexMap to GeoJSON
        with open(output_json_path, "w") as json_file:
            json_file.write(str(oim))  # Using OpenIndexMap's __str__ method for GeoJSON export

        # Inform user of success
        messages.addMessage(f"Successfully exported {len(sheets)} records to {output_json_path}")

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
