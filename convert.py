import easygui
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
    for file in oldskin.namelist():
        if file.startswith("Default"):
            oldskin.extract(file, path=temppath)
    baddir = Path(str(temppath) + "/Default")
    for file in baddir.iterdir():
        if "DS_Store" not in str(file):
            dest = Path(str(temppath) + "/" + file.name)
            file.replace(dest)
    shutil.rmtree(baddir)
else:
    oldskin.extractall(path=temppath)

# Convert the info.json file


# Zip all files into a new .deltaskin
deltaskin = ZipFile(re.sub("[^\.]*$", "deltaskin", str(skinpath)), "w")
for file in temppath.iterdir():
    deltaskin.write(file, file.name)
deltaskin.close()
