# -*- coding: utf-8 -*-
import arcpy
import os
import json
from pathlib import Path
from json import JSONDecodeError
from jsonschema import validate, ValidationError
from openindexmaps_py.oimpy import OpenIndexMap, Sheet
from openindexmaps_py.geodex import GeodexDictionary

# Initialize the GeodexDictionary for lookup purposes
geodex_dict = GeodexDictionary()

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "GeodexTools"
        self.alias = "geodextools"
        self.tools = [LoadData, ExportGeodexJSON, ValidateGeodexJSON, BackupGeodatabase]  # Add new tools here


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

        param0.value = r"C:\Users\srappel\Documents\ArcGIS\Projects\Geodex\Connections\connection.sde"

        params = [param0]
        return params

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

        server_connection = parameters[0].valueAsText

        geodex_layer_path = f"{server_connection}\\Geodex.DBO.Geodex"

        if not arcpy.Exists(geodex_layer_path):
            raise arcpy.ExecuteError(
                f"Geodex layer '{geodex_layer_path}' does not exist or cannot be found."
            )

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.listMaps()[0]  # Access the first map in the project

        arcpy.MakeFeatureLayer_management(geodex_layer_path, "Geodex")

        geodex_layer = map.addDataFromPath(geodex_layer_path)

        arcpy.AddMessage(
            f"Successfully loaded the Geodex layer from: {geodex_layer_path}"
        )
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        try:
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

        param0 = arcpy.Parameter(
            displayName="Input Features",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

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
            parameterType="Optional",  
            direction="Input",
        )
        param2.value = False 
        params.append(param2)

        return params

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal validation is performed."""
        return

    def execute(self, parameters, messages):
        """Execute the tool."""
        input_layer = parameters[0].valueAsText
        output_json_path = parameters[1].valueAsText
        flip = parameters[2].value  
        
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

        date_fields = ["YEAR1", "YEAR1_TYPE", "YEAR2", "YEAR2_TYPE", "YEAR3", "YEAR3_TYPE", "YEAR4", "YEAR4_TYPE"]

        geodex_dict = GeodexDictionary()

        oim_date_dict = {
            "datePub": [97, 98, 99, 113],
            "date": [100, 110, 114, 116, 118, 119],
            "dateSurvey": [102, 109, 115],
            "datePhoto": [103, 104, 105, 106, 120],
            "edition": [121]
        }

        sheets = []

        with arcpy.da.SearchCursor(
            input_layer,
            list(field_mapping.keys()) + list(special_fields.keys()) + date_fields
        ) as cursor:
            for row in cursor:
                sheet_dict = {}

                for i, arcgis_field in enumerate(field_mapping.keys()):
                    oim_field = field_mapping[arcgis_field]
                    sheet_dict[oim_field] = row[i]

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


                if flip:
                    sheet_dict["label"], sheet_dict["title"] = sheet_dict["title"], sheet_dict["label"]

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

                for year in years:
                    for year_key, (year_val, year_type) in year.items():
                        if year_val is None or year_type is None:
                            continue
                        for date_key, type_list in oim_date_dict.items():
                            if year_type in type_list:
                                # Assign the most recent valid date to the corresponding OIM field
                                if dates[date_key] is None or int(year_val) > int(dates[date_key]):
                                    dates[date_key] = str(year_val)

                sheet_dict.update({k: v for k, v in dates.items() if v is not None})

                arcpy.AddMessage(f"Processing record: {sheet_dict}")

                try:
                    sheet = Sheet(sheet_dict)
                    sheets.append(sheet)
                except Exception as e:
                    arcpy.AddWarning(f"Skipping record due to error: {e}")
                    continue

        oim = OpenIndexMap(sheets)

        with open(output_json_path, "w") as json_file:
            json_file.write(str(oim))  # Using OpenIndexMap's __str__ method for GeoJSON export

        messages.addMessage(f"Successfully exported {len(sheets)} records to {output_json_path}")

        return


class ValidateGeodexJSON:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Validate Geodex JSON"
        self.description = "Validates a Geodex JSON file against a provided JSON Schema"

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName="Input JSON File",
            name="input_json",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )

        param1 = arcpy.Parameter(
            displayName="JSON Schema File",
            name="json_schema",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param1.value = r"C:\Users\srappel\Documents\ArcGIS\Projects\Geodex\schemas\1.0.0.schema.json" 

        return [param0, param1]

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def execute(self, parameters, messages):
        input_json = Path(parameters[0].valueAsText)
        schema_path = Path(parameters[1].valueAsText)

        try:
            # Load the schema from the given path
            with schema_path.open("r") as schema_file:
                schema = json.load(schema_file)

            with input_json.open("r") as json_file:
                json_data = json.load(json_file)

            # Validate the FeatureCollection against the schema
            validate(json_data, schema)
            messages.addMessage("The FeatureCollection is valid according to the JSON Schema.")
        except ValidationError as e:
            # Enhanced feedback with context
            messages.addErrorMessage(f"Validation error: {e.message} at {e.path}")
        except FileNotFoundError as e:
            messages.addErrorMessage(f"File not found: {e.filename}")
        except JSONDecodeError as e:
            messages.addErrorMessage(f"Error decoding JSON: {e.msg}")
        except Exception as e:
            messages.addErrorMessage(f"An unexpected error occurred: {e}")

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and added to the display."""
        return


class BackupGeodatabase:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Backup Geodatabase"
        self.description = "Backup the database to a feature class in a local GeoDatabase"

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = []

        # Input Feature Layer: The Geodex feature class
        param0 = arcpy.Parameter(
            displayName="Geodex Layer",
            name="GeodexLayer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
        )
        params.append(param0)

        # Output Workspace: The geodatabase where the feature class will be created
        param1 = arcpy.Parameter(
            displayName="Output Feature Class",
            name="OutputFeatureClass",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )
        params.append(param1)

        # Add to map switch
        param2 = arcpy.Parameter(
            displayName="Add to Map",
            name="AddToMap",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param2.value = False 
        params.append(param2)

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def execute(self, parameters, messages):
        """The source code of the tool."""
        GeodexLayer = parameters[0].valueAsText
        OutputFeatureClass = parameters[1].valueAsText
        AddToMap = parameters[2].value  # This is True or False based on user selection

        try:
            # Perform the feature copy operation
            arcpy.management.CopyFeatures(GeodexLayer, OutputFeatureClass)
            arcpy.AddMessage(f"Feature class {OutputFeatureClass} successfully created.")

            # Add the feature class to the map manually if the user wants it
            if AddToMap:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                map = aprx.activeMap
                map.addDataFromPath(OutputFeatureClass)
                arcpy.AddMessage(f"Feature class {OutputFeatureClass} added to the map.")
                
        except arcpy.ExecuteError:
            arcpy.AddError(f"Arcpy error: {arcpy.GetMessages(2)}")
        except Exception as e:
            arcpy.AddError(f"An unexpected error occurred: {str(e)}")

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
