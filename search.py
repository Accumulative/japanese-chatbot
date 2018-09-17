
import xml.etree.ElementTree as ET
tree = ET.parse('JMdict_e.xml')
root = tree.getroot()
from helper import is_kata

class Results(object):
    def __init__(self, definitions, readings, types):
        self.definitions = definitions
        self.readings = readings
        self.types = types


def search(query):
    b_is_kata = is_kata(query)
    element = root.find(".//{}/[{}='{}']...".format("r_ele" if b_is_kata else "k_ele", "reb" if b_is_kata else "keb", query))

    if element is not None:
        definitions = []
        for i in element.findall("sense//gloss"):
            definitions.append(i.text)
        
        readings = []
        for i in element.findall("k_ele//keb"):
            readings.append(i.text)
        for i in element.findall("r_ele//reb"):
            readings.append(i.text)

        types = []
        for i in element.findall("sense//pos"):
            if "exp" not in i.text:
                types.append(i.text.replace(";",""))
        if len(types) == 0:
            types = ["exp"]
        return Results(definitions, readings, types)
    return None


def test():
    print(search("違う"))
    print(search("出来る"))
    print(search("こんにちは"))
    print(search("携帯"))


