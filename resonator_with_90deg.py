from __future__ import annotations

from pathlib import Path
import uuid
import gdstk
import gdsfactory as gf

from MDM3_23_Nov_2025_GC import gcR_alld_highNA_red


# =========================
# Parameters
# =========================
WG_WIDTH = 0.25
TARGET_CLEAR = 10.0     # fixed clearance stripe height (this removed the step)
SEAM_OVERLAP = 0.2
ROW_SPACING = 6.0
GC_GAP = 5.0           # WG gap from GC inner port to QT bbox edge (adjust if you want)
LAYER = (1, 0)


def _uid(tag: str) -> str:
    return f"{tag}_{uuid.uuid4().hex[:8]}"

def sanitize_gds_cellnames(input_gds: Path, output_gds: Path, prefix: str) -> Path:
    """Prefix all cell names to avoid TOP collisions in kfactory."""
    lib = gdstk.read_gds(str(input_gds))
    used = set()
    for cell in lib.cells:
        base = f"{prefix}__{cell.name}"
        name = base
        i = 1
        while name in used:
            i += 1
            name = f"{base}__{i}"
        used.add(name)
        cell.name = name
    lib.write_gds(str(output_gds))
    return output_gds

def extend_gc_clearance_in_tmp(c_tmp: gf.Component, gc_ref) -> gf.Component | object:
    """
    GC already has clearance, but may be missing extent to reach TARGET_CLEAR.
    Extension direction depends on GC rotation:
      - 0 / 180 deg  -> extend UP/DOWN
      - +/-90 deg    -> extend LEFT/RIGHT
    """
    b = gc_ref.dbbox()
    xmin, xmax = float(b.left), float(b.right)
    ymin, ymax = float(b.bottom), float(b.top)

    w = xmax - xmin
    h = ymax - ymin

    # determine orientation from bbox aspect ratio
    is_vertical = h > w   # GC rotated 90deg

    if is_vertical:
        # extend LEFT / RIGHT
        gc_span = w
    else:
        # extend UP / DOWN
        gc_span = h

    gc_pad = max(0.0, (TARGET_CLEAR - gc_span) / 2.0)
    pad_w = gc_pad + SEAM_OVERLAP

    if pad_w <= 0:
        return gc_ref

    if is_vertical:
        # LEFT pad
        pad_L = gf.components.rectangle(size=(pad_w, h))
        pad_L_ref = c_tmp.add_ref(pad_L)
        pad_L_ref.move((xmin - gc_pad, ymin))

        # RIGHT pad
        pad_R = gf.components.rectangle(size=(pad_w, h))
        pad_R_ref = c_tmp.add_ref(pad_R)
        pad_R_ref.move((xmax - SEAM_OVERLAP, ymin))

        pads = gf.boolean(A=pad_L_ref, B=pad_R_ref, operation="or", layer=LAYER)

    else:
        # TOP pad
        pad_T = gf.components.rectangle(size=(w, pad_w))
        pad_T_ref = c_tmp.add_ref(pad_T)
        pad_T_ref.move((xmin, ymax - SEAM_OVERLAP))

        # BOTTOM pad
        pad_B = gf.components.rectangle(size=(w, pad_w))
        pad_B_ref = c_tmp.add_ref(pad_B)
        pad_B_ref.move((xmin, ymin - gc_pad))

        pads = gf.boolean(A=pad_T_ref, B=pad_B_ref, operation="or", layer=LAYER)

    return gf.boolean(A=gc_ref, B=pads, operation="or", layer=LAYER)

def build_clearance_row_wg(wg_length: float) -> gf.Component:
    """Row: GC – WG(material) – GC, with clearance merged. Clearance-only output."""
    row = gf.Component(_uid("ROW_WG_{wg_length}"))
    c_tmp = gf.Component(_uid(f"TMP_WG_{wg_length}"))

    gc = gcR_alld_highNA_red()
    gc_L = c_tmp.add_ref(gc)

    # material WG
    wg = gf.components.straight(length=wg_length, width=WG_WIDTH)
    wg_tmp = c_tmp.add_ref(wg)
    wg_tmp.connect("o1", gc_L.ports["o2"], allow_width_mismatch=True)

    # right GC
    gc_R = c_tmp.add_ref(gc).drotate(180)
    gc_R.connect("o2", wg_tmp.ports["o2"], allow_width_mismatch=True)

    # clearance stripe (fixed width = TARGET_CLEAR)
    stripe = gf.components.straight(length=wg_length, width=TARGET_CLEAR)
    stripe_ref = c_tmp.add_ref(stripe)
    stripe_ref.connect("o1", gc_L.ports["o2"], allow_width_mismatch=True)

    wg_trench = gf.boolean(A=stripe_ref, B=wg_tmp, operation="A-B", layer=LAYER)

    gc_L_clear = extend_gc_clearance_in_tmp(c_tmp, gc_L)
    gc_R_clear = extend_gc_clearance_in_tmp(c_tmp, gc_R)

    merged = gf.boolean(
        A=gf.boolean(A=gc_L_clear, B=gc_R_clear, operation="or", layer=LAYER),
        B=wg_trench,
        operation="or",
        layer=LAYER,
    )

    row.add_ref(merged)
    return row

def build_clearance_row_qt(qt_gds: Path, prefix: str) -> gf.Component:
    """
    Row: GC – (WG gap) – QTxx (imported) – (WG gap) – GC
    Clearance-only output (merged clearance).
    """
    row = gf.Component(_uid(f"ROW_{prefix}"))
    c_tmp = gf.Component(_uid(f"TMP_{prefix}"))

    # import QT with safe cellnames
    qt_s = qt_gds.with_name(f"_san_{qt_gds.stem}_{uuid.uuid4().hex[:6]}.gds")
    sanitize_gds_cellnames(qt_gds, qt_s, prefix=prefix)

    dev = gf.import_gds(qt_s)
    dev_ref = c_tmp.add_ref(dev)

    # device bbox
    bb = dev_ref.dbbox()
    xmin, xmax = float(bb.left), float(bb.right)
    ymin, ymax = float(bb.bottom), float(bb.top)
    ymid = 0.5 * (ymin + ymax)

    gc = gcR_alld_highNA_red()

    # left GC
    gc_L = c_tmp.add_ref(gc)
    gc_L.move(destination=(xmin - GC_GAP, ymid), origin=gc_L.ports["o2"].center)
    y_row = gc_L.ports["o2"].center[1]

    # shift device to row y
    dev_ref.dmovey(y_row - ymid)

    # recompute bbox
    bb = dev_ref.dbbox()
    xmin, xmax = float(bb.left), float(bb.right)

    # right GC
    gc_R = c_tmp.add_ref(gc).drotate(180)
    gc_R.move(destination=(xmax + GC_GAP, y_row), origin=gc_R.ports["o2"].center)

    # material WG gaps
    wg_gap_L = gf.components.straight(length=GC_GAP + 1, width=WG_WIDTH)
    wgL_ref = c_tmp.add_ref(wg_gap_L)
    wgL_ref.move((xmin - GC_GAP, 0))

    wg_gap_R = gf.components.straight(length=GC_GAP, width=WG_WIDTH)
    wgR_ref = c_tmp.add_ref(wg_gap_R)
    wgR_ref.move((xmax, 0))

    # clearance stripe
    stripe_len = (xmax - xmin) + 2 * GC_GAP
    stripe = gf.components.straight(length=stripe_len, width=TARGET_CLEAR)
    stripe_ref = c_tmp.add_ref(stripe)
    stripe_ref.connect("o1", gc_L.ports["o2"], allow_width_mismatch=True)

    # subtract material
    sub_u = gf.boolean(A=dev_ref, B=wgL_ref, operation="or", layer=LAYER)
    sub_u = gf.boolean(A=sub_u, B=wgR_ref, operation="or", layer=LAYER)
    stripe_trench = gf.boolean(A=stripe_ref, B=sub_u, operation="A-B", layer=LAYER)

    # extend GC clearance
    gc_L_clear = extend_gc_clearance_in_tmp(c_tmp, gc_L)
    gc_R_clear = extend_gc_clearance_in_tmp(c_tmp, gc_R)

    merged = gf.boolean(
        A=gf.boolean(A=gc_L_clear, B=gc_R_clear, operation="or", layer=LAYER),
        B=stripe_trench,
        operation="or",
        layer=LAYER,
    )

    row.add_ref(merged)
    return row

def build_clearance_row_90deg_down(R=20.0) -> gf.Component:
    """
    Row: GC – (90deg bend, R=35um, facing DOWN) – GC
    Clearance-only output (merged clearance).
    """
    row = gf.Component(_uid("ROW_90DEG_DOWN_R35"))
    c_tmp = gf.Component(_uid("TMP_90DEG_DOWN_R35"))

    gc = gcR_alld_highNA_red()

    # =========================
    # Geometry parameters
    # =========================
    Lx = 0.0       # straight before bend
    Ly = 0.0       # straight after bend
    STEM_LEN = 0.0  # short stem into GC

    # =========================
    # Left GC
    # =========================
    gc_L = c_tmp.add_ref(gc)
    x0, y0 = gc_L.ports["o2"].center

    # =========================
    # Centerline path (right then down)
    # =========================
    pts = [
        (x0, y0),
        (x0 + Lx, y0),
        (x0 + Lx + R, y0),
        (x0 + Lx + R, y0 - R),
        (x0 + Lx + R, y0 - R - Ly),
    ]

    # =========================
    # Material path (FlexPath)
    # =========================
    mat_comp = gf.Component(_uid("MAT_FP"))
    mat_fp = gdstk.FlexPath(pts, WG_WIDTH, bend_radius=R)
    for p in mat_fp.to_polygons():
        mat_comp.add_polygon(p.points, layer=LAYER)
    mat_ref = c_tmp.add_ref(mat_comp)

    # =========================
    # Clearance path (FlexPath)
    # =========================
    clr_comp = gf.Component(_uid("CLR_FP"))
    clr_fp = gdstk.FlexPath(pts, TARGET_CLEAR, bend_radius=R)
    for p in clr_fp.to_polygons():
        clr_comp.add_polygon(p.points, layer=LAYER)
    clr_ref = c_tmp.add_ref(clr_comp)

    # =========================
    # Stem into right GC (material)
    # =========================
    end_x = x0 + Lx + R
    end_y = y0 - R - Ly

    if STEM_LEN > 0:
        stem_mat = gf.components.rectangle(size=(WG_WIDTH, STEM_LEN))
        stem_mat_ref = c_tmp.add_ref(stem_mat)
        stem_mat_ref.move((end_x - WG_WIDTH / 2, end_y))

        mat_u = gf.boolean(
            A=mat_ref,
            B=stem_mat_ref,
            operation="or",
            layer=LAYER,
        )

        # =========================
        # Stem into right GC (clearance)
        # =========================

        stem_clr = gf.components.rectangle(size=(TARGET_CLEAR, STEM_LEN))
        stem_clr_ref = c_tmp.add_ref(stem_clr)
        stem_clr_ref.move((end_x - TARGET_CLEAR / 2, end_y))

        clr_u = gf.boolean(
            A=clr_ref,
            B=stem_clr_ref,
            operation="or",
            layer=LAYER,
        )

        # =========================
        # Trench = clearance - material
        # =========================
        trench = gf.boolean(
            A=clr_u,
            B=mat_u,
            operation="A-B",
            layer=LAYER,
        )
    else:
        trench = gf.boolean(
            A=clr_ref,
            B=mat_ref,
            operation="A-B",
            layer=LAYER,
        )

    # =========================
    # Right GC (rotated DOWN)
    # =========================
    gc_R = c_tmp.add_ref(gc).drotate(90)
    gc_R.move(destination=(end_x, end_y), origin=gc_R.ports["o2"].center)

    # =========================
    # Extend GC clearance blocks
    # =========================
    gc_L_clear = extend_gc_clearance_in_tmp(c_tmp, gc_L)
    gc_R_clear = extend_gc_clearance_in_tmp(c_tmp, gc_R)


    merged = gf.boolean(
        A=gf.boolean(A=gc_L_clear, B=gc_R_clear, operation="or", layer=LAYER),
        B=trench,
        operation="or",
        layer=LAYER,
    )


    row.add_ref(merged)
    return row

def main() -> gf.Component:
    c = gf.Component(_uid("MERGED_3_ROWS"))

    base_dir = Path(__file__).resolve().parent
    gds_dir = base_dir / "Selected Resonators to FAB"
    qt18_gds = gds_dir / "QT18.gds"
    qt20_gds = gds_dir / "QT20.gds"

    # Build rows
    row1 = build_clearance_row_wg(5.0)
    row2 = build_clearance_row_wg(10.0)
    row3 = build_clearance_row_wg(15.0)
    row4 = build_clearance_row_qt(qt18_gds, "QT18")
    row5 = build_clearance_row_qt(qt20_gds, "QT20")
    row6 = build_clearance_row_90deg_down(R=21)
    row7 = build_clearance_row_90deg_down(R=15)

    # Put all rows into one temp and OR them to merge into a single polygon
    tmp_merge = gf.Component(_uid("TMP_MERGE_ALL"))
    r1 = tmp_merge.add_ref(row1)
    r2 = tmp_merge.add_ref(row2); r2.dmovey(-ROW_SPACING)
    r3 = tmp_merge.add_ref(row3); r3.dmovey(-2 * ROW_SPACING)
    r4 = tmp_merge.add_ref(row4); r4.dmovey(-3 * ROW_SPACING); r4.dmovex(GC_GAP*2+4.345)
    r5 = tmp_merge.add_ref(row5); r5.dmovey(-4 * ROW_SPACING); r5.dmovex(GC_GAP * 2 + 4.345)
    r6 = tmp_merge.add_ref(row6); r6.dmovey(-5 * ROW_SPACING)
    r7 = tmp_merge.add_ref(row7); r7.dmovey(-6 * ROW_SPACING)

    m12 = gf.boolean(A=r1, B=r2, operation="or", layer=LAYER)
    m123 = gf.boolean(A=m12, B=r3, operation="or", layer=LAYER)
    m1234 = gf.boolean(A=m123, B=r4, operation="or", layer=LAYER)
    m12345 = gf.boolean(A=m1234, B=r5, operation="or", layer=LAYER)
    m123456 = gf.boolean(A=m12345, B=r6, operation="or", layer=LAYER)
    m1234567 = gf.boolean(A=m123456, B=r7, operation="or", layer=LAYER)


    c.add_ref(m1234567)

    return c

def run_and_save(wg_width: float):
    global WG_WIDTH
    WG_WIDTH = wg_width

    c = main()

    suffix = f"{WG_WIDTH:.2f}".replace(".", "p")
    out_name = f"MERGED_CLEARANCE_WG{suffix}.gds"

    c.write_gds(out_name)
    print(f"Wrote {out_name}")


if __name__ == "__main__":
    # First: current WG_WIDTH (whatever is set above)
    run_and_save(WG_WIDTH)

    # Second: WG_WIDTH = 0.3
    run_and_save(0.3)

