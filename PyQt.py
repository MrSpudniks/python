import ezdxf
from PyQt5.QtWidgets import QWidget  # Update imports for QScrollArea
from PyQt5.QtCore import QRect
import xml.etree.ElementTree as ET
from xml.dom import minidom  # For pretty-printing the XML


# Custom MMCFPButterflyValve widget class
class MMCFPButterflyValve(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size = 10  # Default size for the butterfly valve

    def setGeometry(self, x, y, width, height):
        # Call QWidget's setGeometry to set the position and size
        super().setGeometry(QRect(x, y, width, height))


# Custom MMCFPPipe widget class
class MMCFPPipe(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thickness = 5  # Default pipe thickness

    def setGeometry(self, x, y, width, height):
        # Call QWidget's setGeometry to set the position and size
        super().setGeometry(QRect(x, y, width, height))


# Function to parse the DXF file and extract POLYLINE, LINE, and Block Reference entities
def parse_dxf_file(dxf_file, scale_factor=2):
    # Load the DXF file
    doc = ezdxf.readfile(dxf_file)
    lines = []
    butterfly_valves = []
    throttle_valves = []

    min_x, min_y = float('inf'), float('inf')  # Initialize min_x and min_y to very large values
    max_y = float('-inf')  # Initialize max_y to track the highest Y for flipping purposes

    # Process POLYLINE and LWPOLYLINE entities
    for entity in doc.entities:
        if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            points = entity.get_points('xy')  # Get the vertices of the polyline

            # Track the minimum and maximum x, y coordinates
            for x, y in points:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

            # Create segments from polyline vertices
            for i in range(len(points) - 1):
                start_x, start_y = points[i]
                end_x, end_y = points[i + 1]

                length = ((end_x - start_x)**2 + (end_y - start_y)**2)**0.5
                is_horizontal = abs(end_y - start_y) < abs(end_x - start_x)

                lines.append({
                    'start_x': start_x,
                    'start_y': start_y,
                    'end_x': end_x,
                    'end_y': end_y,
                    'length': length,
                    'is_horizontal': is_horizontal
                })

    # Process LINE entities
    for entity in doc.entities:
        if entity.dxftype() == 'LINE':
            start_x, start_y, _ = entity.dxf.start
            end_x, end_y, _ = entity.dxf.end

            delta_x = abs(end_x - start_x)
            delta_y = abs(end_y - start_y)

            # Swap coordinates if the line is "backward" (i.e., if Start X > End X)
            #if start_x > end_x:
            #    start_x, end_x = end_x, start_x
            #    start_y, end_y = end_y, start_y

            # Track the minimum and maximum x, y coordinates
            min_x = min(min_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_y = max(max_y, start_y, end_y)

            length = ((end_x - start_x)**2 + (end_y - start_y)**2)**0.5
            round(start_y, 2)
            round(end_y, 2)
            is_horizontal = start_y == end_y
            
            lines.append({
                'start_x': start_x,
                'start_y': round(start_y, 2),
                'delta_x': delta_x,
                'delta_y': delta_y,
                'end_x': end_x,
                'end_y': round(end_y, 2),
                'length': length,
                'is_horizontal': is_horizontal
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


    # Subtract the minimum x and y values from all coordinates to shift them into the positive quadrant
    # Also apply scaling and flip the Y coordinates by subtracting from max_y
    for line in lines:
        # Adjust length scaling if needed
        line['length'] *= scale_factor
        print(line['start_y'] , line['end_y'])
        print(line['is_horizontal'])
        if line['start_y'] == line['end_y']: # is horizontal
            print("Is horizontal!")
            if line['end_x'] > line['start_x']:
                line['start_x'] = (line['start_x']) * scale_factor
                line['start_y'] = (line['start_y']) * scale_factor
            else:
                # Scale and translate start_x and start_y
                line['start_x'] = (line['end_x']) * scale_factor
                line['start_y'] = ((line['start_y']) * scale_factor)  # <-----   TODO: ADD max_y HERE 
                line['length'] = abs(line['delta_x'])
                print(line['start_y'], line['length'])
            
        else:
            print("Is vertical!")
            if line['start_y'] > line['end_y']: # if line is drawn up->down
                # Scale and translate start_x and start_y
                line['start_x'] = (line['start_x']) * scale_factor
                line['start_y'] = (line['end_y']) - abs(line['delta_y']) * scale_factor
                #print("downwards line: " , line['start_x'], line['start_y'])
            else:
                line['start_x'] = (line['start_x']) * scale_factor
                line['start_y'] = (line['start_y']  - line['length']) * scale_factor  # Flip Y-axis 
                #print("upwards line: " , line['start_x'], line['start_y'])


    for valve in butterfly_valves:
        valve['x'] = (valve['x']) * scale_factor
        valve['y'] = (max_y - valve['y']) * scale_factor  # Correct Y-flip


    for valve in throttle_valves:
        valve['x'] = (valve['x']) * scale_factor
        valve['y'] = (max_y - valve['y']) * -scale_factor  # Correct Y-flip


    return lines, butterfly_valves, throttle_valves



# Function to create an MMCFPPipe widget based on parsed LINE info
def create_pipe_widget_xml(line, widget_id, max_y):  # Add max_y as a parameter
    width = 5
    x = line['start_x']
    y = line['start_y']
    length = line['length']
    is_horizontal = line['is_horizontal']
    
    widget = ET.Element('widget', {'class': 'MMCFPPipe', 'name': f'pipe_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')

    ET.SubElement(rect, 'x').text = str(int(max_y + x))
    ET.SubElement(rect, 'y').text = str(int(max_y + y))  # Adjusted Y-coordinate
    ET.SubElement(rect, 'width').text = str(int(length+((width/2))+1) if is_horizontal else width)
    ET.SubElement(rect, 'height').text = str(5 if is_horizontal else int(length+((width/2)+1)))
    print("Created LINE: ", x, y, max_y)
    return widget



# Function to create an MMCFPButterflyValve widget based on parsed valve info
def create_butterfly_valve_widget_xml(valve, widget_id, max_y):  # Add max_y as a parameter
    x = valve['x']
    y = valve['y']

    widget = ET.Element('widget', {'class': 'MMCFPButterflyValve', 'name': f'butterfly_valve_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')
    
    if valve['rotate'] == 0:
        ET.SubElement(rect, 'x').text = str(int(max_y + x) - 8)
        ET.SubElement(rect, 'y').text = str(int(max_y + y) + 13)  # Adjusted Y-coordinate
    else:
        ET.SubElement(rect, 'x').text = str(int(max_y + x) - 8)
        ET.SubElement(rect, 'y').text = str(int(max_y + y) + 8)  # Adjusted Y-coordinate
    
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
def create_throttle_valve_widget_xml(valve, widget_id, max_y):  # Add max_y as a parameter
    x = valve['x']
    y = valve['y']
    

    widget = ET.Element('widget', {'class': 'MMCFPThrottleValve', 'name': f'throttle_valve_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')

    ET.SubElement(rect, 'x').text = str(int(max_y + x))
    ET.SubElement(rect, 'y').text = str(int(max_y - y))  # Adjusted Y-coordinate
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
def generate_ui_file(parsed_lines, parsed_valves, output_ui_file):
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
    ET.SubElement(rect, 'width').text = '1920'
    ET.SubElement(rect, 'height').text = '999'
    
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
    ET.SubElement(contents_rect, 'width').text = '1920'
    ET.SubElement(contents_rect, 'height').text = '999'
    
   
    
    # Add the pipe widgets
    for i, line in enumerate(parsed_lines):
        line_widget = create_pipe_widget_xml(line, i, 100)
        scroll_area_widget_contents.append(line_widget)

    # Add the butterfly valve widgets
    for i, valve in enumerate(parsed_valves):
        valve_widget = create_butterfly_valve_widget_xml(valve, i, 100)
        scroll_area_widget_contents.append(valve_widget)
    
     # Add the throttleValves valve widgets
    for i, valve in enumerate(parsed_thrValves):
        valve_widget = create_throttle_valve_widget_xml(valve, i, 100)
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
    dxf_file = 'Pipes.dxf'
    output_ui_file = 'output.ui'
    
    parsed_lines, parsed_valves, parsed_thrValves = parse_dxf_file(dxf_file)
    generate_ui_file(parsed_lines, parsed_valves, output_ui_file)

    print(f"Generated {output_ui_file} successfully.")

