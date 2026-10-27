"""Trace the preloader figure into public/loader.svg: python -I trace_loader.py <png>
One centreline per drawn stroke: region edges (figure / dress / hair) plus the thin ink lines themselves,
skeletonised and chained into smooth strands that each run bottom -> top."""
import sys
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d
from skimage.morphology import skeletonize

src = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
S = 2.0  # trace at 2x so the centreline sits between source pixels
big = cv2.GaussianBlur(cv2.resize(src, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), (0, 0), 1.2)

# Background = the flat grey connected to the border; everything else is the figure
bg = np.zeros((big.shape[0] + 2, big.shape[1] + 2), np.uint8)
cv2.floodFill(big.copy(), bg, (0, 0), 0, loDiff=10, upDiff=10, flags=4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8))
figure = np.where(bg[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)
n, lab, stats, _ = cv2.connectedComponentsWithStats(figure)
figure = np.where(lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
figure = cv2.morphologyEx(figure, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

dark = np.where(big < 128, 255, 0).astype(np.uint8) & figure
light = figure & ~dark
disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))  # strokes thinner than ~5 source px count as lines
dark_body = cv2.morphologyEx(dark, cv2.MORPH_OPEN, disk)
thin = (dark & ~dark_body) | (light & ~cv2.morphologyEx(light, cv2.MORPH_OPEN, disk))  # ink lines + white lines in the hair
regions = cv2.morphologyEx(dark_body, cv2.MORPH_CLOSE, disk) & figure  # dress / hair masses without the thin white gaps
grad = lambda m: cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
ink = grad(figure) | grad(regions) | thin
# Coincident edges (dress edge = figure edge) merge into one line before thinning
ink = cv2.dilate(ink, np.ones((3, 3), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(~ink, connectivity=4)
ink[np.isin(lab, 1 + np.nonzero(stats[1:, cv2.CC_STAT_AREA] < 120)[0])] = 255  # close pinholes: they thin into tiny loops
sk = skeletonize(ink > 0)
n, lab, stats, _ = cv2.connectedComponentsWithStats(sk.astype(np.uint8), connectivity=8)
sk = np.isin(lab, 1 + np.nonzero(stats[1:, cv2.CC_STAT_AREA] >= 20)[0])

# Chain skeleton pixels into polylines, broken at junctions
pts = set(zip(*np.nonzero(sk)))
OFF = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
nb = {p: [(p[0] + a, p[1] + b) for a, b in OFF if (p[0] + a, p[1] + b) in pts] for p in pts}
nodes = {p for p, q in nb.items() if len(q) != 2}
seen, chains = set(), []


def walk(a, b):
    chain = [a, b]
    seen.add(frozenset((a, b)))
    while chain[-1] not in nodes:
        nxt = [q for q in nb[chain[-1]] if frozenset((chain[-1], q)) not in seen]
        if not nxt:
            break
        seen.add(frozenset((chain[-1], nxt[0])))
        chain.append(nxt[0])
    return chain


for a in nodes:
    for b in nb[a]:
        if frozenset((a, b)) not in seen:
            chains.append((walk(a, b), False))
for a in pts:  # leftovers are closed loops
    for b in nb[a]:
        if frozenset((a, b)) not in seen:
            c = walk(a, b)
            chains.append((c, c[-1] == a or a in nb[c[-1]]))


def open_spline(p):
    """Open Catmull-Rom through points -> cubic Béziers (ends duplicated)."""
    q = np.vstack([p[:1], p, p[-1:]])
    segs = [f"M{p[0][0]:.2f} {p[0][1]:.2f}"]
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        segs.append(f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    return "".join(segs)


out = []
for c, closed in chains:
    end_free = sum(len(nb[c[i]]) == 1 for i in (0, -1))
    if len(c) < 8 or (end_free and len(c) < 16):  # skeleton spurs
        continue
    p = np.array([(x, y) for y, x in c], float)
    p = gaussian_filter1d(p, 2.5, axis=0, mode="wrap" if closed else "nearest")  # pixel staircase -> smooth curve
    if not closed:
        p[0], p[-1] = [(x, y) for y, x in (c[0], c[-1])]  # keep junction ends attached
    b = int(np.argmax(p[:, 1]))
    if closed:  # two halves from the lowest to the highest point
        p = np.roll(p, -b, axis=0)
        t = int(np.argmin(p[:, 1]))
        halves = [p[:t + 1], np.vstack([p[:1], p[t:][::-1]])]
    else:  # two halves from the lowest point out to each end
        halves = [p[:b + 1][::-1], p[b:]]
    for h in halves:
        if len(h) < 3:
            continue
        h = cv2.approxPolyDP(h.astype(np.float32).reshape(-1, 1, 2), 0.5, False).reshape(-1, 2) / S
        if len(h) >= 2:
            out.append((open_spline(h), h[:, 1].max(), h[:, 1].min()))

ys, xs = np.nonzero(figure)
x0, y0, x1, y1 = xs.min() / S, ys.min() / S, xs.max() / S, ys.max() / S
lines = "".join(f'<path data-y0="{yb:.1f}" data-y1="{yt:.1f}" d="{d}"/>' for d, yb, yt in out)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0 - 2:.1f} {y0 - 2:.1f} {x1 - x0 + 4:.1f} {y1 - y0 + 4:.1f}">'
       f'<g id="strands">{lines}</g></svg>')
open("public/loader.svg", "w").write(svg)
cv2.imwrite(sys.argv[2] if len(sys.argv) > 2 else "skeleton.png", (~sk * 255).astype(np.uint8))
print("strands", len(out), "chars", len(svg))
