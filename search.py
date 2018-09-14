
import xml.etree.ElementTree as ET
tree = ET.parse('JMdict_e.xml')
root = tree.getroot()

query = "こんにちは"
for i in root.findall(f".//r_ele/[reb='{query}']..//gloss"):
    print(i.text)