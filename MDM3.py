import numpy as np
import gdstk
import gdsfactory as gf
from functools import partial
from pathlib import Path
from datetime import datetime
import os

from kfactory.kf_types import layer
from shapely.ops import orient


def merge_references(base, refs, layer):
    """Boolean OR of a base geometry with a list of references, handling nested lists."""

    merged = base
    flattened_refs = []

    # Flatten nested lists
    def flatten(ref_list):
        for ref in ref_list:
            if isinstance(ref, list):  # If it's a list, flatten it recursively
                flatten(ref)
            elif isinstance(ref, (gf.Component, gf.Instance)):  # Only keep valid Components
                flattened_refs.append(ref)
            else:
                print(f"❌ Warning: Ignoring invalid reference of type {type(ref)}")

    flatten(refs)  # Flatten input list

    # Perform boolean OR operation on all valid references
    for ref in flattened_refs:
        merged = gf.boolean(A=merged, B=ref, operation="or", layer=layer)

    return merged

def create_spring_comb(c, cross_section, start_pos):
    """
    Create a spring-like geometry starting at 'start_pos'.
    Returns a list of references for subsequent boolean merges.
    """
    refs = []
    horizontal_l=4.4
    vertical_l=3.8

    # Taper that starts the spring
    taper_start = gf.components.taper(length=0.15, width1=0.5, width2=0.15, layer=cross_section.layer)
    taper_start_ref = c.add_ref(taper_start).drotate(90)
    taper_start_ref.move(start_pos)
    refs.append(taper_start_ref)

    straight0 = gf.components.straight(cross_section=cross_section, length=vertical_l-1.65)
    straight0_ref = c.add_ref(straight0)
    straight0_ref.connect(port="in", other=taper_start_ref.ports["o2"], allow_width_mismatch=True)
    refs.append(straight0_ref)

    # Sequence of arcs/straights that form the spring
    bend1 = gf.components.bend_euler(cross_section=cross_section, angle=-90, radius=0.8)
    bend1_ref = c.add_ref(bend1).drotate(90)
    bend1_ref.connect(port="in", other=straight0_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend1_ref)

    straight1 = gf.components.straight(cross_section=cross_section, length=horizontal_l-1.5)
    straight1_ref = c.add_ref(straight1)
    straight1_ref.connect(port="in", other=bend1_ref.ports["out"], allow_width_mismatch=True)
    refs.append(straight1_ref)

    bend2 = gf.components.bend_euler(cross_section=cross_section, angle=-180, radius=0.3, npoints=12)
    bend2_ref = c.add_ref(bend2)
    bend2_ref.connect(port="in", other=straight1_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend2_ref)

    straight2 = gf.components.straight(cross_section=cross_section, length=horizontal_l-1.5)
    straight2_ref = c.add_ref(straight2)
    straight2_ref.connect(port="in", other=bend2_ref.ports["out"], allow_width_mismatch=True)
    refs.append(straight2_ref)

    bend3 = gf.components.bend_euler(cross_section=cross_section, angle=180, radius=0.3, npoints=12)
    bend3_ref = c.add_ref(bend3)
    bend3_ref.connect(port="in", other=straight2_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend3_ref)

    straight3 = gf.components.straight(cross_section=cross_section, length=horizontal_l-1)
    straight3_ref = c.add_ref(straight3)
    straight3_ref.connect(port="in", other=bend3_ref.ports["out"], allow_width_mismatch=True)
    refs.append(straight3_ref)

    bend4 = gf.components.bend_euler(cross_section=cross_section, angle=90, radius=0.3, npoints=12)
    bend4_ref = c.add_ref(bend4)
    bend4_ref.connect(port="in", other=straight3_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend4_ref)

    straight4 = gf.components.straight(cross_section=cross_section, length=1)
    straight4_ref = c.add_ref(straight4)
    straight4_ref.connect(port="in", other=bend4_ref.ports["out"], allow_width_mismatch=True)
    refs.append(straight4_ref)

    bend5 = gf.components.bend_euler(cross_section=cross_section, angle=90, radius=0.3, npoints=12)
    bend5_ref = c.add_ref(bend5)
    bend5_ref.connect(port="in", other=straight4_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend5_ref)

    straight5 = gf.components.straight(cross_section=cross_section, length=horizontal_l-0.4)
    straight5_ref = c.add_ref(straight5)
    straight5_ref.connect(port="in", other=bend5_ref.ports["out"], allow_width_mismatch=True)
    refs.append(straight5_ref)

    bend6 = gf.components.bend_euler(cross_section=cross_section, angle=-90, radius=0.3, npoints=12)
    bend6_ref = c.add_ref(bend6)
    bend6_ref.connect(port="in", other=straight5_ref.ports["out"], allow_width_mismatch=True)
    refs.append(bend6_ref)

    taper_end = gf.components.taper(length=0.5, width1=0.15, width2=0.8, layer=cross_section.layer)
    taper_end_ref = c.add_ref(taper_end)
    taper_end_ref.connect(port="o1", other=bend6_ref.ports["out"], allow_width_mismatch=True)
    refs.append(taper_end_ref)

    return refs

def create_spring_vertical(c, cross_section, comb_spine):
    """
    Create a spring-like geometry starting at 'start_pos'.
    Returns a list of references for subsequent boolean merges.
    """
    refs = []
    vertical_l=3

    # Taper that starts the spring
    taper_start = gf.components.taper(length=0.15, width1=0.5, width2=0.15, layer=cross_section.layer)
    taper_start_ref = c.add_ref(taper_start)
    taper_start_ref.connect(port="o1", other=comb_spine.ports["o2"], allow_width_mismatch=True)
    refs.append(taper_start_ref)

    straight0 = gf.components.straight(cross_section=cross_section, length=vertical_l)
    straight0_ref = c.add_ref(straight0)
    straight0_ref.connect(port="in", other=taper_start_ref.ports["o2"], allow_width_mismatch=True)
    refs.append(straight0_ref)



    taper_end = gf.components.taper(length=0.5, width1=0.15, width2=0.8, layer=cross_section.layer)
    taper_end_ref = c.add_ref(taper_end)
    taper_end_ref.connect(port="o1", other=straight0_ref.ports["out"], allow_width_mismatch=True)
    refs.append(taper_end_ref)

    return refs

def create_vertical_supports(c, layer, cnt1, cnt2,dy):
    """
    Creates vertical support tapers and shapes around the waveguide ports.
    cnt1, cnt2 are (x, y) positions in mm (since you used /1000).
    Returns a list of references for subsequent boolean merges.
    """
    refs = []

    # Taper small
    s3_len = 2
    taper_small = gf.components.taper(length=s3_len+1.5, width1=2, width2=0.2, layer=layer)

    # Taper large
    taper_large = gf.components.taper(length=s3_len+6, width1=4, width2=0.2, layer=layer)

    # Tapers around first waveguide center
    ts1_ref = c.add_ref(taper_small).drotate(90)
    ts1_ref.dmove((cnt1[0], cnt1[1] - s3_len - 1.75))
    refs.append(ts1_ref)

    ts2_ref = c.add_ref(taper_large).drotate(270)
    ts2_ref.dmove((cnt1[0], cnt1[1] + s3_len + 6.25))
    refs.append(ts2_ref)

    # Tapers around second waveguide center
    ts3_ref = c.add_ref(taper_small).drotate(90)
    ts3_ref.dmove((cnt2[0], cnt1[1] - s3_len - 1.75))
    refs.append(ts3_ref)

    ts4_ref = c.add_ref(taper_large).drotate(270)
    ts4_ref.dmove((cnt2[0], cnt2[1] + s3_len + 6.25))
    refs.append(ts4_ref)

    return refs

def create_dc_design_comb(resonator="fish", coupler_l=0.42,clearance_width=50):
    """
    Creates a DC design with a specified resonator type ("fish" or "other"),
    and waveguide/resonator widths.

    Returns
    -------
    dc_positive : gf.Component
        A GDS component representing the final boolean geometry.
    """
    c = gf.Component()

    # General parameters
    wg_width = 0.25       # Waveguide width (microns)
    tooth_width = 0.5
    tooth_length = 5
    dy = tooth_length+0.8  # Vertical offset (microns)
    sbend_length = dy*2  # S-bend length (microns)
    x_spacing = round(3 * tooth_width, 1)
    N_teeth = 12
    output_taper_length=10
    taper1_length, taper1_width2 = 3, 0.6
    width_resonator = 0.42 if resonator == "fish" else 0.54

    layer_main = (1, 0)
    refs=[]

    # --- Load fish or alternative resonator geometry ---
    gds_path = Path("QT14_v1.gds") if resonator == "fish" else Path("QT10.gds")
    fish_component = gf.import_gds(gds_path)
    fish_component.add_port(
        name="o1", center=(0, 0), width=0.5, orientation=180, layer=layer_main
    )

    fish_component.add_port(
        name="o2",
        center=(fish_component.size_info.width - 0.002,0),
        width=0.5,
        orientation=0,
        layer=layer_main,
    )

    # Cross-section for S-bend
    x_sbend = gf.CrossSection(
        sections=[gf.Section(width=wg_width, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    # --- Define Tapers and S-bends ---

    taper1 = gf.components.taper(
        length=taper1_length,
        width1=wg_width,
        width2=taper1_width2,
        layer=layer_main
    )

    taper_small_in = gf.components.taper(
        length=output_taper_length, width1=0.08, width2=wg_width, layer=layer_main
    )
    taper_small_in_ref = c.add_ref(taper_small_in)
    taper_small_in_ref.dmovex(-sbend_length - 10)
    taper_small_in_ref.dmovey(dy + wg_width/2 + 0.12)
    refs.append(taper_small_in_ref)

    taper1_ref = c.add_ref(taper1)
    taper1_ref.connect(port="o1", other=taper_small_in_ref.ports["o2"])
    refs.append(taper1_ref)

    taper1_mirror = c.add_ref(taper1).mirror_x()
    taper1_mirror.connect(port="o2", other=taper1_ref.ports["o2"], allow_width_mismatch=True)
    refs.append(taper1_mirror)

    sbend = gf.components.bend_s(
        cross_section=x_sbend, size=(sbend_length, -dy - wg_width / 2)
    )
    sbend_ref = c.add_ref(sbend)
    sbend_ref.connect(port="in", other=taper1_mirror.ports["o1"], allow_width_mismatch=True)
    refs.append(sbend_ref)

    coupler_ref = c.add_ref(gf.components.straight(length=coupler_l,width=wg_width,layer=layer_main))
    coupler_ref.connect(port="o1", other=sbend_ref.ports["out"], allow_width_mismatch=True)
    refs.append(coupler_ref)

    sbend_ref_mirror = c.add_ref(sbend).mirror_x()
    sbend_ref_mirror.connect(port="in", other=coupler_ref.ports["o2"])
    refs.append(sbend_ref_mirror)

    taper1_ref_2 = c.add_ref(gf.components.taper(length=taper1_length, width1=wg_width, width2=width_resonator, layer=layer_main))
    taper1_ref_2.connect(port="o1", other=sbend_ref_mirror.ports["out"], allow_width_mismatch=True)
    refs.append(taper1_ref_2)

    # --- Attach fish component ---
    fish_ref = c.add_ref(fish_component)
    fish_ref.connect(port="o1", other=taper1_ref_2.ports["o2"], allow_width_mismatch=True)
    refs.append(fish_ref)

    comb_base = c.add_ref(gf.components.straight(length=tooth_width, width=tooth_length*2+0.8, layer=layer_main))
    comb_base.connect(port="o1", other=fish_ref.ports["o2"], allow_width_mismatch=True)
    if not resonator == "fish":
        comb_base.dmovex(-0.093)
    refs.append(comb_base)

    comb_spine = c.add_ref(gf.components.straight(length=N_teeth*x_spacing, width=0.8, layer=layer_main))
    comb_spine.connect(port="o1", other=comb_base.ports["o2"], allow_width_mismatch=True)
    refs.append(comb_spine)

    opposing_comb_spine_up = c.add_ref(gf.components.straight(length=N_teeth*x_spacing+1, width=1.3, layer=layer_main))
    opposing_comb_spine_up.connect(port="o1", other=comb_base.ports["o2"], allow_width_mismatch=True)
    opposing_comb_spine_up.dmovey(tooth_length+1.25).dmovex(0.15)
    refs.append(opposing_comb_spine_up)

    opposing_comb_spine_up_ancor = c.add_ref(gf.components.straight(length=15, width=5, layer=layer_main))
    opposing_comb_spine_up_ancor.connect(port="o1", other=comb_base.ports["o2"], allow_width_mismatch=True)
    opposing_comb_spine_up_ancor.dmovex(5).dmovey(9)
    refs.append(opposing_comb_spine_up_ancor)

    opposing_comb_spine_down = c.add_ref(gf.components.straight(length=N_teeth*x_spacing+1, width=0.5, layer=layer_main))
    opposing_comb_spine_down.connect(port="o1", other=comb_base.ports["o2"], allow_width_mismatch=True)
    opposing_comb_spine_down.dmovey(-dy).dmovex(0.15)
    refs.append(opposing_comb_spine_down)

    opposing_comb_spine_down_ext = c.add_ref(gf.components.straight(length=1.2, width=.5, layer=layer_main))
    opposing_comb_spine_down_ext.connect(port="o2", other=opposing_comb_spine_down.ports["o1"], allow_width_mismatch=True)
    refs.append(opposing_comb_spine_down_ext)

    opposing_comb_spine_down_taper = c.add_ref(gf.components.taper(length=.82, width1=dy,width2=0.5, layer=layer_main))
    opposing_comb_spine_down_taper.connect(port="o2", other=opposing_comb_spine_down_ext.ports["o1"], allow_width_mismatch=True)
    refs.append(opposing_comb_spine_down_taper)

    # --- "Teeth" arrays ---

    teeth_array_1 = c.add_ref(
        unite_array(
            gf.components.straight(length=tooth_width, width=tooth_length, layer=layer_main),
            rows=2, cols=N_teeth, spacing=(x_spacing, tooth_length+0.8)
        )
    )
    teeth_array_1.move((comb_base.ports["o2"].x / 1000-tooth_width+x_spacing, comb_base.ports["o2"].y / 1000-tooth_length/2-.4))
    refs.append(teeth_array_1)

    teeth_array_2 = c.add_ref(
        unite_array(
            gf.components.straight(length=tooth_width, width=tooth_length+0.1, layer=layer_main),
            rows=2, cols=N_teeth, spacing=(x_spacing, tooth_length+1.2)
        )
    )
    teeth_array_2.move((comb_base.ports["o2"].x / 1000+0.15, comb_base.ports["o2"].y / 1000-3.1))
    refs.append(teeth_array_2)

    fillet_array =  unite_array(create_fillet(), rows=1, cols=N_teeth, spacing=(x_spacing, 0))
    fillet_array_left_top = c.add_ref(fillet_array)
    fillet_array_left_top.move((comb_base.ports["o2"].x / 1000 , comb_spine.ports["o2"].y / 1000 + 0.4))
    refs.append(fillet_array_left_top)
    fillet_array_left_bot = c.add_ref(fillet_array).mirror_y()
    fillet_array_left_bot.move((comb_base.ports["o2"].x / 1000 , comb_spine.ports["o2"].y / 1000 - 0.4))
    refs.append(fillet_array_left_bot)

    fillet_array_right_top = c.add_ref(fillet_array).mirror_x()
    fillet_array_right_top.move((comb_base.ports["o2"].x / 1000  + x_spacing*(N_teeth)-tooth_width, comb_spine.ports["o2"].y / 1000 + 0.4))
    refs.append(fillet_array_right_top)
    fillet_array_right_bot = c.add_ref(fillet_array).mirror_x().mirror_y()
    fillet_array_right_bot.move((comb_base.ports["o2"].x / 1000  + x_spacing*(N_teeth)-tooth_width, comb_spine.ports["o2"].y / 1000 - 0.4))
    refs.append(fillet_array_right_bot)

    # --- SPRING cross-section + geometry ---
    spring_cs = gf.CrossSection(
        sections=[gf.Section(width=0.15, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    # Build the spring segments
    spring_refs = create_spring_comb(c=c, cross_section=spring_cs,
                                     start_pos=(comb_base.ports["o2"].x / 1000 - 0.25, comb_base.ports["o2"].y / 1000 + tooth_length + 0.3))
    refs.append(spring_refs)

    # --- Vertical supports ---
    cnt1_x = taper1_ref.ports["o2"].center[0] / 1000
    cnt1_y = taper1_ref.ports["o2"].center[1] / 1000
    cnt2_x = taper1_ref_2.ports["o2"].center[0] / 1000+1.3
    cnt2_y = taper1_ref.ports["o2"].center[1] / 1000

    vertical_supports = create_vertical_supports(c=c,layer=layer_main,cnt1=(cnt1_x, cnt1_y),cnt2=(cnt2_x, cnt2_y),dy=dy)
    refs.append(vertical_supports)


    # --- Construct top waveguide geometry with boolean OR ---
    top_waveguide = gf.boolean(
        A=taper_small_in_ref, B=taper1_ref, operation="or", layer=layer_main
    )

    top_waveguide = merge_references(top_waveguide, refs, layer_main)

    # Merge all references

    # Create mirrored waveguide (bot_waveguide)
    bot_waveguide_ref = gf.Component().add_ref(top_waveguide).mirror_y()
    # Shift if necessary: .dmovey(dy*0) does nothing, but keep it for clarity:
    bot_waveguide_ref.dmovey(dy * 0)

    # Combine top + bottom waveguides
    combined_dc = gf.boolean(A=top_waveguide, B=bot_waveguide_ref, operation="or", layer=layer_main)

    #########################

    thick_cs = gf.CrossSection(
        sections=[gf.Section(width=3, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    thick_dc = gf.Component()

    # Straight section along the first taper
    straight1 = gf.components.straight(length=output_taper_length + 2 * taper1_length, cross_section=thick_cs)
    s1 = thick_dc.add_ref(straight1)
    s1.connect(port="in", other=taper_small_in_ref.ports["o2"], allow_width_mismatch=True)
    s1.dmovex(-output_taper_length)

    # First S-bend section (same as the original code)
    thick_s_bend1 = gf.components.bend_s(size=(sbend_length, -dy - wg_width / 2), cross_section=thick_cs)
    b1 = thick_dc.add_ref(thick_s_bend1)
    b1.connect(port="in", other=s1.ports["out"])

    # Straight coupler section along the resonator
    straight2 = gf.components.straight(length=coupler_l, cross_section=thick_cs)
    s2 = thick_dc.add_ref(straight2)
    s2.connect(port="in", other=b1.ports["out"])

    # Second S-bend section (mirror of the first one)
    thick_s_bend2 = gf.components.bend_s(size=(sbend_length, dy + wg_width / 2), cross_section=thick_cs)
    b2 = thick_dc.add_ref(thick_s_bend2)
    b2.connect(port="in", other=s2.ports["out"])

    # Final straight section after the second S-bend
    final_straight = gf.components.straight(length=taper1_length + 5.379, cross_section=thick_cs)
    s3 = thick_dc.add_ref(final_straight)
    s3.connect(port="in", other=b2.ports["out"])

    # Create bottom mirrored version
    thick_dc_ref_bot = gf.Component().add_ref(thick_dc).mirror_y()

    # Combine top and bottom thick DC into one component
    combined_thick_dc = gf.boolean(A=thick_dc, B=thick_dc_ref_bot, operation="or", layer=layer_main)

    #########################

    # --- Subtract combined waveguide from a large rectangle to get final geometry ---
    bounding_rect = gf.components.straight(
        length=N_teeth*x_spacing+1.55,
        width=dy * 2.5 + 16,
        layer=layer_main
    )
    bounding_rect_ref = c.add_ref(bounding_rect)
    bounding_rect_ref.dmovex(25.5)
    bounding_ext = c.add_ref(gf.components.straight(length=clearance_width,width=50,layer=layer_main)).dmovex(-21.6-clearance_width)
    bounding_rect_ref = gf.boolean(A=bounding_rect_ref, B=bounding_ext, operation="or", layer=layer_main)
    bounding_rect_ref = c.add_ref(gf.boolean(A=bounding_rect_ref, B=combined_thick_dc, operation="or", layer=layer_main))


    dc_positive = gf.boolean(A=bounding_rect_ref, B=combined_dc, operation="A-B", layer=layer_main)



    return dc_positive

def create_dc_design_vertical(resonator="fish",coupler_l=0.42,clearance_width=50,pad_x_offset=10,pad_y_offset=0,layers=None):
    """
    Creates a DC design with a specified resonator type ("fish" or "other"),
    and waveguide/resonator widths.

    Returns
    -------
    dc_positive : gf.Component
        A GDS component representing the final boolean geometry.
    """
    c = gf.Component()

    # General parameters
    wg_width = 0.25       # Waveguide width (microns)
    tooth_width = 0.5
    tooth_length = 5
    dy = tooth_length+0.8  # Vertical offset (microns)
    sbend_length = dy*2  # S-bend length (microns)
    x_spacing = round(3 * tooth_width, 1)
    N_teeth = 12
    output_taper_length=10
    taper1_length, taper1_width2 = 3, 0.6
    width_resonator = 0.42 if resonator == "fish" else 0.54


    layer_main = (1, 0)
    refs=[]

    # --- Load fish or alternative resonator geometry ---
    gds_path = Path("Selected Resonators to FAB\QT14_v1.gds") if resonator == "fish" else Path("Selected Resonators to FAB\QT10.gds")
    fish_component = gf.import_gds(gds_path)
    fish_component.add_port(
        name="o1", center=(0, 0), width=0.5, orientation=180, layer=layer_main
    )

    fish_component.add_port(
        name="o2",
        center=(fish_component.size_info.width - 0.05,0),
        width=0.5,
        orientation=0,
        layer=layer_main,
    )


    # Cross-section for S-bend
    x_sbend = gf.CrossSection(
        sections=[gf.Section(width=wg_width, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    # --- Define Tapers and S-bends ---

    taper1 = gf.components.taper(
        length=taper1_length,
        width1=wg_width,
        width2=taper1_width2,
        layer=layer_main
    )

    taper_small_in = gf.components.taper(
        length=output_taper_length, width1=0.08, width2=wg_width, layer=layer_main
    )
    taper_small_in_ref = c.add_ref(taper_small_in)
    taper_small_in_ref.dmovex(-sbend_length - 10)
    taper_small_in_ref.dmovey(dy + wg_width/2 + 0.12)
    refs.append(taper_small_in_ref)

    taper1_ref = c.add_ref(taper1)
    taper1_ref.connect(port="o1", other=taper_small_in_ref.ports["o2"])
    refs.append(taper1_ref)

    taper1_mirror = c.add_ref(taper1).mirror_x()
    taper1_mirror.connect(port="o2", other=taper1_ref.ports["o2"], allow_width_mismatch=True)
    refs.append(taper1_mirror)

    sbend = gf.components.bend_s(
        cross_section=x_sbend, size=(sbend_length, -dy - wg_width / 2)
    )
    sbend_ref = c.add_ref(sbend)
    sbend_ref.connect(port="in", other=taper1_mirror.ports["o1"], allow_width_mismatch=True)
    refs.append(sbend_ref)

    coupler_ref = c.add_ref(gf.components.straight(length=coupler_l,width=wg_width,layer=layer_main))
    coupler_ref.connect(port="o1", other=sbend_ref.ports["out"], allow_width_mismatch=True)
    refs.append(coupler_ref)

    sbend_ref_mirror = c.add_ref(sbend).mirror_x()
    sbend_ref_mirror.connect(port="in", other=coupler_ref.ports["o2"])
    refs.append(sbend_ref_mirror)

    taper1_ref_2 = c.add_ref(gf.components.taper(length=taper1_length, width1=wg_width, width2=width_resonator, layer=layer_main))
    taper1_ref_2.connect(port="o1", other=sbend_ref_mirror.ports["out"], allow_width_mismatch=True)
    refs.append(taper1_ref_2)

    # --- Attach fish component ---
    fish_ref = c.add_ref(fish_component)
    fish_ref.connect(port="o1", other=taper1_ref_2.ports["o2"], allow_width_mismatch=True)
    refs.append(fish_ref)

    # --- Spine component ---
    comb_spine = c.add_ref(gf.components.straight(length=3, width=0.972 if resonator=="fish" else 0.55, layer=layer_main))
    comb_spine.connect(port="o1", other=fish_ref.ports["o2"], allow_width_mismatch=True)
    refs.append(comb_spine)
    if resonator == "extractor":
        comb_spine.dmovex(-0.2)


    # --- SPRING cross-section + geometry ---
    spring_cs = gf.CrossSection(
        sections=[gf.Section(width=0.15, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    # Build the spring segments
    spring_refs = create_spring_vertical(c=c, cross_section=spring_cs,comb_spine=comb_spine)
    refs.append(spring_refs)

    # --- Vertical supports ---
    cnt1_x = taper1_ref.ports["o2"].center[0] / 1000
    cnt1_y = taper1_ref.ports["o2"].center[1] / 1000
    cnt2_x = taper1_ref_2.ports["o2"].center[0] / 1000+1.3
    cnt2_y = taper1_ref.ports["o2"].center[1] / 1000

    vertical_supports = create_vertical_supports(c=c,layer=layer_main,cnt1=(cnt1_x, cnt1_y),cnt2=(cnt2_x, cnt2_y),dy=dy)
    refs.append(vertical_supports)

    # --- Construct top waveguide geometry with boolean OR ---
    top_waveguide = gf.boolean(
        A=taper_small_in_ref, B=taper1_ref, operation="or", layer=layer_main
    )

    top_waveguide = merge_references(top_waveguide, refs, layer_main)

    # Merge all references

    # Create mirrored waveguide (bot_waveguide)
    bot_waveguide_ref = gf.Component().add_ref(top_waveguide).mirror_y()
    # Shift if necessary: .dmovey(dy*0) does nothing, but keep it for clarity:
    bot_waveguide_ref.dmovey(dy * 0)

    # Combine top + bottom waveguides
    combined_dc = gf.boolean(A=top_waveguide, B=bot_waveguide_ref, operation="or", layer=layer_main)

    ######## Thick DC #######

    thick_cs = gf.CrossSection(
        sections=[gf.Section(width=3, layer=layer_main, port_names=("in", "out"))],
        radius_min=0.15
    )

    thick_dc = gf.Component()

    # Straight section along the first taper
    straight1 = gf.components.straight(length=output_taper_length + 2 * taper1_length, cross_section=thick_cs)
    s1 = thick_dc.add_ref(straight1)
    s1.connect(port="in", other=taper_small_in_ref.ports["o2"], allow_width_mismatch=True)
    s1.dmovex(-output_taper_length)

    # First S-bend section (same as the original code)
    thick_s_bend1 = gf.components.bend_s(size=(sbend_length, -dy - wg_width / 2), cross_section=thick_cs)
    b1 = thick_dc.add_ref(thick_s_bend1)
    b1.connect(port="in", other=s1.ports["out"])

    # Straight coupler section along the resonator
    straight2 = gf.components.straight(length=coupler_l, cross_section=thick_cs)
    s2 = thick_dc.add_ref(straight2)
    s2.connect(port="in", other=b1.ports["out"])

    # Second S-bend section (mirror of the first one)
    thick_s_bend2 = gf.components.bend_s(size=(sbend_length, dy + wg_width / 2), cross_section=thick_cs)
    b2 = thick_dc.add_ref(thick_s_bend2)
    b2.connect(port="in", other=s2.ports["out"])

    # Final straight section after the second S-bend
    final_straight = gf.components.straight(length=taper1_length + 5.379, cross_section=thick_cs)
    s3 = thick_dc.add_ref(final_straight)
    s3.connect(port="in", other=b2.ports["out"])

    # Create bottom mirrored version
    thick_dc_ref_bot = gf.Component().add_ref(thick_dc).mirror_y()

    # Combine top and bottom thick DC into one component
    combined_thick_dc = gf.boolean(A=thick_dc, B=thick_dc_ref_bot, operation="or", layer=layer_main)

    #########################

    # --- Subtract combined waveguide from a large rectangle to get final geometry ---
    bounding_rect = gf.components.straight(length=7.3,width=dy * 2.5 + 0.6,layer=layer_main)
    bounding_rect_ref = c.add_ref(bounding_rect).dmovex(25.5)
    bounding_ext = c.add_ref(gf.components.straight(length=clearance_width,width=50,layer=layer_main)).dmovex(-21.6-clearance_width)
    bounding_rect_ref = gf.boolean(A=bounding_rect_ref, B=bounding_ext, operation="or", layer=layer_main)
    # pad_h = 150
    # pad_l = 150
    # ext1 = c.add_ref(gf.components.straight(length=pad_x_offset+10, width=6, layer=layer_main)).dmovex(30)
    # if pad_y_offset>0:
    #     ext2 = c.add_ref(gf.components.straight(length=6, width=pad_y_offset+6, layer=layer_main)).dmovex(40+pad_x_offset).dmovey(pad_y_offset/2)
    #     ext1 = gf.boolean(A=ext1, B=ext2, operation="or", layer=layer_main)
    # bounding_rect_ref = gf.boolean(A=bounding_rect_ref, B=ext1, operation="or", layer=layer_main)

    bounding_rect_ref = c.add_ref(gf.boolean(A=bounding_rect_ref, B=combined_thick_dc, operation="or", layer=layer_main))

    dc_positive = gf.boolean(A=bounding_rect_ref, B=combined_dc, operation="A-B", layer=layer_main)


    result_c= gf.Component()
    result_c.add_ref(dc_positive)
    # result_c.add_ref(gf.components.straight(length=pad_l, width=pad_h, layer=layers["coarse_ebl_layer"])).dmovex(30+pad_x_offset).dmovey(
    #     72+pad_y_offset).flatten()

    return result_c

def create_bent_taper(taper_length, taper_width1, taper_width2, bend_radius, bend_angle, enable_sbend=False):
    """
    Creates a bent taper transitioning from taper_width1 to taper_width2
    with a specified bend radius and angle.

    Args:
        taper_length (float): Length of the taper (straight section).
        taper_width1 (float): Width at the wider end of the taper.
        taper_width2 (float): Width at the narrower end of the taper.
        bend_radius (float): Radius of the bend.
        bend_angle (float): Angle of the bend in degrees.

    Returns:
        gf.Component: The bent taper component.
    """
    debug=False
    c = gf.Component()

    if bend_angle == 0:
        # Regular straight taper
        path = gf.path.straight(length=taper_length)
        taper_cross_section = gf.path.transition(
            cross_section1=gf.CrossSection(sections=[gf.Section(width=taper_width1, layer=(1, 0), name="waveguide")]),
            cross_section2=gf.CrossSection(sections=[gf.Section(width=taper_width2, layer=(1, 0), name="waveguide")]),
            width_type="sine",
        )
        straight_taper = gf.path.extrude_transition(path, transition=taper_cross_section)
        straight_taper_ref = c.add_ref(straight_taper)

        # Add ports
        c.add_port(
            name="o1",
            center=(0, 0),
            width=taper_width1,
            orientation=180,
            layer=(1, 0)
        )
        c.add_port(
            name="o2",
            center=(taper_length, 0),
            width=taper_width2,
            orientation=0,
            layer=(1, 0)
        )
        return c


    # Create the path
    path = gf.Path()
    arc_length = 0
    bend_angle_rad=0

    if enable_sbend:
        # Create an S-bend
        euler1 = gf.path.euler(radius=bend_radius, angle=bend_angle / 2, p=0.5)
        euler2 = gf.path.euler(radius=bend_radius, angle=-bend_angle / 2, p=0.5)
        path.append(euler1)
        path.append(euler2)
        # Calculate S-bend length
        arc_length = euler1.length() + euler2.length()
    else:
        # Regular bend
        path.append(gf.path.arc(radius=bend_radius, angle=bend_angle))
        # Calculate arc length and remaining straight length
        bend_angle_rad = np.radians(bend_angle)
        arc_length = bend_radius * bend_angle_rad


    straight_length = max(taper_length - arc_length, 0)

    if debug:
        print(f"sbend={enable_sbend}, taper_length={taper_length}, arc_length={arc_length}, straight_length={straight_length}")


    if straight_length > 0:
        path.append(gf.path.straight(length=straight_length))

    # Define the cross-section transition for the taper
    taper_cross_section = gf.path.transition(
        cross_section1=gf.CrossSection(sections=[gf.Section(width=taper_width1, layer=(1, 0), name="waveguide")]),
        cross_section2=gf.CrossSection(sections=[gf.Section(width=taper_width2, layer=(1, 0), name="waveguide")]),
        width_type="sine",
    )

    # Extrude the path to create the bent taper
    bent_taper = gf.path.extrude_transition(path, transition=taper_cross_section)
    # return bent_taper

    # Add the bent taper to the component
    bent_taper_ref = c.add_ref(bent_taper)

    # Add ports
    # Input port at the beginning of the taper
    c.add_port(
        name="o1",
        center=(0, 0),
        width=taper_width1,
        orientation=180,
        layer=(1, 0)
    )

    # Output port at the end of the taper
    if straight_length > 0:
        # For a straight section after the bend
        end_x = bend_radius * np.sin(bend_angle_rad) + straight_length * np.cos(bend_angle_rad)
        end_y = bend_radius * (1 - np.cos(bend_angle_rad)) + straight_length * np.sin(bend_angle_rad)
    else:
        # Only the arc
        end_x = bend_radius * np.sin(bend_angle_rad)
        end_y = bend_radius * (1 - np.cos(bend_angle_rad))

    c.add_port(
        name="o2",
        center=(end_x, end_y),
        width=taper_width2,
        orientation=np.degrees(bend_angle_rad),
        layer=(1, 0)
    )

    return c

def create_rounded_rectangle(length, width, corner_radius, layer):
    """Creates a rectangle with rounded corners as a polygon."""
    if corner_radius > 0:
        rect = gf.Component()
        points = [
            (corner_radius, 0),
            (length - corner_radius, 0),
            (length, corner_radius),
            (length, width - corner_radius),
            (length - corner_radius, width),
            (corner_radius, width),
            (0, width - corner_radius),
            (0, corner_radius),
        ]
        # Add rounded corners using arcs
        rect.add_polygon(points, layer=layer)
        return rect
    else:
        # Fallback to a standard rectangle if no corner radius is specified
        return gf.components.rectangle(size=(length, width), layer=layer)

def add_electrodes( c, length_mmi, taper_length, fish_center, electrode_gap, layer=(1, 0)):
    """
    Adds electrodes to the design with elongation always included.

    Args:
        c: The component to which electrodes will be added.
        length_mmi (float): Length of the MMI section.
        taper_length (float): Length of the taper section.
        fish_center (float): Center alignment for the electrodes.
        electrode_gap (float): Gap between the electrodes.
        layer (tuple): GDS layer for the electrodes.
    """
    elongation_width = 2
    elongation_length = 20
    ele_taper_length = 4

    # Add the middle straight and taper electrodes
    middle_straight = c.add_ref(gf.components.straight(length=3, width=1, layer=layer)).dmovex(
        length_mmi + taper_length * 2 - fish_center
    )
    middle_taper = c.add_ref(gf.components.taper(length=.5, width1=2, width2=1, layer=layer)).dmovex(
        length_mmi + taper_length * 2 - fish_center
    )

    x = gf.CrossSection(sections=[gf.Section(width=1, layer=layer, port_names=("in", "out"))])
    x2 = gf.CrossSection(sections=[gf.Section(width=elongation_width, layer=layer, port_names=("in", "out"))])

    # Add elongation to the middle electrode
    middle_elongation_taper = c.add_ref(
        gf.components.taper(length=ele_taper_length, width1=elongation_width, width2=1, layer=layer)
    )
    middle_elongation_taper.connect("o2", middle_straight.ports["o2"], allow_width_mismatch=True)

    middle_elongation_straight = c.add_ref(
        gf.components.straight(length=elongation_length+300, width=elongation_width, layer=layer)
    )
    middle_elongation_straight.connect("o1", middle_elongation_taper.ports["o1"], allow_width_mismatch=True)

    pad_middle = c.add_ref(
        gf.components.straight(length=elongation_length + 130, width=130, layer=layer)
    )
    pad_middle.connect("o1", middle_elongation_straight.ports["o2"], allow_width_mismatch=True)

    # Add upper and lower electrodes
    for direction, y_offset, angle, rot_ang in [("up", 6.5, 76.5,30), ("down", -6.5, -76.5, -30)]:
        straight_section = c.add_ref(gf.components.straight(length=3, width=1, layer=layer)).drotate(rot_ang).dmovex(
            length_mmi + taper_length * 2 - 0.017 - fish_center-1
        ).dmovey(y_offset)
        taper_section = c.add_ref(gf.components.taper(length=1.39, width1=0.01, width2=1.4, layer=layer)).drotate(angle).dmovex(
            length_mmi + taper_length * 2 - fish_center-.9
        ).dmovey(y_offset + (electrode_gap / 2 - 1.6 if direction == "up" else -electrode_gap / 2 + 1.6))

        sbend1 = c.add_ref(
            gf.components.bend_s(size=(4, 2.2 if direction == "up" else -2.2), cross_section=x)
        )
        sbend1.connect("in", straight_section.ports["o2"])

        elongation_taper = c.add_ref(
            gf.components.taper(length=ele_taper_length, width1=elongation_width, width2=1, layer=layer)
        )
        elongation_taper.connect("o2", sbend1.ports["out"], allow_width_mismatch=True)

        elongation_straight = c.add_ref(
            gf.components.straight(length=elongation_length, width=elongation_width, layer=layer)
        )
        elongation_straight.connect("o1", elongation_taper.ports["o1"], allow_width_mismatch=True)

        sbend2 = c.add_ref(
            gf.components.bend_s(size=(40, 30.5 if direction == "up" else -30.5), cross_section=x2)
        )
        sbend2.connect("in", elongation_straight.ports["o2"], allow_width_mismatch=True)

        elongation_straight1 = c.add_ref(
            gf.components.straight(length=elongation_length+100, width=elongation_width, layer=layer)
        )
        elongation_straight1.connect("o1", sbend2.ports["out"], allow_width_mismatch=True)

        pad1 = c.add_ref(
            gf.components.straight(length=elongation_length + 130, width=130, layer=layer)
        )
        pad1.connect("o1", elongation_straight1.ports["o2"], allow_width_mismatch=True)

    return c

def add_fish_components( c, gds_file, length_mmi, taper_length, taper_separation):
    """
    Adds fish components to the design and defines ports for alignment and connection.

    Args:
        c: The parent component to which the fish components will be added.
        gds_file (str): Path to the GDS file for the fish component.
        length_mmi (float): Length of the MMI section.
        taper_length (float): Length of the taper section.
        taper_separation (float): Separation of the fish components.

    Returns:
        list: A list of references to the added fish components.
    """
    # Import the fish component from the GDS file
    fish_component = gf.import_gds(Path(gds_file))

    # Add ports to the imported fish component
    fish_component.add_port(
        name="o1",
        center=(0, 0),  # Define the input port position (update as needed)
        width=0.5,  # Update the width as required
        orientation=180,  # Facing left
        layer=(1, 0)  # Adjust the layer if necessary
    )
    fish_component.add_port(
        name="o2",
        center=(fish_component.size_info.width, 0),  # Define the output port position
        width=0.5,  # Update the width as required
        orientation=0,  # Facing right
        layer=(1, 0)  # Adjust the layer if necessary
    )

    # Add the fish components to the parent component
    fish_ref_1 = c.add_ref(fish_component)
    fish_ref_1.dmove((length_mmi + taper_length * 2 - 4, taper_separation / 2))

    fish_ref_2 = c.add_ref(fish_component)
    fish_ref_2.dmove((length_mmi + taper_length * 2 - 4, -taper_separation / 2))

    return [fish_ref_1, fish_ref_2]

def create_mmi( params=None):
    """
    Creates a 2x2 MMI structure with specified parameters.

    Args:
        params (dict): Dictionary of parameters for the MMI structure. If not provided, default values are used.

    Returns:
        tuple: The MMI component and optional electrodes component.
    """
    # Default parameters
    default_params = {
        "resonator_type": "fish",
        "length_mmi": 79,
        "width_mmi": 6,
        "total_width_mmi": 30,
        "name": None,
        "debug": False,
        "taper_separation": 2.0308,
        "taper_length_out": 10,
        "taper_length_in": 10,
        "taper_width": 1.2,
        "taper_tip": 0.08,
        "bend_radius": 25,
        "bend_angle": 0,
        "corner_support_width": 1,
        "fish_center": 2.2,
        "extractor_center": 2.97,
        "electrode_gap": 1,
        "enable_sbend": True,
        "weird_support": False,
    }

    # Update default parameters with input parameters
    if params is not None:
        default_params.update(params)
    params = default_params

    # Compute dependent parameters
    params["mmi_support_length"] = (params["total_width_mmi"] - params["width_mmi"]) / 2

    # Create a new component for the MMI
    c = gf.Component()
    c_ele = gf.Component()

    # Define the main MMI region
    mmi_section = gf.components.straight(
        length=params["length_mmi"], width=params["width_mmi"], layer=(1, 0)
    )
    mmi_ref = c.add_ref(mmi_section)
    mmi_ref.dmove((params["taper_length_out"], 0))  # Position the MMI after the input tapers

    # Create bent tapers
    taper_in = create_bent_taper(
        params["taper_length_in"],
        params["taper_width"],
        params["taper_tip"],
        params["bend_radius"],
        params["bend_angle"],
        params["enable_sbend"],
    )

    # Place the input tapers
    taper_in1 = c.add_ref(taper_in).mirror_x().dmove(
        (params["taper_length_out"], params["taper_separation"] / 2)
    )
    taper_in2 = c.add_ref(taper_in).mirror_x().mirror_y().dmove(
        (params["taper_length_out"], -params["taper_separation"] / 2)
    )
    coupler = gf.boolean(A=taper_in1, B=taper_in2, operation="or", layer=(1, 0))

    if params["bend_angle"] > 0 and params["enable_sbend"] is False:
        # Process for taper_in1
        rail_taper = gf.components.taper(length=60, width1=60, width2=15, layer=(1, 0))
        rail_taper_ref_1 = gf.Component().add_ref(rail_taper)
        rail_taper_ref_1.connect(port="o2", other=taper_in1.ports["o2"], allow_width_mismatch=True)

        larger_taper = gf.components.taper(length=60, width1=100, width2=25, layer=(1, 0))  # Larger taper
        larger_taper_ref_1 = gf.Component().add_ref(larger_taper)
        larger_taper_ref_1.connect(port="o2", other=taper_in1.ports["o2"], allow_width_mismatch=True)

        # Add a straight line to the rail taper for taper_in1
        straight_line_rail_1 = gf.components.straight(length=400, width=60, layer=(1, 0))
        straight_line_ref_rail_1 = gf.Component().add_ref(straight_line_rail_1)
        straight_line_ref_rail_1.connect(port="o1", other=rail_taper_ref_1.ports["o1"], allow_width_mismatch=True)

        # Add a straight line to the larger taper for taper_in1
        straight_line_larger_1 = gf.components.straight(length=400, width=150, layer=(1, 0))
        straight_line_ref_larger_1 = gf.Component().add_ref(straight_line_larger_1)
        straight_line_ref_larger_1.connect(port="o1", other=larger_taper_ref_1.ports["o1"], allow_width_mismatch=True)

        # Combine rail taper and straight line
        combined_rail_1 = gf.boolean(A=rail_taper_ref_1, B=straight_line_ref_rail_1, operation="or", layer=(1, 0))

        # Combine larger taper and straight line
        combined_larger_1 = gf.boolean(A=larger_taper_ref_1, B=straight_line_ref_larger_1, operation="or", layer=(1, 0))

        # Subtract the combined rail from the combined larger taper
        subtracted_geom_1 = gf.boolean(A=combined_larger_1, B=combined_rail_1, operation="A-B", layer=(1, 0))
        c.add_ref(subtracted_geom_1)

        # Process for taper_in2
        rail_taper_ref_2 = gf.Component().add_ref(rail_taper)
        rail_taper_ref_2.connect(port="o2", other=taper_in2.ports["o2"], allow_width_mismatch=True)

        larger_taper_ref_2 = gf.Component().add_ref(larger_taper)
        larger_taper_ref_2.connect(port="o2", other=taper_in2.ports["o2"], allow_width_mismatch=True)

        # Add a straight line to the rail taper for taper_in2
        straight_line_rail_2 = gf.components.straight(length=400, width=60, layer=(1, 0))
        straight_line_ref_rail_2 = gf.Component().add_ref(straight_line_rail_2)
        straight_line_ref_rail_2.connect(port="o1", other=rail_taper_ref_2.ports["o1"], allow_width_mismatch=True)

        # Add a straight line to the larger taper for taper_in2
        straight_line_larger_2 = gf.components.straight(length=400, width=150, layer=(1, 0))
        straight_line_ref_larger_2 = gf.Component().add_ref(straight_line_larger_2)
        straight_line_ref_larger_2.connect(port="o1", other=larger_taper_ref_2.ports["o1"], allow_width_mismatch=True)

        # Combine rail taper and straight line
        combined_rail_2 = gf.boolean(A=rail_taper_ref_2, B=straight_line_ref_rail_2, operation="or", layer=(1, 0))

        # Combine larger taper and straight line
        combined_larger_2 = gf.boolean(A=larger_taper_ref_2, B=straight_line_ref_larger_2, operation="or", layer=(1, 0))

        # Subtract the combined rail from the combined larger taper
        subtracted_geom_2 = gf.boolean(A=combined_larger_2, B=combined_rail_2, operation="A-B", layer=(1, 0))
        c.add_ref(subtracted_geom_2)

    # Load and add resonator structure
    if params["resonator_type"] == "fish":
        taper_resonator = create_bent_taper(
            params["taper_length_out"],
            taper_width1=params["taper_width"],
            taper_width2=0.68-0.25,
            bend_radius=20,
            bend_angle=13.3*0,
        )
        taper_resonator_ref = c.add_ref(taper_resonator).dmove(
            (params["length_mmi"] + params["taper_length_out"], params["taper_separation"] / 2)
        )
        taper_resonator_mirror_ref = c.add_ref(taper_resonator).dmove(
            (params["length_mmi"] + params["taper_length_out"], params["taper_separation"] / 2)
        ).mirror_y()

        fish_refs = add_fish_components(
            c, 'QT14.gds', params["length_mmi"], params["taper_length_out"], params["taper_separation"]
        )

        fish_refs[0].connect(
            port="o1", other=taper_resonator_ref.ports["o2"], allow_width_mismatch=True
        )
        fish_refs[1].connect(
            port="o1", other=taper_resonator_mirror_ref.ports["o2"], allow_width_mismatch=True
        )

        # add_electrodes(
        #     c, params["length_mmi"] + 4.2, params["taper_length_out"], params["fish_center"], params["electrode_gap"]
        # )
        # ele = add_electrodes(
        #     c_ele, params["length_mmi"] + 4.2, params["taper_length_out"], params["fish_center"], params["electrode_gap"], layer=(2, 0)
        # )

    elif params["resonator_type"] == "extractor":
        taper_resonator = create_bent_taper(
            params["taper_length_out"],
            taper_width1=params["taper_width"],
            taper_width2=0.54,
            bend_radius=20,
            bend_angle=15*0,
        )
        taper_resonator_ref = c.add_ref(taper_resonator).dmove(
            (params["length_mmi"] + params["taper_length_out"], params["taper_separation"] / 2)
        )
        taper_resonator_mirror_ref = c.add_ref(taper_resonator).dmove(
            (params["length_mmi"] + params["taper_length_out"], params["taper_separation"] / 2)
        ).mirror_y()

        fish_refs = add_fish_components(
            c, 'QT10.gds', params["length_mmi"], params["taper_length_out"], params["taper_separation"]
        )

        fish_refs[0].connect(
            port="o1", other=taper_resonator_ref.ports["o2"], allow_width_mismatch=True
        )
        fish_refs[1].connect(
            port="o1", other=taper_resonator_mirror_ref.ports["o2"], allow_width_mismatch=True
        )

    def add_supports(c, positions, width1, width2, rotate_angle=90, mirror=False):
        for i, pos in enumerate(positions):
            taper = gf.components.taper(
                length=params["mmi_support_length"],
                width1=width1,
                width2=width2,
                layer=(1, 0),
            )
            taper_ref = c.add_ref(taper)
            taper_ref.drotate(rotate_angle)
            if mirror and (i % 2 == 1):
                taper_ref.mirror_y()
            taper_ref.dmove(pos)

    # Corner taper positions
    corner_positions = [
        (10 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3),
        (10 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3),
        (params["length_mmi"] + 9 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3),
        (params["length_mmi"] + 9 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3),
    ]

    # Center taper positions
    center_positions = [
        (10 + params["length_mmi"] / 3, -params["width_mmi"] - params["mmi_support_length"] + 3),
        (10 + params["length_mmi"] / 3, params["width_mmi"] + params["mmi_support_length"] - 3),
        (10 + params["length_mmi"] * 2 / 3, -params["width_mmi"] - params["mmi_support_length"] + 3),
        (10 + params["length_mmi"] * 2 / 3, params["width_mmi"] + params["mmi_support_length"] - 3),
    ]

    # Add corner supports
    add_supports(
        c, corner_positions,
        width1=0.1 * params["mmi_support_length"] + params["corner_support_width"],
        width2=params["corner_support_width"],
        rotate_angle=90,
        mirror=True,
    )

    # Add center supports
    add_supports(
        c, center_positions,
        width1=0.1 * params["mmi_support_length"] + 0.6,
        width2=0.25,
        rotate_angle=90,
        mirror = True,
    )

    if params["weird_support"]:
        params["mmi_support_length"]=2
        corner_positions = [
            (10 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3-.5),
            (10 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3+.5),
            (params["length_mmi"] + 9 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3-.5),
            (params["length_mmi"] + 9 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3+.5),
        ]
        add_supports(
            c,
            positions=corner_positions,
            width1=40,
            width2=0.25,
            rotate_angle=90,
            mirror=True,
        )
        center_positions = [
            (10 + params["length_mmi"] / 3, -params["width_mmi"] - params["mmi_support_length"] + 3 - 0.25),  # Lower support (-0.25)
            (10 + params["length_mmi"] / 3, params["width_mmi"] + params["mmi_support_length"] - 3 + 0.25),  # Upper support (+0.25)
            (10 + params["length_mmi"] * 2 / 3, -params["width_mmi"] - params["mmi_support_length"] + 3 - 0.25),  # Lower support (-0.25)
            (10 + params["length_mmi"] * 2 / 3, params["width_mmi"] + params["mmi_support_length"] - 3 + 0.25),  # Upper support (+0.25)
        ]
        add_supports(
            c, center_positions,
            width1=40,
            width2=0.25,
            rotate_angle=90,
            mirror=True,
        )
        # c.show()


    # Combine main MMI and coupler
    device = gf.boolean(A=c, B=coupler, operation="or", layer=(1, 0))

    if params["name"]:  # Set the name if provided
        device.name = params["name"]

    # return Device, ele

    return device

# @gf.cell
def logo( name=None):
    c = gf.Component()
    Big_CR = gf.components.circle(radius=4, layer=(1, 0))
    Small_CR = c.add_ref(gf.components.circle(radius=.7, layer=(1, 0))).dmovex(-5)
    Mid_CR1 = c.add_ref(gf.components.circle(radius=1.1, layer=(1, 0))).dmovex(3).dmovey(-3)
    Mid_CR2 = c.add_ref(gf.components.circle(radius=1.35, layer=(1, 0))).dmovex(3).dmovey(-3)
    Mid_CR3 = c.add_ref(gf.components.circle(radius=1.75, layer=(1, 0))).dmovex(3).dmovey(-3)
    Mid_CR4 = c.add_ref(gf.components.circle(radius=2, layer=(1, 0))).dmovex(3).dmovey(-3)
    CR = c.add_ref(gf.boolean(A=Big_CR, B=Mid_CR4, operation="A-B", layer=(1, 0)))

    right_bottom_small_cir = c.add_ref(gf.boolean(A=Big_CR, B=Mid_CR1, operation="and", layer=(1, 0)))
    right_bottom_shape = gf.boolean(A=Mid_CR3, B=Mid_CR2, operation="A-B", layer=(1, 0))
    right_bottom_shape = gf.boolean(A=right_bottom_shape, B=right_bottom_small_cir, operation="or", layer=(1, 0))

    PT = c.add_ref(gf.path.extrude(
        gf.Path([(0.0000, 4.0000), (0.0000, 2.5000), (-1.4000, 1.1000), (-1.4000, -1.1000), (0.0000, -2.5000), (0.0000, -4.0000)]), layer=(1, 0),
        width=0.3))
    ToCut = c.add_ref(gf.components.straight(length=1, layer=(1, 0), width=0.3)).drotate(90).dmovex(-1.1).dmovey(0)
    x = gf.CrossSection(sections=[gf.Section(width=0.3, layer=(1, 0), port_names=("in", "out"))])
    sbend1 = c.add_ref(gf.components.bend_s(size=(1.15, .5), cross_section=x)).dmovex(-4.5).dmovey(-0.2)
    sbend2 = c.add_ref(gf.components.bend_s(size=(1.15, -.5), cross_section=x))
    sbend2.connect(port="in", other=sbend1.ports["out"])
    sbend3 = c.add_ref(gf.components.bend_s(size=(1.15, .5), cross_section=x))
    sbend3.connect(port="in", other=sbend2.ports["out"])
    sbend3_cut = c.add_ref(gf.boolean(A=sbend3, B=ToCut, operation="A-B", layer=(1, 0)))

    mrg = gf.boolean(A=sbend3_cut, B=sbend2, operation="or", layer=(1, 0))

    mrg = gf.boolean(A=mrg, B=sbend1, operation="or", layer=(1, 0))

    mrg = gf.boolean(A=mrg, B=PT, operation="or", layer=(1, 0))

    center_logo = gf.boolean(A=CR, B=mrg, operation="A-B", layer=(1, 0))
    mrg1 = gf.boolean(A=center_logo, B=right_bottom_shape, operation="or", layer=(1, 0))
    qt_logo = gf.boolean(A=mrg1, B=Small_CR, operation="or", layer=(1, 0))

    s1 = gf.Component().add_ref(gf.components.straight(length=0.3, width=1.5, layer=(1, 0))).dmovex(2.85).dmovey(-5)
    qt_logo = gf.boolean(A=qt_logo, B=s1, operation="A-B", layer=(1, 0))

    if not name==None:
        qt_logo.name = name

    return qt_logo

def debug(self):
    c = gf.Component("TOP")
    straight_c = gf.components.straight(4.5)
    straight_ref = c.add_ref(straight_c)
    c.show()

def unite_array( component, rows=1, cols=1, spacing=(10, 10), name=None, layer=(1,0)):
    """
    Creates an array of a given component and unites all instances into a single geometry.

    Parameters:
        component (gf.Component): The component to array and unite.
        rows (int): Number of rows in the array.
        cols (int): Number of columns in the array.
        spacing (tuple): Spacing (x, y) between instances in the array.

    Returns:
        gf.Component: A new component with all instances united into one geometry.
    """
    # Early return if only one instance is needed
    if rows == 1 and cols == 1:
        if name:
            component.name = name
        return component

    # Create a new component to store the unified array
    c = gf.Component()

    # Place the first instance to initialize merged geometry
    merged_device = c.add_ref(component)

    # Loop through the array and place each instance, uniting it with merged_device
    for row in range(rows):
        for col in range(cols):
            # Skip the first instance since it's already added as merged_device
            if row == 0 and col == 0:
                continue

            # Calculate the position for the next component
            x_pos = col * spacing[0]
            y_pos = row * spacing[1]

            # Place and unite each instance with the merged_device
            next_device = gf.Component().add_ref(component).dmove((x_pos, y_pos))

            merged_device = gf.boolean(A=merged_device, B=next_device, operation="or", layer=layer)

    # Name the final merged component
    if name:
        merged_device.name = name

    y_center = merged_device.size_info.center[1]
    merged_device.add_port(name="o1", center=(0, y_center), width=0.5, orientation=180, layer=layer)
    merged_device.add_port(name="o2", center=(merged_device.size_info.width, y_center), width=0.5, orientation=0, layer=layer)

    return merged_device

def add_scalebar( component, size=100, position=(0, 0), font_size=15):
    """
    Adds a scalebar to the component with dynamically calculated text offset.

    Parameters:
        component: The component to which the scalebar will be added.
        size: The size of the scalebar in micrometers.
        position: The starting position of the scalebar (x, y).
        font_size: Font size of the scalebar.
    """
    # Add the scalebar line
    scalebar = gf.components.rectangle(size=(size, 2),  # 100 µm long and 5 µm thick
                                       layer=(1, 0))
    scalebar_ref = component.add_ref(scalebar)
    scalebar_ref.dmove(position).flatten()

    # Format the size with spaces between digits
    formatted_size = " ".join(str(size))

    # Create a temporary text component to measure its bounding box
    temp_label = gf.components.text(text=formatted_size, size=font_size)
    bbox = temp_label.bbox_np()
    label_width = bbox[1][0] - bbox[0][0]  # Width: max_x - min_x
    label_height = bbox[1][1] - bbox[0][1]  # Height: max_y - min_y

    # Calculate text offset dynamically
    text_offset_x = -label_width / 2  # Center the text horizontally
    text_offset_y = -label_height - 2  # Position above the scalebar with padding

    # Add the scalebar label
    label = gf.components.text(text=formatted_size, size=font_size, position=(position[0] + size / 2 + text_offset_x,  # Center horizontally
                                                                              position[1] + text_offset_y  # Position above the scalebar
                                                                              ))
    component.add_ref(label).flatten()

def create_bbox_component( length_mmi, total_width_mmi,taper_length=10,clearance_width=40):
    bbox_component = gf.Component()
    bbox_component.add_ref(
        gf.components.straight(length=length_mmi + 38.3, width=total_width_mmi, layer=(1, 0))
    ).dmovex(-13)

    bbox_component.add_ref(gf.components.straight(length=clearance_width, width=40, layer=(1, 0))).dmovex(-clearance_width-taper_length+10)

    return bbox_component

def add_mmi_patterns( c, bbox_component, params=None):
    default_params = {
        "is_resist_positive": True,
        "resonator_type": "fish",
        "length_mmi": 79,
        "width_mmi": 6,
        "total_width_mmi": 30,
        "taper_length_in": 10,
        "y_spacing": 30,
    }

    # Update default parameters with input parameters
    if params is not None:
        default_params.update(params)
    params = default_params

    mmi = create_mmi(params=params)

    if params["is_resist_positive"]:
        mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

    # # c.add_ref(unite_array(mmi, cols=1, rows=2, spacing=(0, 60))).dmovey(offset_y).dmovex(params["taper_length_in"]-10)
    # return unite_array(mmi, cols=1, rows=2, spacing=(0, params["y_spacing"]))
    return mmi

def add_mmi_patterns_with_sbend( c, bbox_component, is_resist_positive, resonator_type, offset_y, offset_x):
    """
    Adds MMI patterns for fiber coupling with an S-bend to the component.

    Args:
        c (gf.Component): The component to which patterns are added.
        bbox_component (gf.Component): The bounding box component.
        is_resist_positive (bool): Indicates if the resist is positive.
        resonator_type (str): The type of resonator.
        offset_y (float): Y-offset for placement.
    """
    # Define MMI parameters
    params = {
        "resonator_type": resonator_type,
        "length_mmi": 79,
        "width_mmi": 6,
        "total_width_mmi": 30,
        "bend_angle": 20,
        "taper_length_in": 10,
        "enable_sbend": True,  # Enable S-bend for this function
    }

    # Create MMI
    mmi = create_mmi(params=params)

    # Apply boolean operation if resist is positive
    if is_resist_positive:
        mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

    # Subtract custom polygons
    # custom_polygon_points = get_custom_polygon_points(resonator_type)
    # mmi = subtract_custom_polygon(mmi, custom_polygon_points)

    # Add MMI pattern to the component
    c.add_ref(
        unite_array(mmi, cols=1, rows=2, spacing=(0, 60), name=f"mmi_{resonator_type}_s_bend")
    ).dmovey(offset_y).dmovex(offset_x)

def add_mmi_patterns_fiber( c, bbox_component, is_resist_positive, resonator_type):
    params = {
        "resonator_type": resonator_type,
        "length_mmi": 79,
        "width_mmi": 6,
        "total_width_mmi": 30,
        "bend_angle": 30,
        "taper_length_in": 25,
        "enable_sbend": False,
    }
    mmi = create_mmi(params=params)

    if is_resist_positive:
        mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

    # custom_polygon_points = get_custom_polygon_points(resonator_type)
    # mmi = subtract_custom_polygon(mmi, custom_polygon_points)

    remove_polygon_points = get_remove_polygon_points()
    mmi = subtract_custom_polygon(mmi, remove_polygon_points)

    return unite_array(mmi, cols=1, rows=4, spacing=(0, 100), name=f"mmi_{resonator_type}_fiber")

def add_bulls_eye( c, n_bulls_eye, offset_x):
    a = gf.components.circle(radius=5.8, layer=(1, 0))
    s1 = gf.Component().add_ref(gf.components.straight(length=0.2, width=20, layer=(1, 0))).dmovex(-0.1)
    a = gf.boolean(A=a, B=s1, operation="A-B", layer=(1, 0))

    gds_file = Path('Bulls_Eye_Layout_v1.1.gds')
    b = gf.import_gds(gds_file)
    b.name = "GDS_Import"

    c.add_ref(unite_array(b, cols=n_bulls_eye, rows=1, spacing=(12.5, 12.5), name="Bulls-eye")).dmovey(-20).dmovex(offset_x + 32)

def add_logos( c):
    return unite_array(logo(name="Logo"), cols=1, rows=1, spacing=(30, 120), name="logos")

def add_scalebars( c, offset_x, offset_y):
    add_scalebar(component=c, size=100, position=(offset_x, offset_y), font_size=10)
    add_scalebar(component=c, size=10, position=(offset_x +5, offset_y - 5), font_size=5)

def get_custom_polygon_points( resonator_type):
    if resonator_type == "extractor":
        return [
            (100.33500, 5.39900),
            (99.96300, 6.93300),
            (101.87500, 7.98700),
            (101.85600, 17.35900),
            (120.05600, 19.04300),
            (119.78000, 6.97400),
            (103.23800, 6.96300),
            (101.30600, 6.55400),
        ]
    else:
        return [
            (101.10500, 5.39900),
            (100.73300, 6.93300),
            (102.64500, 7.98700),
            (102.62600, 17.35900),
            (120.82600, 19.04300),
            (120.55000, 6.97400),
            (104.00800, 6.78700),
            (102.07600, 6.55400),
        ]

def get_remove_polygon_points(self):
    return [
        (4.90300, -58.05700),
        (-33.54000, -57.07600),
        (-9.06400, -16.81400),
        (-7.00100, -15.00000),
    ]

def subtract_custom_polygon( mmi, polygon_points):
    custom_polygon_component = gf.Component()
    custom_polygon_component.add_polygon(polygon_points, layer=(1, 0))
    mmi = gf.boolean(A=mmi, B=custom_polygon_component, operation="A-B", layer=(1, 0))

    mirrored_polygon_component = gf.Component()
    mirrored_polygon_component.add_polygon(
        [(x, -y) for x, y in polygon_points], layer=(1, 0)
    )
    mmi = gf.boolean(A=mmi, B=mirrored_polygon_component, operation="A-B", layer=(1, 0))
    return mmi

def create_resonator_or_smw(component_type: str, taper_length: float = 10, taper_width1: float = 0.08,
        layer: tuple = (1, 0), y_spacing: float = 0, clearance = 50, dil = 0):

    """
    Creates a GDS component with tapers and either fish or an arc based on the component type.

    Args:
        component_type (str): The type of component to create ('extractor', 'fish', or 'smw').
        taper_length (float): The length of the taper. Default is 10.
        taper_width1 (float): The width1 of the taper. Default is 0.08.
        layer (tuple): The GDS layer for the taper. Default is (1, 0).
        y_spacing (float): Vertical spacing adjustment for the tapers. Default is 0.
        arc_radius (float): Radius for the 180-degree arc when component_type is 'smw'. Default is 5.

    Returns:
        gf.Component: The created component with tapers and either fish or an arc.
    """
    component = gf.Component()

    if component_type == "extractor":
        support_y_shift=0.25
        tpr1 = component.add_ref(
            gf.components.taper(length=taper_length, width1=taper_width1, width2=0.46, layer=layer)
        ).dmovey(1.5 + y_spacing)

        tpr2 = component.add_ref(
            gf.components.taper(length=taper_length, width1=taper_width1, width2=0.46, layer=layer)
        ).dmovey(-1.5 + y_spacing)

        # Add fish components and connect them to the second short tapers
        if dil == 0:
            fish_refs = add_fish_components(component, 'Selected Resonators to FAB\QT10.gds', 20, 10, 5)
        else:
            fish_refs = add_fish_components(component, f'Selected Resonators to FAB\QT10_dil{dil}.gds', 20, 10, 5)

        fish_refs[0].connect(port="o1", other=tpr1.ports["o2"], allow_width_mismatch=True)
        fish_refs[1].connect(port="o1", other=tpr2.ports["o2"], allow_width_mismatch=True)
    elif component_type == "fish":
        support_y_shift = 0.3
        tpr1 = component.add_ref(
            gf.components.taper(length=taper_length, width1=taper_width1, width2=0.42, layer=layer)
        ).dmovey(1.5 + y_spacing)

        tpr2 = component.add_ref(
            gf.components.taper(length=taper_length, width1=taper_width1, width2=0.42, layer=layer)
        ).dmovey(-1.5 + y_spacing)

        # Add fish components and connect them to the second short tapers
        if dil == 0:
            fish_refs = add_fish_components(component, 'Selected Resonators to FAB\QT14.gds', 20, 10, 5)
        else:
            fish_refs = add_fish_components(component, f'Selected Resonators to FAB\QT14_dil{dil}.gds', 20, 10, 5)


        fish_refs[0].connect(port="o1", other=tpr1.ports["o2"], allow_width_mismatch=True)
        fish_refs[1].connect(port="o1", other=tpr2.ports["o2"], allow_width_mismatch=True)

    # support = component.add_ref(gf.components.straight(length=0.3, width=6)).dmovex(taper_length + 2 - 0.15).dmovey(0)
    component.add_ref(gf.components.taper(width1=0.25, width2=1, length=3)).drotate(90).dmovex(taper_length + 1.3).dmovey(
        -1.5+support_y_shift+y_spacing) #
    # Taper supports
    component.add_ref(gf.components.taper(width1=0.25, width2=1, length=3)).drotate(90).dmovex(taper_length + 1.3).mirror_y().dmovey(
        -1.5-support_y_shift+y_spacing)

    # Corrected layer handling for merging and subtracting
    layers_to_merge = [layer] if isinstance(layer, tuple) else [tuple(layer)]
    merged_component = component.extract(layers=layers_to_merge)

    # Create bounding box

    bbox = component.add_ref(
        gf.components.straight(length=taper_length + 5.3, width=5)
    ).dmovey(y_spacing - 1.5)

    bbox=gf.boolean(A=component.add_ref(gf.components.straight(length=clearance, width=10)).dmovey(y_spacing - 1.5).dmovex(-clearance),B=bbox,operation="or",layer=layer)

    # Subtract merged component from bbox
    c = gf.Component()
    bbox_subtracted = gf.boolean(A=bbox, B=merged_component, operation="A-B", layer=layer)

    if dil != 0:
        text1 = c.add_ref(gf.components.text(text=str(dil), size=5)).dmovex(20).dmovey(-4+y_spacing).flatten()
        # bbox_subtracted = gf.boolean(A=bbox_subtracted, B=circle_ref, operation="or", layer=layer)


    c.add_ref(bbox_subtracted)

    return c

def create_long_waveguide(start: tuple, end: tuple, length: float, width: float = 0.5,
                          layer: tuple = (1, 0), arc_radius: float = 22,
                          support_width: float = 0.6, support_length: float = 3, support_spacing: float = 22,
                          taper_length: float = 10, taper_width1: float = 0.08,clearance_width=50):
    """
    Creates a long waveguide with defined start and end points using straights and arcs,
    adding supports and subtracting the waveguide (with tapers & supports) from a wider path.

    Args:
        start (tuple): Starting coordinates of the waveguide (x, y).
        end (tuple): Ending coordinates of the waveguide (x, y).
        length (float): Total length of the waveguide.
        width (float): Width of the waveguide. Default is 0.5 µm.
        layer (tuple): The GDS layer for the waveguide. Default is (1, 0).
        arc_radius (float): The radius of arc segments used in the path. Default is 22 µm.
        support_width (float): Width of the support structures. Default is 0.6 µm.
        support_length (float): Length of the support structures. Default is 3 µm.
        support_spacing (float): Distance between support structures. Default is 20 µm.
        taper_length (float): Length of the taper. Default is 10 µm.
        taper_width1 (float): Starting width of the taper. Default is 0.08 µm.

    Returns:
        gf.Component: The generated waveguide component with supports and subtracted wider path.
    """
    component = gf.Component()

    # Calculate total Euclidean distance between start and end
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    distance = np.sqrt(dx ** 2 + dy ** 2)

    if distance > length:
        raise ValueError("The specified length is shorter than the straight-line distance between start and end points.")

    # Define waveguide path (excluding tapers for now)
    path = gf.Path()
    first_straight_length = length/2-distance / 2 - taper_length  # Adjusted first segment
    vertical_straight_length = dy -arc_radius*2 # Vertical section
    last_straight_length = length/2-distance / 2 - taper_length  # Adjusted final segment

    path.append(gf.path.straight(length=first_straight_length))
    path.append(gf.path.arc(radius=arc_radius, angle=90))
    path.append(gf.path.straight(length=vertical_straight_length))
    path.append(gf.path.arc(radius=arc_radius, angle=90))
    path.append(gf.path.straight(length=last_straight_length))

    # Create waveguide with tapers and supports
    waveguide_with_supports = gf.Component()

    # Add tapers to waveguide_with_supports
    taper = gf.components.taper(length=taper_length, width1=taper_width1, width2=width, layer=layer)
    taper_start = waveguide_with_supports.add_ref(taper)
    taper_start.move(start)

    waveguide = gf.path.extrude(path, layer=layer, width=width)
    waveguide_ref = waveguide_with_supports.add_ref(waveguide)
    waveguide_ref.move((start[0] + taper_length, start[1]))  # Move after taper

    taper_end = waveguide_with_supports.add_ref(taper)
    taper_end.move((start[0], start[1]+vertical_straight_length+arc_radius*2))

    # Function to add support structures inside waveguide_with_supports
    def add_supports_along_straight(x_start, y_start, length, is_vertical=False):
        num_supports = int(round((length-2) / support_spacing,0))  # Calculate number of supports
        # Create support component
        support = gf.components.taper(length=support_length, width1=width, width2=support_width, layer=layer)
        for i in range(1, num_supports + 2 ):
            if is_vertical:
                support_x = x_start  # X remains the same
                support_y = y_start + i * (support_spacing -2.6) # Increment Y for vertical section
                # support_y = round(y_start + i * support_spacing, -1)  # Snap Y to nearest 10 µm
            else:
                support_x = x_start + i * support_spacing  # Increment X for horizontal section
                support_y = y_start  # Y remains the same

            if is_vertical:
                # Flip Up-Down correctly
                waveguide_with_supports.add_ref(support).drotate(0).move((support_x, support_y + support_length))
                waveguide_with_supports.add_ref(support).drotate(180).move((support_x, support_y + support_length))
                # Flip Left-Right correctly
                waveguide_with_supports.add_ref(support).drotate(90).move((support_x, support_y))
                waveguide_with_supports.add_ref(support).drotate(270).move((support_x, support_y+support_length*2))
            else:
                # Correct horizontal placement
                waveguide_with_supports.add_ref(support).drotate(90).move((support_x, support_y + width))  # Up
                waveguide_with_supports.add_ref(support).drotate(270).move((support_x, support_y - width))  # Down
                waveguide_with_supports.add_ref(support).move((support_x - support_length, support_y))  # Left
                waveguide_with_supports.add_ref(support).drotate(180).move((support_x + support_length, support_y))  # Right

    # Function to add support structures along arc
    def add_supports_along_arc(center_x, center_y, radius, start_angle,end_angle , dx,dy):
        # Calculate arc length
        arc_length = np.abs(end_angle - start_angle) * np.pi * radius / 180
        
        # Create support components
        support2 = gf.components.taper(length=support_length, width1=width, width2=support_width, layer=layer)

        # Add support at the middle of the arc
        angle = np.radians(start_angle + 45)
        # Calculate position on arc with precise shifts
        # For 225° (45° from 180°), we need both x and y shifts
        support_x = center_x + radius * np.cos(angle)
        support_y = center_y + radius * np.sin(angle) 
        # Calculate rotation angle for the support
        # The support should be perpendicular to the tangent of the arc
        # For a circular arc, the tangent is perpendicular to the radius vector
        # We subtract 90 degrees to match the horizontal support pattern
        rotation_angle = np.degrees(angle)
        
        # Create bent support for this specific angle
        bent_support1 = create_bent_taper(taper_length=0, taper_width1=support_width, taper_width2=0.2, 
                                       bend_radius=radius*0.6, bend_angle=10, enable_sbend=False)
        
        # Add four supports around the point
        # Order matches the horizontal pattern: right taper expands then contracts
        # Adjust positions to account for support length and bend radius
        waveguide_with_supports.add_ref(bent_support1).drotate(rotation_angle + 180).move((support_x, support_y))  # Right
        waveguide_with_supports.add_ref(bent_support1).mirror_y().drotate(rotation_angle).move((support_x, support_y))  # Left
        waveguide_with_supports.add_ref(support2).drotate(rotation_angle + 90).move((support_x+dx, support_y-dy))  # Up
        waveguide_with_supports.add_ref(support2).drotate(rotation_angle + 270).move((support_x-dx, support_y+dy))  # Down

    # Add supports in first horizontal section
    add_supports_along_straight(start[0] -10, start[1], first_straight_length, is_vertical=False)

    # Add supports in first arc
    first_arc_center_x = start[0] + first_straight_length + taper_length + arc_radius+14.67
    first_arc_center_y = start[1] + arc_radius
    add_supports_along_arc(first_arc_center_x, first_arc_center_y, arc_radius, 180, 270,0.2,0.2)
    waveguide_with_supports.show()
    # Add supports in vertical section
    upward_section_start_x = start[0] + first_straight_length + arc_radius + taper_length
    upward_section_start_y = start[1] + arc_radius / 2 - 2
    add_supports_along_straight(upward_section_start_x, upward_section_start_y, vertical_straight_length, is_vertical=True)

    # Add supports in second arc
    second_arc_center_x = start[0] + first_straight_length + taper_length + arc_radius-35.03
    second_arc_center_y = start[1] + vertical_straight_length + arc_radius+49.7
    add_supports_along_arc(second_arc_center_x, second_arc_center_y, arc_radius, 270, 360,0.2,-0.2)
    # add_supports_along_arc(second_arc_center_x, second_arc_center_y, arc_radius, 315, 360)  # Add second support at 3/4 of arc
    # waveguide_with_supports.show()
    # Add supports in last horizontal section
    last_section_start_x = start[0]-10
    last_section_start_y = upward_section_start_y + vertical_straight_length + arc_radius * 3 / 2 + 2
    add_supports_along_straight(last_section_start_x, last_section_start_y, last_straight_length, is_vertical=False)

    # Generate the **wider path** that will be used for subtraction
    wider_width = support_length * 2
    # Extend the wider path by adding a 10 µm straight section at the beginning and end
    wider_path = gf.Path()
    wider_path.append(gf.path.straight(length=taper_length+clearance_width))
    wider_path.append(path)  # Original path
    wider_path.append(gf.path.straight(length=taper_length+clearance_width))

    wider_waveguide = gf.path.extrude(wider_path, layer=layer, width=wider_width)
    wider_waveguide_ref = component.add_ref(wider_waveguide)
    wider_waveguide_ref.move((start[0]-clearance_width, start[1]))

    clearance_rect = gf.Component().add_ref(gf.components.straight(length=clearance_width,width=20)).move((start[0]-clearance_width, start[1]))
    wider_waveguide_ref = gf.boolean(A=wider_waveguide_ref, B=clearance_rect, operation='or')
    clearance_rect = gf.Component().add_ref(gf.components.straight(length=clearance_width, width=20)).move((start[0] - clearance_width, end[1]))
    wider_waveguide_ref = gf.boolean(A=wider_waveguide_ref,B=clearance_rect,operation='or')

    # Subtract the entire waveguide (with tapers and supports) from the wider waveguide
    cutout_component = gf.boolean(A=wider_waveguide_ref, B=waveguide_with_supports, operation="A-B", layer=layer)
    component.add_ref(cutout_component)

    return cutout_component

def create_design(clearance_width=50,to_debug=False,layers=None):
    length_mmi = 79
    total_width_mmi = 10
    width_mmi = 6
    offset_y = 0
    y_spacing = 15
    directional_coupler_l = 0.42

    c = gf.Component()


    config = {"Long_WG":True, "Resonators":True, "N_Bulls_eye": 0, "add_logo": True, "add_rectangle": False, "add_scalebar": True, }

    if to_debug:
        config = {"Long_WG":False, "Resonators":False, "N_Bulls_eye": 0, "add_logo": False, "add_rectangle": False, "add_scalebar": False, }

    if to_debug:
        config = {"Long_WG":True, "Resonators":True, "N_Bulls_eye": 0, "add_logo": False, "add_rectangle": False, "add_scalebar": False, }

    params = {"is_resist_positive": True, "resonator_type": "fish", "length_mmi": length_mmi, "width_mmi": width_mmi, "total_width_mmi": 30,
        "taper_length_in": 20, "y_spacing": y_spacing / 2, }


    if config["Resonators"]:
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                  taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y-y_spacing/2,taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

        params["resonator_type"] = "extractor"
        offset_y+=y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                  taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

        bbox_component = create_bbox_component(length_mmi, total_width_mmi,clearance_width=clearance_width)
        params["taper_length_in"] = 10
        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y ,
                                          taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                                          taper_length=params["taper_length_in"], clearance=clearance_width,dil=5)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing / 2,
                                          taper_length=params["taper_length_in"], clearance=clearance_width,dil=5)).flatten()

        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                                          taper_length=params["taper_length_in"], clearance=clearance_width,dil=10)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing / 2,
                                          taper_length=params["taper_length_in"], clearance=clearance_width,dil=10)).flatten()

        params["resonator_type"] = "fish"
        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                                          taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                                          taper_length=params["taper_length_in"],clearance=clearance_width,dil=5)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,taper_length=params["taper_length_in"],clearance=clearance_width,dil=5)).flatten()

        offset_y += y_spacing
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y,
                                          taper_length=params["taper_length_in"], clearance=clearance_width, dil=10)).flatten()
        c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing / 2,
                                          taper_length=params["taper_length_in"], clearance=clearance_width, dil=10)).flatten()

    ###################   DIRECTIONAL COUPLER   ###################
    offset_y += 12
    params["resonator_type"] = "fish"
    c.add_ref(create_dc_design_vertical(resonator=params["resonator_type"],
                                    coupler_l=directional_coupler_l,pad_x_offset=210,pad_y_offset=23,clearance_width=clearance_width,layers=layers
                                        )).dmovey(offset_y).dmovex(21.6).flatten()
    offset_y += 18
    params["resonator_type"] = "extractor"
    c.add_ref(create_dc_design_vertical(resonator=params["resonator_type"],
                                    coupler_l=directional_coupler_l,clearance_width=clearance_width,layers=layers)).dmovey(offset_y).dmovex(21.6).flatten()
    # offset_y += 19
    # c.add_ref(create_dc_design_comb(resonator=params["resonator_type"],
    #                                     coupler_l=directional_coupler_l,clearance_width=clearance_width)).dmovey(offset_y).dmovex(21.6).flatten()
    # offset_y += 36
    # params["resonator_type"] = "fish"
    # c.add_ref(create_dc_design_comb(resonator=params["resonator_type"],
    #                                 coupler_l=directional_coupler_l,clearance_width=clearance_width)).dmovey(offset_y).dmovex(21.6).flatten()

    if config["N_Bulls_eye"] > 0:
        add_bulls_eye(c, config["N_Bulls_eye"], 150)

    if config["add_logo"]:
        c.add_ref(add_logos(c)).dmovex(60).dmovey(offset_y-100).flatten()

    if config["add_scalebar"]:
        add_scalebars(c, 17, -50)

    #####################    CIRCULAR TEST PATTERN    #############
    if not to_debug:
        circ=gf.boolean(
                A=gf.components.circle(radius=3, layer=(1, 0)),
                B=gf.components.circle(radius=1, layer=(1, 0)),
                operation="A-B",
                layer=(1, 0),
            )
        c.add_ref(unite_array(circ,3,3,(5,5),layer=(1,0))).dmovex(45).dmovey(offset_y-50).flatten()

        circ = gf.boolean(
            A=gf.components.circle(radius=6, layer=(1, 0)), #        B=gf.components.circle(radius=3, layer=(1, 0)),
            B=gf.components.straight(length=2,width=3,layer=(1,0)),
            operation="A-B",
            layer=(1, 0),
        )
        c.add_ref(unite_array(circ, 3, 3, (8, 8), layer=(1, 0))).dmovex(90).dmovey(offset_y - 55).flatten()

    ###########################    Long WG    ######################
    if config["Long_WG"]:
        arc_radius = 35
        wg_length = 640
        offset_step = 9
        length_step = 150

        for i in range(3):
            start_y = -35 + i * offset_step
            end_y = offset_y+32 - i*offset_step
            c.add_ref(create_long_waveguide(start=(0, start_y), end=(0, end_y), length=wg_length, width=0.25, arc_radius=arc_radius,clearance_width=clearance_width)).flatten()
            wg_length -= length_step

    ############################## TEXT !!!!!! #####################
    #
    # for i in range(1, 7):  # Loop from 1 to 18
    #     x_offset = 122  # Fixed x offset for all numbers
    #     y_offset = -5 + (i - 1) * y_spacing  # Incremental y offset based on the number
    #     c.add_ref(gf.components.text(text=str(i), size=5)).dmovex(x_offset).dmovey(y_offset).flatten()

    # c.add_ref(gf.components.straight(length=clearance_width,width=offset_y+20,layer=(1,0))).dmovex(-clearance_width).dmovey(offset_y/2-3).flatten()

    # c.show()
    return c

def merge_layer(component, layer=(1, 0)):
    """
    Merges overlapping or adjacent shapes in the specified layer.

    Args:
        component (gf.Component): The input photonic component.
        layer (tuple): The GDS layer to merge (default: (1, 0)).

    Returns:
        gf.Component: A new component with merged shapes.
    """
    merged_component = gf.Component()

    # Extract all polygons in the given layer
    layer_shapes = component.extract(layers=[layer])

    # Check if there are any polygons in the layer
    if not layer_shapes or not layer_shapes.get_polygons():
        print(f"⚠️ Warning: No shapes found in layer {layer}. Skipping merge operation.")
        return merged_component  # Return the original component

    # Merge adjacent or overlapping polygons
    merged_shapes = gf.boolean(A=layer_shapes, B=layer_shapes, operation="or", layer=layer)

    # Create a new component to store the merged result
    merged_component = gf.Component()
    merged_component.add_ref(merged_shapes).flatten()

    return merged_component

def create_fillet(radius = 0.15):
    c = gf.Component()

    # Create a square of size 0.15x0.15
    square = gf.components.rectangle(size=(radius, radius), layer=(1, 0))

    # Create a circle with radius 0.15 at the top-right corner of the square
    circle = gf.components.circle(radius=radius, layer=(1, 0))
    circle_ref = c.add_ref(circle)
    circle_ref.move((radius, radius))  # Move circle center to the top-right corner

    # Subtract the circle from the square
    result = gf.boolean(A=square, B=circle_ref, operation="A-B", layer=(1, 0))

    return result

def run_coupon_mode(base_directory, today_date, clearance_width,to_debug,layers):
    # Coupon mode: create coupon design (without electrodes).
    design_component = create_design(clearance_width=clearance_width,to_debug=to_debug,layers=layers)
    c = merge_layer(design_component, layer=layers["fine_ebl_layer"])
    # coarse_component=merge_layer(design_component, layer=layers["coarse_ebl_layer"])
    # c.add_ref(coarse_component).flatten()
    if not to_debug:
        c.add_ref(gf.components.straight(length=85, width=222,layer=layers["coarse_ebl_layer"])).dmovex(-85).dmovey(222/2-45).dmovex(
            -clearance_width).flatten()
        c.add_ref(gf.components.straight(length=10, width=500,layer=layers["coarse_ebl_layer"])).dmovex(-95).dmovey(500/2-45-100).dmovex(
            -clearance_width).flatten()

         # Save GDS file
        gds_output_file = os.path.join(base_directory, f"Left MDM-{today_date}.gds")
        c.write_gds(gds_output_file)
        print(f"GDS saved to {gds_output_file}")

    # Create rotated versions and save them
    def save_rotated(original, angle, name):
        rotated = gf.Component(name=f"rotated_{name}")
        ref = rotated.add_ref(original)
        ref.rotate(angle)
        gds_file = os.path.join(base_directory, f"{name} MDM-{today_date}.gds")
        rotated.write_gds(gds_file)
        print(f"GDS saved to {gds_file}")
        rotated.show()

    if not to_debug:
        save_rotated(c, 90, "Bottom")
        save_rotated(c, 180, "Right")
        save_rotated(c, 270, "Top")

    c.show()

def run_labels_mode(base_directory, today_date,layers=None):
    # Die dose_labels mode: create and save the full die dose_labels.
    dose_labels = ["300", "280", "260"]
    coupon_width=350
    coupon_height = 290

    def create_labels_component(labels, chip_name, size, spacing, position, horizontal=False, add_or_sub=True, include_ti=True,layers=None):
        label_component = gf.Component()
        label_component.add_ref(gf.components.text(text=chip_name, size=80, layer=layers["chip_name_layer"])).move((2000, 1770)).flatten()

        if include_ti:
            label_component.add_ref(gf.components.text(text="Ti", size=80, layer=layers["chip_name_layer"])).move((2000, 1650)).flatten()

        label_component.add_ref(gf.components.straight(length=250, width=150, layer=layers["square_layer"])).move((2200, 2600)).flatten() #SQUARE

        for i, dose_label in enumerate(dose_labels):
            text = label_component.add_ref(gf.components.text(text=str(dose_label), size=size, layer=layers["dose_label_layer"])).dmovex(
                (coupon_width/2+100 if add_or_sub else -coupon_width/2-100)).dmovey(coupon_height/2+100 if add_or_sub else -coupon_height/2-20)
            if horizontal:
                device = label_component.add_ref(gf.components.straight(length=coupon_height, width=coupon_width, layer=layers["fine_ebl_layer"]))
                text.move((position[0] + i * spacing, position[1])).flatten()
                device.move((position[0] + i * spacing - 80, position[1] + (300 if add_or_sub else -210))).flatten()

                electrode_component = add_electrodes_to_coupon(layers=layers)
                electrodes_ref = label_component.add_ref(electrode_component).drotate(270 if add_or_sub else 90)
                # Place electrodes with an offset: 60 to the right and 40 down from device position.
                electrodes_ref.move((position[0] + i * spacing +(11.6 if add_or_sub else 138.5), position[1] + (375.2 if add_or_sub else
                                                                                                             -283.8))).flatten()
            else:
                device = label_component.add_ref(gf.components.straight(length=coupon_width, width=coupon_height, layer=layers["fine_ebl_layer"]))
                text.move((position[0], position[1] - i * spacing)).flatten()
                device.move((position[0] + (215 if add_or_sub else -380), position[1] - i * spacing + 81.5)).flatten()

                electrode_component = add_electrodes_to_coupon(layers=layers)
                electrodes_ref = label_component.add_ref(electrode_component).drotate(180 if add_or_sub else 0)
                # Place electrodes with an offset: 60 to the right and 40 down from device position.
                electrodes_ref.move((position[0] +48 + (419 if add_or_sub else -330), position[1] - i * spacing + (175 if add_or_sub else
                                                                                                                      -12))).flatten()

        return label_component

    y_pos=2250
    spacing=770
    positions = {
        "Left": (925, y_pos, False, False),
        "Right": (1890, y_pos-95, False, True),
        # "Top": (800, 2150, True, True),
        # "Bottom": (810, 750, True, False),
    }

    def save_label_gds(chip_name, include_ti=True,layers=None):
        label_component = gf.Component(name=f"labels_{chip_name}")
        label_component.add_ref(gf.components.straight(length=3000, width=3000, layer=(4, 0))).dmovey(1500).flatten()
        label_component.add_ref(gf.components.straight(length=2400, width=2400, layer=(5, 0))).dmovey(1500).dmovex(300).flatten()

        for _, (x, y, is_horizontal, add_or_sub) in positions.items():
            label_component.add_ref(
                create_labels_component(
                    dose_labels, chip_name, size=70, spacing=spacing, position=(x, y), horizontal=is_horizontal,
                    add_or_sub=add_or_sub, include_ti=include_ti,layers=layers
                )
            ).flatten()

        labels_gds_file = os.path.join(base_directory, f"{chip_name}-{today_date}.gds")
        label_component.write_gds(labels_gds_file)
        print(f"GDS saved to {labels_gds_file}")
        label_component.show()

    save_label_gds("QT-MDM3.4",layers=layers)
    save_label_gds("QT-MDM3.5",layers=layers)
    save_label_gds("QT-MDM3.6", include_ti=False,layers=layers)

def add_electrodes_to_coupon(coupon = gf.Component(), layers = None):
    pad_x_spacing = 200
    pad_y_spacing = 100

    col1_1 = 112.9
    col1_2 = col1_1-19.4
    col1_3 = col1_2-19.4
    col1_4 = col1_3-19.4
    col1_5 = col1_4 - 19.4

    col2_1 = 103.9
    col2_2 = col2_1-19.4
    col2_3 = col2_2-19.4
    col2_4 = col2_3 - 19.4
    col2_5 = col2_4 - 19.4
    col2_6 = col2_5 - 19.4

    col3_1 = 114.3
    col3_2 = col3_1 - 19.4
    col3_3 = col3_2 - 19.4
    col3_4 = col3_3 - 19.4
    col3_5 = col3_4 - 19.4
    col3_6 = col3_5 - 19.4
    col3_7 = col3_6 - 19.4

    e_layer=layers["electrodes_layer"]
    pad_labels_layer=layers["pad_labels_layer"]
    label_size=35
    label_offset_x=155
    label_offset_y=15


    c = gf.Component()

    c.add_ref(gf.boolean(A=coupon, B=coupon, operation="or", layer=(1, 0)))

    pad_h = 120

    label_text = "B"
    xp=64
    yp=288
    c.add_ref(gf.components.straight(length=145, width=145, layer=e_layer)).dmovex(xp).dmovey(yp)
    points = [(50, 221), (50, 215), (68, 215)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    points = [(50, 208.9), (50, 215)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x-100, yp +label_offset_y+70),
                                 layer=pad_labels_layer))

    label_text = "D"
    xp+=pad_x_spacing
    c.add_ref(gf.components.straight(length=145, width=145, layer=e_layer)).dmovex(xp).dmovey(yp)
    points = [(50, 198), (50, 192), (274.8, 192), (274.8, 230)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    points = [(50, 185.9), (50, 192)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x-100, yp + label_offset_y+70),
                                 layer=pad_labels_layer))

    label_text = "A"
    xp+=pad_x_spacing
    yp+=pad_y_spacing
    points = [(47.5, 221), (58, 221), (58, yp+50), (xp, yp+50)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp+label_offset_x, yp+label_offset_y), layer=pad_labels_layer))

    label_text = "C"
    xp+=pad_x_spacing
    yp-=pad_y_spacing
    points = [(47.5, 208.9), (58, 208.9), (58, 203), (220, 203), (220, 420), (xp-pad_x_spacing-30, 420), (xp-pad_x_spacing-30, yp), (xp, yp)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    points = [(50, 208.9), (50, 215)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    points = [(48, 198), (58, 198), (58, 203)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    label_text = "E"
    xp+=pad_x_spacing
    yp-=pad_y_spacing
    points = [(48, 185.9), (390, 185.9), (xp-pad_x_spacing-30, 185.9), (xp-pad_x_spacing-30, yp), (xp, yp)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp+label_offset_x, yp+label_offset_y), layer=pad_labels_layer))

    label_text="F"
    xp+=pad_x_spacing
    yp-=pad_y_spacing
    points = [(45.2, 138.55), (45.2, 151), (100, 151), (100, 182), (xp-pad_x_spacing-30, 182), (xp-pad_x_spacing-30, yp), (xp, yp)]
    addition=c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    addition1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    addition1.connect(port='o1', other=addition.ports['o1'])
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp+label_offset_y),layer=pad_labels_layer))

    c.add_ref(gf.components.straight(length=label_size, width=26, layer=e_layer)).dmovex(48).dmovey(130)
    c.add_ref(gf.components.straight(length=label_size, width=26, layer=e_layer)).dmovex(48).dmovey(94)

    label_text = "G"
    xp += pad_x_spacing
    yp-=pad_y_spacing
    points = [(53, 144), (49, 144), (49, 148), (122, 148), (122, 178), (xp-pad_x_spacing*2-30*2, 178), (xp-pad_x_spacing*2-30*2, yp+pad_y_spacing-30),
              (xp-pad_x_spacing-30, yp+pad_y_spacing-30),(xp-pad_x_spacing-30, yp), (xp, yp)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp+label_offset_x, yp+label_offset_y), layer=pad_labels_layer))

    label_text = "H"
    xp = 300
    yp = 105
    points = [
        (70, 130),
        (140, 130),
        (140, col1_1),
        (190, col1_1),
        (190, col2_1),
        (230, col2_1),
        (230, col3_1),
        (260, col3_1),
        (260, yp),
        (xp, yp)
    ]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    points = [(50, 130), (45.2, 130), (45.2, 133.5)]
    p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    t1.connect(port='o1', other=p1.ports['o2'])

    # points = [(45.2, 130), (45.2, 126.45)]
    # p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    # t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    # t1.connect(port='o1', other=p1.ports['o2'])

    label_text = "I"
    xp += pad_x_spacing
    yp -= pad_y_spacing
    points = [
        (53, 115.9),
        (49, 115.9),
        (49, 112),
        (125, 112),
        (125, col1_2),
        (190, col1_2),
        (190, col2_2),
        (230, col2_2),
        (230, 80),
        (285, 80),
        (285, yp+30),
        (xp, yp+30)
    ]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2.5, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    points = [(53, 108), (49, 108), (49, 112)]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2.5, layer=e_layer))

    # points = [(50, 112), (45.2, 112), (45.2, 121.45)]
    # p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    # t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    # t1.connect(port='o1', other=p1.ports['o2'])

    # points = [(45.2, 112), (44.62, 112), (44.62, 102.54)]
    # p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    # t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    # t1.connect(port='o1', other=p1.ports['o2'])

    label_text = "J"
    xp += pad_x_spacing
    yp -= pad_y_spacing
    points = [
        (70, 83),
        (140, 83),
        (140, col1_3),  # col1_3 = 78.6
        (190, col1_3),
        (190, col2_3),  # col2_3 = 69.6
        (230, col2_3),
        (230, col3_4),  # col3_4 = 60.6
        (270, col3_4),
        (270, col2_5),  # col2_5 = 30.8
        (430, col2_5),
        (430, yp),
        (xp, yp)
    ]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2.5, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    # points = [(50, 94), (44.62, 94), (44.64, 97.54)]
    # p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    # t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    # t1.connect(port='o1', other=p1.ports['o2'])

    points = [(50, 94), (44.62, 94), (44.62, 90.45)]
    p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))
    t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    t1.connect(port='o1', other=p1.ports['o2'])

    label_text = "K"
    xp += pad_x_spacing
    yp -= pad_y_spacing
    points = [
        (53, 80),
        (49, 80),
        (49, 75),
        (120, 75),
        (120, col1_4),
        (195, col1_4),
        (195, col2_5),
        (230, col2_5),
        (230, col3_6),
        (410, col3_6),
        (410, yp),
        (xp, yp)
    ]
    c.add_ref(gf.path.extrude(gf.Path(points), width=2.5, layer=e_layer))
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    label_text = "L"
    xp += pad_x_spacing
    yp -= pad_y_spacing
    points = [
        (44.62, 85.45),
        (44.62, 70),
        (115, 70),
        (115, col1_5),
        (175, col1_5),
        (175, col2_6),
        (230, col2_6),
        (230, col3_7),
        (390, col3_7),
        (390, yp),
        (xp, yp)
    ]
    p1 = c.add_ref(gf.path.extrude(gf.Path(points), width=1, layer=e_layer))

    t1 = c.add_ref(gf.components.taper(length=1, width1=1, width2=0.02, layer=e_layer))
    t1.connect(port='o1', other=p1.ports['o1'])
    c.add_ref(gf.components.straight(length=150, width=pad_h, layer=e_layer)).move((xp, yp))
    c.add_ref(gf.components.text(text=label_text, size=label_size, position=(xp + label_offset_x, yp +label_offset_y), layer=pad_labels_layer))

    merged_layer = merge_layer(c, e_layer)
    merged_labels = merge_layer(c, pad_labels_layer)

    merged_layer.add_ref(coupon)
    merged_layer.add_ref(merged_labels)

    return merged_layer

def run_electrodes_mode(coupon_gds_path, base_directory, today_date,layers):
    # Load the coupon design from the existing GDS file.
    # Here we use gdsfactory's import function.
    coupon = gf.import_gds(coupon_gds_path)

    # Add the electrodes to the coupon design.
    coupon_with_electrodes = add_electrodes_to_coupon(coupon,layers)

    # Save the updated design to a new GDS file.
    electrodes_gds_file = os.path.join(base_directory, f"Left_Electrodes_{today_date}.gds")
    coupon_with_electrodes.write_gds(electrodes_gds_file)
    print(f"Updated coupon with electrodes saved to {electrodes_gds_file}")
    coupon_with_electrodes.show()

    # Create rotated versions and save them
    def save_rotated(original, angle, name):
        rotated = gf.Component(name=f"rotated_{name}")
        ref = rotated.add_ref(original)
        ref.rotate(angle)
        gds_file = os.path.join(base_directory, f"{name} MDM-{today_date}.gds")
        rotated.write_gds(gds_file)
        print(f"GDS saved to {gds_file}")
        rotated.show()

    save_rotated(coupon_with_electrodes, 90, "Bottom_Electrodes")
    save_rotated(coupon_with_electrodes, 180, "Right_Electrodes")
    save_rotated(coupon_with_electrodes, 270, "Top_Electrodes")

def main():
    layers = {
        "fine_ebl_layer": (1,0),
        "coarse_ebl_layer": (2,0),
        "electrodes_layer": (3,0),
        "pad_labels_layer": (4,0),
        "chip_name_layer": (5,0),
        "chip_frame_layer": (6,0),
        "square_layer": (7,0),
        "dose_label_layer": (8,0),
    }

    clearance_width = 5
    to_debug = True
    to_debug = False

    today_date = datetime.now().strftime("%d-%m-%y")
    base_directory = r"C:\PyLayout\Build"
    base_directory = r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM"

    # Mode selection: coupon (default), labels, or electrodes
    mode = "coupon"
    # mode = "labels"
    # mode = "electrodes"

    coupon_gds_path = r"C:\PyLayout\PyLayout\build\gds\MDM3C_run_coupon_mode.oas"

    if mode == "coupon":
        run_coupon_mode(base_directory, today_date, clearance_width,to_debug,layers)
    elif mode == "labels":
        run_labels_mode(base_directory, today_date,layers)
    elif mode == "electrodes":
        run_electrodes_mode(coupon_gds_path, base_directory, today_date,layers)
    else:
        print(f"Unknown mode '{mode}'. Please choose 'coupon', 'labels', or 'electrodes'.")

if __name__ == "__main__":
    main()
