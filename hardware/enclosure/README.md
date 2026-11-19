# S-01 enclosure: starter CAD model

A parametric starting point, not a finished design. It lays out the main parts
at real sizes so you can see what fits, then refine the shape in Onshape or FreeCAD.

## Files
- `s01_enclosure.py`: the model. Every dimension is a named parameter at the top.
- `check.py`: checks that placeholder parts don't collide with the housing.
- `render.py`: writes `s01_preview.png`, quick matplotlib renders.
- `s01_preview.png`: the renders.

Running the model generates `s01_assembly.step` (housing plus named, colored
placeholder parts) and `s01_front.stl` / `s01_rear.stl` (housing halves for a
test print). These are build outputs and are not committed.

## Change it
    pip install build123d matplotlib
    python s01_enclosure.py
    python check.py
    python render.py

Edit a number (say `D = 34.0` for depth), re-run, re-import the STEP file.

## Before trusting any dimension
Component sizes are approximate. Check the e-paper panel, compute module, carrier
board and connectors against their datasheets. Tolerances, gasket channel, button
mechanisms, antenna windows and heat paths are not modeled yet.
