# setup
import ezdxf
from PyQt5.QtWidgets import QWidget  # Update imports for QScrollArea
from PyQt5.QtCore import QRect
import xml.etree.ElementTree as ET
from xml.dom import minidom  # For pretty-printing the XML

def parse_dxf(dxf_file : str):
    dxf_object = ezdxf.readfile(dxf_file)
    bounds : dict = {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
    
    lines = get_dxf_entities(dxf_file, "LWPOLYLINE")

    for line in lines:

        line["size": {"x": 0, "y": 0, "length": 0, "is_horizontal": True}]





def get_dxf_entities(dxf_file : str, entity_type : str):
    dxf_object = ezdxf.readfile(dxf_file)
    target_entities : list = []

    for entity in dxf_object.entities:
        if entity.dxftype() == entity_type:
            target_entities.append({"entity": entity})
            
    return target_entities



parse_dxf("Pipes.dxf")