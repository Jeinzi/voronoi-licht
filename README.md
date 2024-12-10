# Voronoi Candle Holder
## General Procedure
### FreeCAD
- Create Voronoi pattern with [macro](https://github.com/reox/FreeCAD_macros/blob/master/Voronoi.FCMacro) and cut it into the side panels.
- Install and open "Laser Cut Interlocking" workbench
- Choose side and bottom panels, "Add same parts"
  - Configure laser width: 0.25mm for my machine
- Hide right and left plate, choose the four side faces of the front and back plates to which the interlocking fingers should be added, "Add same faces"
  - 7 fingers, no dog bone holes
- Hide the front and back plates as well and choose the four side faces of the "bottom plate", "Add same faces"
  - 5 fingers, no dog bone holes
- Generate tabs
- Select all parts that should be laser cut, export via Laser Cut Interlocking. In the new window, select the contours and export via "File > Export" as "Flattened SVG".

### Inkscape
FreeCAD exports the Voronoi cells as unconnected, unordered line segments. It might be different for your laser, but in my case the machine cuts one line segment for one cell, then jumps to another cell to cut one line segment there and so one. Because of this, I merge the line segments together in Inkscape:
- Select all line segments of one of the side panels, "Path > Combine". The line segments have now been merged into one path object, but all the end points are still unconnected.
- Switch to the path tool and press CTRL+A to select all nodes, then press "Join selected nodes" to merge overlapping points.

## Path Optimization
In my case, the laser cuts objects mostly in the same order as they are saved in the SVG file.
This means that cutting still takes longer than necessary as the individual Voronoi cells are in random order, e.g one cell in the bottom left, then one cell in the top right and so on. If this is an issue for you, you can use `path-optimization/optimize-paths.py` to sort them in a way that minimizes travel time. First, continue preparing the SVG file in Inkscape:
- "Path > Break Apart" for each of the side panels so that each Voronoi cell is its own path object, all grouped together to form one side.
- In the object properties, rename those groups IDs to side{0..3} so that `optimize-paths.py` can identify them.
- Install the required Python dependencies and execute the script:
```bash
cd path-optimization
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./optimize-paths.py myfile.svg
```
- The script will sort the Voronoi cells in each side panel, make all outlines red (which for my machine means "please cut this") and (for an input file named `myfile.svg`) save the result as `myfile-opt.svg`.
