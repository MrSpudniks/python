import ezdxf
from PyQt5.QtWidgets import QWidget  # Update imports for QScrollArea
from PyQt5.QtCore import QRect
import xml.etree.ElementTree as ET
from xml.dom import minidom  # For pretty-printing the XML
import regex

# Function to parse the DXF file and extract POLYLINE, LINE, and Block Reference entities
def parse_dxf_file(dxf_file, thickness : int = 5, scale : float = 1, margin : int = 50):
    # Load the DXF file
    doc = ezdxf.readfile(dxf_file)
    lines = []
    butterfly_valves = []
    throttle_valves = []

    min_x, min_y = float('inf'), float('inf') # Initialize min_x and min_y to very large values
    max_x, max_y = float('-inf'), float('-inf')  # Initialize max_y to track the highest Y for flipping purposes


    for layer in doc.layers.entries:
        layer[0]

    # Process POLYLINE and LWPOLYLINE entities
    for entity in doc.entities:
        if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:

            points = entity.get_points('xy')  # Get the vertices of the polyline

            # Track the minimum and maximum x, y coordinates
            for x, y in points:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
            
            # Create segments from polyline vertices
            for i in range(len(points) - 1):
                start_x, start_y = points[i]
                end_x, end_y = points[i + 1]

                width = round(max(start_x, end_x) - min(start_x, end_x)) * scale + thickness
                height = round(max(start_y, end_y) - min(start_y, end_y)) * scale + thickness

                lines.append({
                    'x': min(start_x, end_x),
                    'y': max(start_y, end_y),
                    'width': width,
                    'height': height
                })

        if entity.dxftype() == 'LINE':
            start_x, start_y, _ = entity.dxf.start
            end_x, end_y, _ = entity.dxf.end

            # Track the minimum and maximum x, y coordinates
            min_x = min(min_x, start_x, end_x)
            max_x = max(max_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_y = max(max_y, start_y, end_y)

            width = round(max(start_x, end_x) - min(start_x, end_x)) * scale + thickness
            height = round(max(start_y, end_y) - min(start_y, end_y)) * scale + thickness

            lines.append({
                'x': min(start_x, end_x),
                'y': max(start_y, end_y),
                'width': width,
                'height': height
            })

    # Process Block References for Butterfly Valves
    for block_ref in doc.modelspace().query('INSERT'):
        # Check if block name ends with "F_MMC"
        if block_ref.dxf.name.endswith("F_MMC"):
            #print(f"Processing Block Reference: {block_ref.dxf.name}")  # Debugging statement
            
            # Access attributes directly
            attributes = block_ref.attribs  # Access the list of attributes directly
            rotation = block_ref.dxf.rotation

            # Print attributes for debugging
            valve_properties = {}
            
            for attr in attributes:
                #print(f"Attribute Tag: {attr.dxf.tag}, Value: {attr.dxf.text}")
                valve_properties[attr.dxf.tag] = attr.dxf.text
            

            # Check for the relevant title and ensure textMessage is set to "ManualOpenClose"
            title = valve_properties.get("ITEMNR.", "")  # Set title from ITEMNR.
            
            butterfly_valves.append({
                'x': block_ref.dxf.insert.x,
                'y': block_ref.dxf.insert.y,
                'size': 10,  # Set a default size for the butterfly valve
                'title': title,
                'routing': valve_properties.get("routing", ""),
                'textMessage': "ManualOpenClose",  # Always set to "ManualOpenClose"
                'rotate': rotation,  
                'labelOffsetY': float(valve_properties.get("labelOffsetY", 0.0)),  # Convert to float
                'enableValveMenu': valve_properties.get("enableValveMeny", "false") == "true",  # Convert to boolean
            })
        # Check if block name ends with "FP_MMC"
        if block_ref.dxf.name.endswith("FP_MMC"):
            #print(f"Processing Block Reference: {block_ref.dxf.name}")  # Debugging statement
            
            # Access attributes directly
            attributes = block_ref.attribs  # Access the list of attributes directly
            

            # Print attributes for debugging
            valve_properties = {}
            
            for attr in attributes:
                #print(f"Attribute Tag: {attr.dxf.tag}, Value: {attr.dxf.text}")
                valve_properties[attr.dxf.tag] = attr.dxf.text
            

            # Check for the relevant title and ensure textMessage is set to "ManualOpenClose"
            title = valve_properties.get("ITEMNR.", "")  # Set title from ITEMNR.
            
            throttle_valves.append({
                'x': block_ref.dxf.insert.x,
                'y': block_ref.dxf.insert.y,
                'size': 10,  # Set a default size for the butterfly valve
                'title': title,
                'routing': valve_properties.get("routing", ""),
                'textMessage': "",  # Always set to ""
                'rotate': 0.0,  
                'labelOffsetY': float(valve_properties.get("labelOffsetY", 0.0)),  # Convert to float
                'enableValveMenu': valve_properties.get("enableValveMeny", "false") == "true",  # Convert to boolean
            })

            print(block_ref.dxf.name)

        

    # fix coordinates
    for line in lines:
        line["y"] = round(max_y - line["y"])
        line["y"] = round(line["y"] + margin / scale) * scale
        line["x"] = round(line["x"] - min_x + margin / scale) * scale
        
    for valve in butterfly_valves:
        valve["y"] = round(max_y - valve["y"])
        valve["y"] = round(valve["y"] + margin / scale) * scale
        valve["x"] = round(valve["x"] - min_x + margin / scale) * scale

    for valve in throttle_valves:
        valve["y"] = round(max_y - valve["y"])
        valve["y"] = round(valve["y"] + margin / scale) * scale
        valve["x"] = round(valve["x"] - min_x + margin / scale) * scale

    max_x = round((max_x - min_x) * scale) + margin
    max_y = round((max_y - min_y) * scale) + margin
    min_x = margin
    min_y = margin

    print(round(min_x), round(max_x), round(min_y), round(max_y))
    return lines, butterfly_valves, throttle_valves, max_x, max_y



# Function to create an MMCFPPipe widget based on parsed LINE info
def create_pipe_widget_xml(line, widget_id):  # Add max_y as a parameter

    widget = ET.Element('widget', {'class': 'MMCFPPipe', 'name': f'pipe_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')

    ET.SubElement(rect, 'x').text = str(line["x"])
    ET.SubElement(rect, 'y').text = str(line["y"])
    ET.SubElement(rect, 'width').text = str(line["width"])
    ET.SubElement(rect, 'height').text = str(line["height"])
    return widget



# Function to create an MMCFPButterflyValve widget based on parsed valve info
def create_butterfly_valve_widget_xml(valve, widget_id, scale):  # Add max_y as a parameter
    x = valve['x']
    y = valve['y']

    widget = ET.Element('widget', {'class': 'MMCFPButterflyValve', 'name': f'butterfly_valve_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')
    
    if valve['rotate'] == 0:
        ET.SubElement(rect, 'x').text = str(int(x) - 0)
        ET.SubElement(rect, 'y').text = str(int(y) - 0)
    else:
        ET.SubElement(rect, 'x').text = str(int(x) - 0)
        ET.SubElement(rect, 'y').text = str(int(y) - 0)
    
    ET.SubElement(rect, 'width').text = str(18)
    ET.SubElement(rect, 'height').text = str(18)

    # Add additional properties
    for prop_name in ['title', 'routing', 'textMessage', 'rotate', 'labelOffsetY', 'enableValveMenu']:
        prop = ET.SubElement(widget, 'property', {'name': prop_name})
        if prop_name == 'textMessage':
            ET.SubElement(prop, 'string').text = "ManualOpenClose"  # Always set to "ManualOpenClose"
        elif prop_name in valve:
            if isinstance(valve[prop_name], bool):
                ET.SubElement(prop, 'bool').text = str(valve[prop_name]).lower()  # Convert bool to lowercase string
            elif isinstance(valve[prop_name], float):
                ET.SubElement(prop, 'double').text = str(valve[prop_name])
            else:
                ET.SubElement(prop, 'string').text = valve[prop_name]

    return widget

# Function to create an MMCFPThrottleValve widget based on parsed valve info
def create_throttle_valve_widget_xml(valve, widget_id):  # Add max_y as a parameter
    x = valve['x']
    y = valve['y']
    

    widget = ET.Element('widget', {'class': 'MMCFPThrottleValve', 'name': f'throttle_valve_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')

    ET.SubElement(rect, 'x').text = str(round(x + 14))
    ET.SubElement(rect, 'y').text = str(round(y + 13))
    ET.SubElement(rect, 'width').text = str(28)
    ET.SubElement(rect, 'height').text = str(26)

    # Add additional properties
    for prop_name in ['title', 'routing', 'textMessage', 'rotate', 'labelOffsetY', 'enableValveMenu']:
        prop = ET.SubElement(widget, 'property', {'name': prop_name})
        if prop_name == 'textMessage':
            ET.SubElement(prop, 'string').text = ""  # Always set to ""
        elif prop_name in valve:
            if isinstance(valve[prop_name], bool):
                ET.SubElement(prop, 'bool').text = str(valve[prop_name]).lower()  # Convert bool to lowercase string
            elif isinstance(valve[prop_name], float):
                ET.SubElement(prop, 'double').text = str(valve[prop_name])
            else:
                ET.SubElement(prop, 'string').text = valve[prop_name]

    return widget




# Function to pretty-print and save the XML as .ui file
def save_pretty_xml(tree, output_ui_file):
    # Convert ElementTree to string and pretty-print using minidom
    xml_string = ET.tostring(tree.getroot(), encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

    # Write the pretty-printed XML to the file
    with open(output_ui_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


# Function to generate the .ui file based on parsed lines and valves
def generate_ui_file(parsed_lines : list, parsed_valves : list, output_ui_file : str, scale : float, margin : int, max_x : int, max_y : int):
    # Create the root UI element with the specified version
    ui = ET.Element('ui', {'version': '4.0'})
    
    # Add the class and main QScrollArea widget
    ET.SubElement(ui, 'class').text = 'ScrollArea'
    
    scroll_area = ET.SubElement(ui, 'widget', {'class': 'QScrollArea', 'name': 'ScrollArea'})
    
    # Set properties for the scroll area
    geometry = ET.SubElement(scroll_area, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')
    ET.SubElement(rect, 'x').text = '0'
    ET.SubElement(rect, 'y').text = '0'
    ET.SubElement(rect, 'width').text = str(max_x + margin)
    ET.SubElement(rect, 'height').text = str(max_y + margin)
    
    base_size = ET.SubElement(scroll_area, 'property', {'name': 'baseSize'})
    size = ET.SubElement(base_size, 'size')
    ET.SubElement(size, 'width').text = '1545'
    ET.SubElement(size, 'height').text = '956'
    
    window_title = ET.SubElement(scroll_area, 'property', {'name': 'windowTitle'})
    ET.SubElement(window_title, 'string').text = 'ScrollArea'
    
    style_sheet = ET.SubElement(scroll_area, 'property', {'name': 'styleSheet'})
    ET.SubElement(style_sheet, 'string', {'notr': 'true'}).text = 'background-color: rgb(60, 60, 60);'
    
    frame_shape = ET.SubElement(scroll_area, 'property', {'name': 'frameShape'})
    ET.SubElement(frame_shape, 'enum').text = 'QFrame::NoFrame'
    
    widget_resizable = ET.SubElement(scroll_area, 'property', {'name': 'widgetResizable'})
    ET.SubElement(widget_resizable, 'bool').text = 'true'
    
    # Create the contents widget for the scroll area
    scroll_area_widget_contents = ET.SubElement(scroll_area, 'widget', {'class': 'QWidget', 'name': 'scrollAreaWidgetContents'})
    
    # Set geometry for the contents widget
    contents_geometry = ET.SubElement(scroll_area_widget_contents, 'property', {'name': 'geometry'})
    contents_rect = ET.SubElement(contents_geometry, 'rect')
    ET.SubElement(contents_rect, 'x').text = '0'
    ET.SubElement(contents_rect, 'y').text = '0'
    ET.SubElement(contents_rect, 'width').text = str(max_x + margin)
    ET.SubElement(contents_rect, 'height').text = str(max_y + margin)
    
   
    
    # Add the pipe widgets
    for i, line in enumerate(parsed_lines):
        line_widget = create_pipe_widget_xml(line, i)
        scroll_area_widget_contents.append(line_widget)

    # Add the butterfly valve widgets
    for i, valve in enumerate(parsed_valves):
        valve_widget = create_butterfly_valve_widget_xml(valve, i, scale)
        scroll_area_widget_contents.append(valve_widget)
    
     # Add the throttleValves valve widgets
    for i, valve in enumerate(parsed_thrValves):
        valve_widget = create_throttle_valve_widget_xml(valve, i)
        scroll_area_widget_contents.append(valve_widget)

    # Add the custom widgets section before closing the UI
    custom_widgets = ET.SubElement(ui, 'customwidgets')
    
    custom_widget = ET.SubElement(custom_widgets, 'customwidget')
    ET.SubElement(custom_widget, 'class').text = 'MMCFPPipe'
    ET.SubElement(custom_widget, 'extends').text = 'QWidget'
    ET.SubElement(custom_widget, 'header').text = 'MMCFPPipePlugin.h'
    
    # Save the pretty XML output
    save_pretty_xml(ET.ElementTree(ui), output_ui_file)

# Main execution flow
if __name__ == "__main__":
    # Specify the DXF file to parse and the output UI file
    dxf_file = ["Pipes", "Pipes_negativeCoords", "Pipes_centered", "TankDrainSys", "VacuumSys"][4]
    dxf_file = f"dxf_files/{dxf_file}.dxf"
    output_ui_file = 'output.ui'
    scale = 2
    margin = 50
    
    parsed_lines, parsed_valves, parsed_thrValves, max_x, max_y = parse_dxf_file(dxf_file, scale = scale, margin = margin)
    generate_ui_file(parsed_lines, parsed_valves, output_ui_file, scale, margin, max_x, max_y)

    print(f"Generated {output_ui_file} successfully.")

