import os 
for root, dirs, files in os.walk(r"iso_root"): 
    print(root, "->", files) 
