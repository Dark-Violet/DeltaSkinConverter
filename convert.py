import easygui
import json
import PIL
import re
import shutil
from zipfile import ZipFile
from pathlib import Path
from tempfile import TemporaryDirectory

# User selects the .gbaskin or .gbcskin file
skinpath = Path(easygui.fileopenbox("Select the skin file you wish to convert", title="Skin Selection", default="*.gbcskin;*.gbaskin", filetypes=[["*.gbcskin", "*.gbaskin", "GBA4iOS Skins"], ["*.*", "All files"]]))

# Unzip the files into tempfile.TemporaryDirectory
oldskin = ZipFile(skinpath, "r")
tempdir = TemporaryDirectory()
temppath = Path(tempdir.name)
if "__MACOSX/" in oldskin.namelist(): # if the zip contains the hidden MACOSX metadata, extract only relevant parts, delete the rest
    # Extract the "Default" files
    for file in oldskin.namelist():
        if file.startswith("Default"):
            oldskin.extract(file, path=temppath)
    # Copy the files into the main directory and delete the "Default" folder
    baddir = temppath.joinpath("Default")
    for file in baddir.iterdir():
        if "DS_Store" not in str(file):
            file.replace(temppath.joinpath(file.name))
    shutil.rmtree(baddir)
else:
    oldskin.extractall(path=temppath)

# Convert the info.json file
info = {}
with open(temppath.joinpath("info.json"), "r") as file:
    info = json.load(file)
system = re.findall("\.([a-zA-Z]{3})", str(skinpath))[0].lower()
if system != "gba" and system != "gbc":
    while system != "gba" or system != "gbc":
        system = input("Enter system format (gba or gbc): ").lower()

deltainfo = {
    "name" : info["name"],
    "identifier" : info["identifier"],
    "gameTypeIdentifier" : "com.rileytestut.delta.game." + system,
    "debug" : info.get("debug", False),
    "representations": {}
}
repr_dict = {}
standard = {}
device = {}
for representation in ["iPhone", "iPad"]:
    for orientation in ["portrait", "landscape"]:
        if orientation not in info.keys() or representation not in info[orientation]["layouts"].keys():
            continue
        mapping = info[orientation]

        # Prefer large/widescreen mappings if possible
        # This is because the normal iPhone size is too small, but portait on some skins
        # should still work on the iPhone 8 sized devices
        repr = representation
        if repr + " Widescreen" in mapping["layouts"].keys():
            repr += " Widescreen"
        elif repr + " Retina" in mapping["layouts"].keys():
            repr += " Retina"

        # Assets
        maximg = mapping["assets"].get(repr)

        assets = {
            "small": maximg,
            "medium": maximg,
            "large": maximg
        }

        # Items
        items = []
        extendedEdges = {}
        screens = []
        for key, item in mapping["layouts"][repr].items():
            if key == "extendedEdges":
                extendedEdges = item
                continue
            elif key == "screen":
                screens = [{
                    "outputFrame": item["screen"]
                }]
                continue
            elif key == "dpad":
                newitem = {
                    "inputs" : {
                    "up" : "up",
                    "down" : "down",
                    "left" : "left",
                    "right" : "right"
                    }
                }
            elif key == "ab":
                newitem = {
                    "inputs": ["a", "b"]
                }
            else:
                newitem = {
                    "inputs": [key]
                }

            newitem["frame"] = {
                "x" : item["x"],
                "y" : item["y"],
                "width" : item["width"],
                "height" : item["width"]
            }
            if "extendedEdges" in item.keys():
                newitem["extendedEdges"] = item["extendedEdges"]
            items.append(newitem)

        # MappingSize - find the width and height of image and divide by 2
        width = height = 0
        with PIL.Image.open(temppath.joinpath(maximg)) as image:
            (width, height) = image.size
        mappingSize = {
            "width" : round(width / 2),
            "height" : round(height / 2)
        }

        orient = {
            "assets": assets,
            "items": items,
            "mappingSize": mappingSize,
            "extendedEdges": extendedEdges,
            "translucent": mapping.get("translucent", False)
        }
        if screens:
            orient["screens"] = screens
        # Hard-coded for standard size only since gba4ios didn't support X-series
        standard[orientation] = orient
        device["standard"] = standard
        repr_dict[representation.lower()] = device
        deltainfo["representations"] = repr_dict

with open(temppath.joinpath("info.json"), "w") as file:
    json.dump(deltainfo, file, indent=2)

# Zip all files into a new .deltaskin
deltaskin = ZipFile(re.sub("\..*$", ".deltaskin", str(skinpath)), "w")
for file in temppath.iterdir():
    deltaskin.write(file, file.name)
deltaskin.close()
