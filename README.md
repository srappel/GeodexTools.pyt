# GeodexTools.pyt

![image](https://github.com/user-attachments/assets/b9591292-9133-4861-a91f-1f82f8641499)


GeodexTools.pyt is a Python Toolbox for ArcGIS Pro for working with the Geodex database--a polygon dataset stored in an Enterprise Geodatabase (SQL Server) on UWM's ArcGIS Server. The toolbox includes tools for loading Geodex data into ArcGIS and exporting it to GeoJSON format in the OpenIndexMaps specification.

## Features

- Load Data: This tool loads the Geodex.DBO.Geodex feature class from an Enterprise Geodatabase (SQL Server) into the current ArcGIS Pro project. It validates the server connection file and ensures that the dataset is loaded correctly.

- Export Geodex JSON: This tool exports selected Geodex records to JSON format. It provides options for customizing the output by flipping RECORD and LOCATION fields if needed, as many Geodex files reversed the usage of these two fields.
	
## Installation

1. Download the Toolbox: Clone or download the toolbox from the repository.
2. ArcGIS Pro Setup: Open ArcGIS Pro, and navigate to the Catalog pane. Right-click Toolboxes and select Add Toolbox. Browse to the location where you saved the GeodexTools.pyt file and add it to your project.

## Usage

### Load Data Tool

1. Open the Load Data tool in the GeodexTools toolbox.
2. Select the Server Connection parameter by browsing to your .sde connection file.
3. The tool will load the Geodex.DBO.Geodex feature class into your current ArcGIS Pro project.
	
### Export Geodex JSON Tool

1. Open the Export Geodex JSON tool.
2. Select records in the Geodex layer using any selection method (manual, select by attributes, select by location, etc.)
3. Select the Feature Layer from which to export selected records.
4. Specify the Output JSON File path.
5. (Optional) Set the Flip RECORD and LOCATION parameter to switch these fields in the output.
6. Run the tool, and the selected records will be saved as a JSON file which meets OIM specification 1.0


