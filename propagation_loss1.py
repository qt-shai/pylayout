import math
import gdstk
import gdsfactory as gf

# =========================
# Parameters (edit here)
# =========================
LAYER = (1, 0)

WG_WIDTH = 0.25          # um
CLEARANCE = 5.0          # um per side (outer width = WG_WIDTH + 2*CLEARANCE)
RADIUS = 35.0            # um (rounded corners)

# Inverted-P geometry
BODY_HALF_W = 125.0      # um (right extent)
NECK_HALF_W = 20.0       # um (top ends at +/- NECK_HALF_W)
BODY_H = 50.0           # um
NECK_H = 140.0           # um

# Supports
SUPPORT_SPACING = 20.0   # um
SUPPORT_LENGTH = 5.0     # um
SUPPORT_TIP_WIDTH = 0.6  # um
SUPPORT_SHIFT = 0.25     # um (left/right nudges)

# Small biases to avoid boolean “hairline gaps”
BIAS_H_Y = 0.10          # um for horizontal-segment up/down
BIAS_V_Y = 0.13          # um for vertical-segment up/down

# Extra supports placement
EXTRA_STEP = 20.0        # um
EXTRA_TOP_Y_ADJUST = -3.125  # keep your current tweak
RIGHT_EXTRA_BASE_SHIFT = 15.0

# Grating coupler
GC_TAPER_L = 12.0        # um
GC_WIDE_W = 0.3          # um
GC_N = 16
GC_PERIOD = 0.484        # um
GC_FILL = 0.623
GC_BRIDGE = 0.075        # um (75 nm bridge)

# GC cap (taper above the teeth)
GC_CAP_H = 2.0           # um
GC_CAP_W1 = 5.0          # um (top width)
GC_CAP_SHIFT_HALF_PITCH = -0.5  # *GC_PERIOD (your current choice)

INNER_INSET = 20.0  # um (distance between outer and inner loop walls)

# -------------------------
# Helpers
# -------------------------
def _left_normal(dx, dy):
    # returns a unit left normal for axis-aligned segments
    if dx > 0:   # moving +x
        return (0.0, 1.0)
    if dx < 0:   # moving -x
        return (0.0, -1.0)
    if dy > 0:   # moving +y
        return (-1.0, 0.0)
    if dy < 0:   # moving -y
        return (1.0, 0.0)
    return (0.0, 0.0)

def _shift_endpoint(p_end, p_in, off):
    # p_end = port point, p_in = next point INTO the device
    dx = p_in[0] - p_end[0]
    dy = p_in[1] - p_end[1]
    nx, ny = _left_normal(dx, dy)
    return (p_end[0] + nx * off, p_end[1] + ny * off)

def _offset_path(pts, offset):
    """Return a new point list offset to the left of the path by 'offset' µm."""
    fp = gdstk.FlexPath(pts, 0.001, bend_radius=RADIUS)
    offset_polys = fp.offsets(offset)  # positional arg only
    return offset_polys[0].points

def _poly_to_gf(component: gf.Component, polys, layer=LAYER):
    for p in polys:
        component.add_polygon(p.points, layer=layer)

def _union(polys):
    if not polys:
        return []
    return gdstk.boolean(polys, polys, "or")

def _sub(a, b):
    if not a:
        return []
    if not b:
        return a
    return gdstk.boolean(a, b, "not")

def _rotate_translate(polys, angle_deg, dx, dy, origin=(0, 0)):
    out = []
    ang = math.radians(angle_deg)
    ox, oy = origin
    for p in polys:
        q = p.copy()
        q.rotate(ang, (ox, oy))
        q.translate(dx, dy)
        out.append(q)
    return out

# -------------------------
# Geometry
# -------------------------
def _bottle_pts(inset=0.0):
    """
    Inverted-P open path.
    inset > 0 shrinks the loop inward (NOT an offset curve), keeping bend_radius identical.
    """
    # original vertical extents
    y_bottom = 0.0
    y_body_top = y_bottom + BODY_H
    y_neck_base = y_body_top + 2 * RADIUS
    y_top0 = y_neck_base + NECK_H

    # inset affects the loop walls
    x_left_top  = -NECK_HALF_W + inset
    x_right_top = +NECK_HALF_W
    x_right     =  BODY_HALF_W - inset

    # keep corners roundable
    y_low = y_bottom + RADIUS + inset
    y_top = y_top0

    pts = [
        (x_left_top,  y_top),   # top-left end
        (x_left_top,  y_low),   # DOWN
        (x_right,     y_low),   # RIGHT
        (x_right,     y_top-inset+35),   # UP
        (x_right_top+(inset-15)*1.6, y_top-inset+35),   # LEFT to top-right end (open)
    ]
    return pts, y_top

def _flexpath_polys(pts, width, offset=0.0, bend_radius=RADIUS):
    fp = gdstk.FlexPath(
        pts,
        width,
        offset=offset,
        bend_radius=bend_radius,
        layer=LAYER[0],
        datatype=LAYER[1],
    )
    return fp.to_polygons()

def _support_trapezoid(center, direction, base_w, tip_w, length):
    """
    One-sided wedge: narrow at attachment (tip_w), wide outward (base_w).
    NOTE: up/down and left/right are intentionally asymmetric (as in your current file).
    """
    x, y = center
    bw = base_w
    tw = tip_w
    L = length

    w2b = bw / 2  # outward end
    w2t = tw / 2  # attachment end

    if direction == "up":
        y0 = y + w2b
        y1 = y0 + L
        return gdstk.Polygon(
            [(x - w2t, y0), (x + w2t, y0), (x + w2b, y1), (x - w2b, y1)],
            layer=LAYER[0], datatype=LAYER[1],
        )

    if direction == "down":
        y0 = y - w2b
        y1 = y0 - L
        return gdstk.Polygon(
            [(x - w2t, y0), (x + w2t, y0), (x + w2b, y1), (x - w2b, y1)],
            layer=LAYER[0], datatype=LAYER[1],
        )

    # (kept exactly as in your current code)
    if direction == "right":
        x0 = x + w2b
        x1 = x0 + L
        return gdstk.Polygon(
            [(x0, y - w2b), (x0, y + w2b), (x1, y + w2t), (x1, y - w2t)],
            layer=LAYER[0], datatype=LAYER[1],
        )

    if direction == "left":
        x0 = x - w2b
        x1 = x0 - L
        return gdstk.Polygon(
            [(x0, y - w2b), (x0, y + w2b), (x1, y + w2t), (x1, y - w2t)],
            layer=LAYER[0], datatype=LAYER[1],
        )

    raise ValueError("direction must be one of: up/down/left/right")


def _supports_on_straights(pts, is_inner = False):
    H_START_SHIFT = -45
    V_START_SHIFT = 39

    # find top and bottom horizontal y-levels
    h_ys = [y0 for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]) if y0 == y1 and x0 != x1]
    y_top_h = max(h_ys) if h_ys else None
    y_bot_h = min(h_ys) if h_ys else None

    margin = RADIUS + SUPPORT_LENGTH - 1.6
    inner = []
    outer = []

    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        dx = x1 - x0
        dy = y1 - y0

        # horizontal segment
        if dy == 0 and dx != 0:
            xa, xb = (x0, x1) if x0 < x1 else (x1, x0)
            seg_len = xb - xa
            if seg_len <= 1.5 * margin:
                continue

            # classify this horizontal
            is_top = (y0 == y_top_h)
            is_bot = (y0 == y_bot_h)

            # start position (your shift)
            x = xa + margin

            # ---- force one extra support near the top corner ----
            # place one at the right end of the TOP segment (before the bend)
            if is_top:
                x0_force = xa + margin + H_START_SHIFT
                force_dx = 20.0  # um

                for xx in (x0_force, x0_force + force_dx):
                    inner.append(_support_trapezoid((xx + SUPPORT_SHIFT, y0 - BIAS_H_Y), "up",
                                                    SUPPORT_TIP_WIDTH, WG_WIDTH, SUPPORT_LENGTH))
                    inner.append(_support_trapezoid((xx - SUPPORT_SHIFT, y0 + BIAS_H_Y), "down",
                                                    SUPPORT_TIP_WIDTH, WG_WIDTH, SUPPORT_LENGTH))
                    inner.append(_support_trapezoid((xx + SUPPORT_TIP_WIDTH / 2, y0), "left",
                                                    SUPPORT_TIP_WIDTH, WG_WIDTH, SUPPORT_LENGTH*0.7))
                    inner.append(_support_trapezoid((xx - SUPPORT_TIP_WIDTH / 2, y0), "right",
                                                    SUPPORT_TIP_WIDTH, WG_WIDTH, SUPPORT_LENGTH*0.7))

            # regular spaced supports
            while x <= xb - margin:
                inner.append(_support_trapezoid((x + SUPPORT_SHIFT, y0 - BIAS_H_Y), "up", SUPPORT_TIP_WIDTH, WG_WIDTH,
                                                SUPPORT_LENGTH))
                inner.append(_support_trapezoid((x - SUPPORT_SHIFT, y0 + BIAS_H_Y), "down", SUPPORT_TIP_WIDTH, WG_WIDTH,
                                                SUPPORT_LENGTH))
                inner.append(_support_trapezoid((x + SUPPORT_TIP_WIDTH / 2, y0), "left", SUPPORT_TIP_WIDTH, WG_WIDTH,
                                                SUPPORT_LENGTH*0.7))
                inner.append(_support_trapezoid((x - SUPPORT_TIP_WIDTH / 2, y0), "right", SUPPORT_TIP_WIDTH, WG_WIDTH,
                                                SUPPORT_LENGTH*0.7))
                x += SUPPORT_SPACING

        # vertical
        if dx == 0 and dy != 0:
            nx, ny = _left_normal(dx, dy)  # <-- no offset argument
            sx, sy = nx * 0, ny * 0
            x_base = x0 + sx  # y unchanged for vertical offset
            is_left = (x0 < 10)

            ya, yb = (y0, y1) if y0 < y1 else (y1, y0)
            if (yb - ya) <= margin:
                continue

            y = ya + margin
            while y <= yb - margin:
                inner.append(_support_trapezoid((x_base, y - 0.13), "up",   WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH*0.7))
                inner.append(_support_trapezoid((x_base, y + 0.13), "down", WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH*0.7))
                inner.append(_support_trapezoid((x_base, y - SUPPORT_SHIFT), "left",  WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH))
                inner.append(_support_trapezoid((x_base, y + SUPPORT_SHIFT), "right", WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH))
                y += SUPPORT_SPACING

            # ---- force TWO supports on the vertical (20 µm apart) ----
            if is_left:
                # choose shift depending on which trench we’re on
                if not is_inner:  # outer trench
                    y0_force = yb - margin + V_START_SHIFT
                else:  # inner trench
                    y0_force = yb - margin + V_START_SHIFT

                force_dy = 20.0

                for yy in (y0_force, y0_force - force_dy):  # downward direction
                    # clamp to segment range

                    inner.append(
                        _support_trapezoid((x_base, yy - 0.13), "up", WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH*0.7))
                    inner.append(
                        _support_trapezoid((x_base, yy + 0.13), "down", WG_WIDTH, SUPPORT_TIP_WIDTH, SUPPORT_LENGTH*0.7))
                    inner.append(_support_trapezoid((x_base, yy - SUPPORT_SHIFT), "left", WG_WIDTH, SUPPORT_TIP_WIDTH,
                                                    SUPPORT_LENGTH))
                    inner.append(_support_trapezoid((x_base, yy + SUPPORT_SHIFT), "right", WG_WIDTH, SUPPORT_TIP_WIDTH,
                                                    SUPPORT_LENGTH))

    return inner, outer


def _grating_coupler_polys():
    """
    GC local direction is +Y.
    Returns (inner_polys, outer_polys).
    """
    inner = []
    outer = []

    # taper (inner)
    inner.append(
        gdstk.Polygon(
            [
                (-WG_WIDTH / 2, 0.0),
                ( WG_WIDTH / 2, 0.0),
                ( GC_WIDE_W / 2 + GC_BRIDGE, GC_TAPER_L),
                (-GC_WIDE_W / 2 - GC_BRIDGE, GC_TAPER_L),
            ],
            layer=LAYER[0], datatype=LAYER[1],
        )
    )

    # taper (outer clearance)
    outer.append(
        gdstk.Polygon(
            [
                (-(WG_WIDTH + 2 * CLEARANCE) / 2, 0.0),
                ( (WG_WIDTH + 2 * CLEARANCE) / 2, 0.0),
                ( (GC_WIDE_W + 2 * CLEARANCE) / 2, GC_TAPER_L + CLEARANCE),
                (-(GC_WIDE_W + 2 * CLEARANCE) / 2, GC_TAPER_L + CLEARANCE),
            ],
            layer=LAYER[0], datatype=LAYER[1],
        )
    )

    # teeth
    tooth_w = GC_FILL * GC_PERIOD
    y0 = GC_TAPER_L
    y_end = GC_TAPER_L + GC_N * GC_PERIOD

    for i in range(GC_N):
        y_start = y0 + i * GC_PERIOD
        inner.append(gdstk.rectangle(
            (-GC_WIDE_W / 2, y_start),
            ( GC_WIDE_W / 2, y_start + tooth_w),
            layer=LAYER[0], datatype=LAYER[1],
        ))
        outer.append(gdstk.rectangle(
            (-(GC_WIDE_W + 2 * CLEARANCE) / 2, y_start - CLEARANCE * 0.2),
            ( (GC_WIDE_W + 2 * CLEARANCE) / 2, y_start + tooth_w + CLEARANCE * 0.2),
            layer=LAYER[0], datatype=LAYER[1],
        ))

    # 75 nm bridge keep strips (inner)
    y0_keep = GC_TAPER_L
    y1_keep = y_end
    x_g = GC_WIDE_W / 2
    inner.append(gdstk.rectangle(( x_g, y0_keep), ( x_g + GC_BRIDGE, y1_keep), layer=LAYER[0], datatype=LAYER[1]))
    inner.append(gdstk.rectangle((-x_g - GC_BRIDGE, y0_keep), (-x_g, y1_keep), layer=LAYER[0], datatype=LAYER[1]))

    # tapered cap above GC, shifted by half pitch
    GC_CAP_W0 = GC_WIDE_W + 2 * GC_BRIDGE
    y_shift = GC_CAP_SHIFT_HALF_PITCH * GC_PERIOD
    y0_cap = y_end + y_shift
    y1_cap = y_end + GC_CAP_H + y_shift

    inner.append(
        gdstk.Polygon(
            [
                (-GC_CAP_W0 / 2, y0_cap),
                ( GC_CAP_W0 / 2, y0_cap),
                ( GC_CAP_W1 / 2, y1_cap),
                (-GC_CAP_W1 / 2, y1_cap),
            ],
            layer=LAYER[0], datatype=LAYER[1],
        )
    )

    return inner, outer


def build_bottle_trench() -> gf.Component:
    gc_in_local, gc_out_local = _grating_coupler_polys()

    outer_parts = []
    inner_parts = []

    for inset in (0.0, INNER_INSET):
        pts, y_top = _bottle_pts(inset)

        # waveguide + clearance (same radius for both!)
        bottle_inner = _flexpath_polys(pts, WG_WIDTH, offset=0.0)
        bottle_outer = _flexpath_polys(pts, WG_WIDTH + 2 * CLEARANCE, offset=0.0)

        supports_inner, supports_outer = _supports_on_straights(pts, is_inner=(inset > 0))


        # endpoints for this trench are just pts endpoints now
        left_end  = pts[0]
        right_end = pts[-1]

        # Left GC vertical; Right GC horizontal pointing left
        gc_in_left   = _rotate_translate(gc_in_local,  0,  left_end[0],  left_end[1])
        gc_out_left  = _rotate_translate(gc_out_local, 0,  left_end[0],  left_end[1])

        gc_in_right  = _rotate_translate(gc_in_local,  90, right_end[0], right_end[1])
        gc_out_right = _rotate_translate(gc_out_local, 90, right_end[0], right_end[1])

        outer_parts += bottle_outer + gc_out_left + gc_out_right + supports_outer
        inner_parts += bottle_inner + supports_inner + gc_in_left + gc_in_right

    trench = _sub(_union(outer_parts), _union(inner_parts))

    c = gf.Component("double_trench_sameR")
    _poly_to_gf(c, trench, layer=LAYER)
    return c


def main():
    c = build_bottle_trench()
    c.write_gds("bottle_trench_with_supports_gc.gds")
    c.show()


if __name__ == "__main__":
    main()
