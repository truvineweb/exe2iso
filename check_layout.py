import os 
root = r"iso_root" 
for dirpath, dirnames, filenames in os.walk(root): 
    print(dirpath, "->", filenames) 
