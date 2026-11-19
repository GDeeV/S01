import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import s01_enclosure as m

def mesh(shape, tol=0.4):
    v, t = shape.tessellate(tol, 0.3)
    v = np.array([[p.X, p.Y, p.Z] for p in v]); return v[np.array(t)]

light = np.array([0.4, 0.6, 1.0]); light /= np.linalg.norm(light)
def draw(ax, parts, elev, azim, title):
    T, C = [], []
    for shape, rgb, alpha in parts:
        tris = mesh(shape)
        n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.45 + 0.55*np.clip(np.abs(n@light), 0, 1)
        cols = np.clip(np.array(rgb)[None,:]*shade[:,None], 0, 1)
        T.append(tris); C.append(np.c_[cols, np.full(len(cols), alpha)])
    pc = Poly3DCollection(np.concatenate(T), facecolors=np.concatenate(C), linewidths=0, zsort="max")
    ax.add_collection3d(pc)
    ax.set_xlim(-85,85); ax.set_ylim(-118,118); ax.set_zlim(-85,85)
    ax.view_init(elev=elev, azim=azim, vertical_axis="y"); ax.set_axis_off(); ax.set_title(title, fontsize=13)
    ax.set_box_aspect((170,236,170))

TAN=(0.72,0.65,0.48); DARK=(0.22,0.22,0.22); BRASS=(0.78,0.63,0.3)
ext=[(m.front,TAN,1),(m.rear,TAN,1),(m.pad,(0.85,0.33,0.12),1),(m.knob,BRASS,1),(m.ptt,DARK,1),(m.port,BRASS,1),(m.panel,(0.93,0.93,0.9),1)]
inside=[(m.front,TAN,0.18),(m.panel,(0.93,0.93,0.9),1),(m.board,(0.25,0.45,0.25),1),(m.module,DARK,1)]+[(c,(0.3,0.5,0.3),1) for c in m.cells]+[(m.knob,BRASS,1),(m.port,BRASS,1)]
fig=plt.figure(figsize=(16,9))
draw(fig.add_subplot(131,projection="3d"),ext,15,-30,"Front")
draw(fig.add_subplot(132,projection="3d"),[(m.front,TAN,1),(m.rear,TAN,1),(m.knob,BRASS,1),(m.port,BRASS,1),(m.ptt,DARK,1)],15,150,"Rear (battery door opening)")
draw(fig.add_subplot(133,projection="3d"),inside,15,210,"Internals, rear removed")
plt.tight_layout(); plt.savefig("s01_preview.png",dpi=110)
