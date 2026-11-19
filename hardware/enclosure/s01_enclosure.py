"""
S-01 enclosure: parametric starting model (build123d).

Run:   pip install build123d
       python s01_enclosure.py
Output: s01_assembly.step  (open in Onshape, FreeCAD or Fusion)
        s01_front.stl, s01_rear.stl  (printable housing halves)

Axes: X = width, Y = height (top of device is +Y), Z = depth (screen faces +Z).
All units in millimeters. Change the numbers below and re-run.

Component sizes are approximate placeholders. Check each one against the
manufacturer's datasheet before designing anything that has to fit.
"""
from build123d import (Axis, Box, Color, Compound, Cylinder, Keep, Plane,
                       Pos, Rot, chamfer, export_step, export_stl, split)

# ---------------------------------------------------------------- parameters
W, H, D = 114.0, 216.0, 34.0      # outer body: width, height, depth
WALL = 2.5                        # housing wall thickness
EDGE = 4.0                        # chamfer on every outer edge (the faceted look)
SPLIT_Z = -5.0                    # where front and rear housings meet

# 6" HD e-paper panel (1448x1072), portrait. VERIFY against Waveshare drawing.
PANEL_W, PANEL_H, PANEL_T = 101.8, 138.4, 1.2
ACTIVE_W, ACTIVE_H = 90.6, 122.4  # visible area; the window is cut slightly larger
WINDOW_MARGIN = 2.0
TOP_MARGIN = 15.0                 # space above the screen for the knob

# Controls
PAD_D = 34.0                      # 4-way rocker diameter
PAD_Y_GAP = 28.0                  # screen bottom edge to pad center
SIDE_BTN = (18.0, 12.0)           # BACK and HOME button size
SIDE_BTN_X = 38.0
KNOB_D, KNOB_H, KNOB_X = 16.0, 9.0, 30.0
PTT_LEN, PTT_W = 62.0, 11.0       # push-to-talk bar on the left side
PTT_Y = 30.0
PORT_D = 15.0                     # sealed round data/power port, bottom edge

# Battery bay: 3 x 18650, lying across the device
CELL_D, CELL_L, N_CELLS = 18.6, 65.0, 3
CELL_GAP = 1.0
BAY_Y = -62.0                     # center of the battery bay

# Electronics placeholders
BOARD = (90.0, 62.0, 1.6)         # carrier board (for a Pi CM5 or similar)
MODULE = (55.0, 40.0, 4.7)        # compute module (Raspberry Pi CM5 size)
BOARD_Y = 40.0

SCREW_D, BOSS_D = 2.5, 6.5        # M2.5 screws in corner bosses

# ---------------------------------------------------------------- derived layout
screen_y = H / 2 - TOP_MARGIN - PANEL_H / 2
pad_y = screen_y - PANEL_H / 2 - PAD_Y_GAP
front_z = D / 2
rear_z = -D / 2

# ---------------------------------------------------------------- body
body = Box(W, H, D)
body = chamfer(body.edges(), EDGE)

# Faceted armor plate over the keypad area, adds the layered-plate look
plate = Box(W - 2 * EDGE - 6, 62, 3)
plate = chamfer(plate.edges().group_by(Axis.Z)[-1], 2.4)
plate = Pos(0, pad_y - 4, front_z + 1.5 - 0.01) * plate
body = body + plate

# Raised bezel ring around the screen window
bezel_outer = Box(ACTIVE_W + 2 * WINDOW_MARGIN + 12, ACTIVE_H + 2 * WINDOW_MARGIN + 12, 2.5)
bezel_outer = chamfer(bezel_outer.edges().group_by(Axis.Z)[-1], 2.0)
body = body + Pos(0, screen_y, front_z + 1.25 - 0.01) * bezel_outer

# Hollow it out, then split into front and rear housings
inner = chamfer(Box(W - 2 * WALL, H - 2 * WALL, D - 2 * WALL).edges(), max(EDGE - WALL, 0.5))
housing = body - inner

# ---------------------------------------------------------------- cutouts
cuts = []
cuts.append(Pos(0, screen_y, front_z) *
            Box(ACTIVE_W + 2 * WINDOW_MARGIN, ACTIVE_H + 2 * WINDOW_MARGIN, 12))
cuts.append(Pos(0, pad_y, front_z) * Cylinder(PAD_D / 2, 12))
for x in (-SIDE_BTN_X, SIDE_BTN_X):
    cuts.append(Pos(x, pad_y, front_z) * Box(*SIDE_BTN, 12))
# speaker grille: grid of 1.6 mm holes below the keypad
for i in range(-5, 6):
    for j in range(2):
        cuts.append(Pos(i * 4.2, pad_y - 26 - j * 4.2, front_z) * Cylinder(0.8, 12))
cuts.append(Pos(-W / 2, PTT_Y, 0) * Box(12, PTT_LEN, PTT_W))           # PTT slot
cuts.append(Pos(KNOB_X, H / 2, 0) * Rot(90, 0, 0) * Cylinder(3.5, 12))  # knob shaft
cuts.append(Pos(0, -H / 2, 0) * Rot(90, 0, 0) * Cylinder(PORT_D / 2 - 2, 12))
bay_w = N_CELLS * (CELL_D + CELL_GAP) + 4
cuts.append(Pos(0, BAY_Y, rear_z) * Box(CELL_L + 6, bay_w, 12))       # battery door
for c in cuts:
    housing = housing - c

# ---------------------------------------------------------------- screw bosses
bx, by = W / 2 - WALL - BOSS_D / 2 - 1.5, H / 2 - WALL - BOSS_D / 2 - 6
boss_len = D - 2 * WALL
for x in (-bx, bx):
    for y in (-by, by):
        boss = Pos(x, y, 0) * Cylinder(BOSS_D / 2, boss_len)
        housing = (housing + boss) - Pos(x, y, 0) * Cylinder(SCREW_D / 2, boss_len + 1)

front = split(housing, Plane.XY.offset(SPLIT_Z), keep=Keep.TOP)
rear = split(housing, Plane.XY.offset(SPLIT_Z), keep=Keep.BOTTOM)

# ---------------------------------------------------------------- placeholders
panel = Pos(0, screen_y, front_z - WALL - PANEL_T / 2 - 0.3) * Box(PANEL_W, PANEL_H, PANEL_T)
board_z = front_z - WALL - PANEL_T - 4 - BOARD[2] / 2
board = Pos(0, BOARD_Y, board_z) * Box(*BOARD)
module = Pos(0, BOARD_Y, board_z - BOARD[2] / 2 - MODULE[2] / 2) * Box(*MODULE)
cells = []
for i in range(N_CELLS):
    y = BAY_Y + (i - (N_CELLS - 1) / 2) * (CELL_D + CELL_GAP)
    cells.append(Pos(0, y, rear_z + WALL + CELL_D / 2 + 0.5) * Rot(0, 90, 0) *
                 Cylinder(CELL_D / 2, CELL_L))
knob = Pos(KNOB_X, H / 2 + KNOB_H / 2, 0) * Rot(90, 0, 0) * Cylinder(KNOB_D / 2, KNOB_H)
pad = Pos(0, pad_y, front_z + 1.2) * Cylinder(PAD_D / 2 - 1, 3)
ptt = Pos(-W / 2 - 0.8, PTT_Y, 0) * Box(4, PTT_LEN - 2, PTT_W - 2)
port = Pos(0, -H / 2 - 4, 0) * Rot(90, 0, 0) * Cylinder(PORT_D / 2, 8)


def part(shape, name, rgb):
    shape.label, shape.color = name, Color(*rgb)
    return shape


TAN, DARK, ORANGE, GREEN, BRASS = (0.72, 0.65, 0.48), (0.2, 0.2, 0.2), (0.85, 0.33, 0.12), \
    (0.25, 0.45, 0.25), (0.78, 0.63, 0.3)
assembly = Compound(label="S-01", children=[
    part(front, "front_housing", TAN),
    part(rear, "rear_housing", TAN),
    part(panel, "eink_panel", (0.9, 0.9, 0.88)),
    part(board, "carrier_board", GREEN),
    part(module, "compute_module", DARK),
    *[part(c, f"cell_18650_{i + 1}", (0.3, 0.5, 0.3)) for i, c in enumerate(cells)],
    part(knob, "knob", BRASS),
    part(pad, "dpad", DARK),
    part(ptt, "ptt_bar", DARK),
    part(port, "port", BRASS),
])

if __name__ == "__main__":
    export_step(assembly, "s01_assembly.step")
    export_stl(front, "s01_front.stl")
    export_stl(rear, "s01_rear.stl")
    bb = assembly.bounding_box()
    print(f"Overall size incl. knob and port: {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm")
    print(f"Housing volume: {(front.volume + rear.volume) / 1000:.1f} cm^3")
