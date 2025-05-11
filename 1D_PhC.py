import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.circle import circle
from gdsfactory.components.taper import taper as taper_fn


def nanobeam_cavity_positive_geometry(
    a=255,  # nm
    r=65,  # nm
    w=370,  # nm
    taper_factors=[0.84, 0.844, 0.858, 0.88, 0.911, 0.951],
    mirror_N=10,
    taper_length=20.0,  # um
    taper_width=500,  # nm
    support_width=100,  # nm
    support_gap=5.0,  # um
    layer=(1, 0),
) -> Component:
    c = gf.Component("nanobeam_positive_fixed")

    # Convert to microns
    a_list = [a] * mirror_N + [a * f for f in taper_factors[::-1] + taper_factors] + [a] * mirror_N
    a_list_um = [ai * 1e-3 for ai in a_list]
    r_um = r * 1e-3
    w_um = w * 1e-3
    taper_width_um = taper_width * 1e-3
    support_width_um = support_width * 1e-3

    # Total lengths
    beam_length = sum(a_list_um)
    x_start = 0
    x = x_start

    # --- Create beam with holes subtraction ---
    holes = gf.Component()

    # --- Nanobeam rectangle ---
    beam = gf.components.straight(length=beam_length, width=w_um, layer=layer)

    # --- Air holes ---
    for ai in a_list_um:
        hole = circle(radius=r_um, layer=layer)
        hole_ref = holes.add_ref(hole)
        hole_ref.move((x + ai / 2, 0))
        x += ai

    beam_final = gf.boolean(A=beam, B=holes, operation="A-B", layer=layer)
    beam_ref = c.add_ref(beam_final)

    # Left taper
    taper_left = c.add_ref(taper_fn(length=10, width1=taper_width_um, width2=w_um, layer=layer))
    taper_left.connect("o2", other=beam.ports["o2"], allow_width_mismatch=True)

    # Right taper
    taper_right = c.add_ref(taper_fn(length=20, width1=taper_width_um, width2=0.02, layer=layer))
    taper_right.connect("o1", other=taper_left.ports["o1"], allow_width_mismatch=True)

    # --- Supports ---
    support = gf.components.straight(width=support_width_um, length=2, layer=layer)

    support1 = c.add_ref(support).rotate(90)
    support1.move((taper_left.xmax, -1))

    support_taper_down = c.add_ref(taper_fn(length=0.5, width1=support_width_um, width2=0.5, layer=layer))
    support_taper_down.connect("o1",other=support1.ports["o1"], allow_width_mismatch=True)

    support_taper_up = c.add_ref(taper_fn(length=0.5, width1=support_width_um, width2=0.5, layer=layer))
    support_taper_up.connect("o1", other=support1.ports["o2"], allow_width_mismatch=True)

    bbox=gf.components.straight(length=40,width=3)

    final = gf.boolean(A=bbox, B=c, operation="A-B")
    return final

def add_2D_phc_cavity(
    component: Component,
    a=252e-3,  # um
    r=65e-3,   # um
    nx=15,
    ny=5,
    shifts=[10.1e-3, 7.575e-3, 5.05e-3, 2.525e-3],
    x_offset=5,
    y_offset=5,
    layer=(1, 0),
):
    """Adds a 2D photonic crystal with a line-defect cavity."""
    for i in range(-nx, nx + 1):
        for j in range(-ny, ny + 1):
            # Triangular lattice coordinates
            x = i * a
            y = j * a * (3**0.5) / 2

            # Skip the center row (line defect)
            if j == 0:
                continue

            # Apply horizontal shifts for the central 4 cavity columns
            shift = 0
            abs_i = abs(i)
            if abs_i in [1, 2, 3, 4]:
                shift = shifts[abs_i - 1] * (1 if i > 0 else -1)
                x += shift

            # Place the air hole
            hole = circle(radius=r, layer=layer)
            hole_ref = component.add_ref(hole)
            hole_ref.move((x+x_offset, y+y_offset))



if __name__ == "__main__":
    c = nanobeam_cavity_positive_geometry()
    # --- Add 2D PhC cavity above 1D ---
    y_offset = 5  # microns above the beam
    phc2d = gf.Component("phc2d")
    add_2D_phc_cavity(phc2d, layer=(1, 0))

    # Create bounding box for 2D region
    phc_bbox = gf.components.rectangle(size=(8, 3), layer=(1, 0))
    phc_bbox_ref = gf.Component("phc2d_bbox")
    phc_bbox_ref.add_ref(phc_bbox).move((1, 3.5))

    # c.add_ref(phc2d)
    # Subtract 2D PhC holes from the box
    phc2d_final = gf.boolean(A=phc_bbox_ref, B=phc2d, operation="A-B", layer=(1, 0))

    # Add it to the main component
    c.add_ref(phc2d_final)

    c.show()
    c.write_gds(r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM\11-05-25\nanobeam_final.gds")
