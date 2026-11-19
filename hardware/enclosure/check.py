import s01_enclosure as m
housing = m.front + m.rear
for name, s in [("panel", m.panel), ("board", m.board), ("module", m.module)] + [(f"cell{i}", c) for i, c in enumerate(m.cells)]:
    v = (housing & s).volume
    print(f"{name:8s} overlap with housing: {v:.1f} mm^3")
for i,c in enumerate(m.cells):
    for n,s in [("board",m.board),("module",m.module),("panel",m.panel)]:
        v=(c & s).volume
        if v>0.01: print("cell",i,"hits",n,v)
