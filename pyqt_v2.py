import ezdxf
from PyQt5.QtWidgets import QWidget  # Update imports for QScrollArea
from PyQt5.QtCore import QRect
import xml.etree.ElementTree as ET
from xml.dom import minidom  # For pretty-printing the XML

class MMCFPButterflyValve(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.size = 10

    def setGeometry(self, x, y, width, height):
        
        super().setGeometry(QRect(x, y, width, height))



class MMCFPPipe(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.thickness = 5

    def setGeometry(self, x, y, width, height):
        
        super().setGeometry(QRect(x, y, width, height))



def parse_dxf(dxf_file : str, margin : dict = {"x": 0, "y": 0}):

    dxf_object = ezdxf.readfile(dxf_file)

    lines = get_dxf_entities(dxf_file, "LWPOLYLINE")

    # line attribute setup
    for line in lines:

        line["points"] = []
        for x, y in line["entity"].get_points("xy"):

            line["points"].append({"x": round(x), "y": round(y)})

        min_x = line["points"][0]["x"]
        max_x = line["points"][0]["x"]
        min_y = line["points"][0]["y"]
        max_y = line["points"][0]["y"]

        for point in line["points"]:

            if point["x"] < min_x:

                min_x = point["x"]

            elif point["x"] > max_x:

                max_x = point["x"]
            
            if point["y"] < min_y:

                min_y = point["y"]

            elif point["y"] > max_y:

                max_y = point["y"]
            
        line["points"] = [{"x": min_x, "y": max_y}, {"x": max_x, "y": min_y}]

        if min_x == max_x:

            line["dimensions"] = {"x": min_x, "y": max_y, "height": max_y - min_y, "width": 5}

        else:

            line["dimensions"] = {"x": min_x, "y": max_y, "height": 5, "width": max_x - min_x}

    # set bounds, and coordinate translation
    dxf_bounds : dict = {"min_x": lines[0]["points"][0]["x"], "max_x": lines[0]["points"][0]["x"], "min_y": lines[0]["points"][0]["y"], "max_y": lines[0]["points"][0]["y"]} # set dxf_bounds to the first point of the first line
    qt_bounds : dict = {"x": dxf_bounds["max_x"], "y": dxf_bounds["min_y"]}

    for line in lines:

        for point in line["points"]:

            if point["x"] > dxf_bounds["max_x"]:

                dxf_bounds["max_x"] = point["x"]

            elif point["x"] < dxf_bounds["min_x"]:

                dxf_bounds["min_x"] = point["x"]
            
            if point["y"] > dxf_bounds["max_y"]:

                dxf_bounds["max_y"] = point["y"]

            elif point["y"] < dxf_bounds["min_y"]:

                dxf_bounds["min_y"] = point["y"]

        line["dimensions"]

    

    offset : dict = {"x": 0, "y": 0}





    print(dxf_bounds, lines)

    elements : dict[list] = {}
    elements["lines"] = lines # + valves and stuff

    return elements



def get_dxf_entities(dxf_file : str, entity_type : str):

    dxf_object = ezdxf.readfile(dxf_file)
    target_entities : list[dict] = []

    for entity in dxf_object.entities:

        if entity.dxftype() == entity_type:

            target_entities.append({"entity": entity})
            
    return target_entities



def create_pipe_widget_xml(line, widget_id):
    
    widget = ET.Element('widget', {'class': 'MMCFPPipe', 'name': f'pipe_{widget_id}'})
    
    geometry = ET.SubElement(widget, 'property', {'name': 'geometry'})
    rect = ET.SubElement(geometry, 'rect')

    ET.SubElement(rect, 'x').text = line["dimensions"]["x"]
    ET.SubElement(rect, 'y').text = line["dimensions"]["y"]
    ET.SubElement(rect, 'width').text = line["dimensions"]["width"]
    ET.SubElement(rect, 'height').text = line["dimensions"]["height"]
    return widget


# Function to pretty-print and save the XML as .ui file
def save_pretty_xml(tree, output_ui_file):
    # Convert ElementTree to string and pretty-print using minidom
    xml_string = ET.tostring(tree, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="    ")

    # Write the pretty-printed XML to the file
    with open(output_ui_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


# Function to generate the .ui file based on parsed lines and valves
def generate_ui_file(elements, output_ui_file):
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
    for i, line in enumerate(elements["lines"]):
        line_widget = create_pipe_widget_xml(line, i)
        scroll_area_widget_contents.append(line_widget)

    # Add the butterfly valve widgets
    # for i, valve in enumerate(parsed_valves):
    #     valve_widget = create_butterfly_valve_widget_xml(valve, i)
    #     scroll_area_widget_contents.append(valve_widget)
    
    # Add the throttleValves valve widgets
    # for i, valve in enumerate(parsed_thrValves):
    #     valve_widget = create_throttle_valve_widget_xml(valve, i)
    #     scroll_area_widget_contents.append(valve_widget)

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
    
    elements = parse_dxf(dxf_file)
    generate_ui_file(elements, output_ui_file)

    # print(f"Generated {output_ui_file} successfully.")