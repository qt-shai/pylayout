import numpy as np
import gdstk
import gdsfactory as gf
from functools import partial
from pathlib import Path
from datetime import datetime
import os

# # ------------------------------------------
# # KLayout Macro: Save Layout as High-Res PNG
# # ------------------------------------------
#
# app = RBA::Application.instance
# mw  = app.main_window
# cv  = mw.current_view
#
# if cv.nil?
#   mw.message("No layout is currently open.")
# else
#   # 1. Zoom to fit the entire layout in the view
#   cv.zoom_fit
#
#   # 2. Define the output file name (change the path if needed)
#   file_name = "C:\Users\shai\Documents\layout_export.png"
#
#   # 3. Define the desired resolution by specifying image dimensions in pixels
#   width_px  = 15000   # adjust as needed for higher/lower resolution
#   height_px = 15000   # adjust as needed for higher/lower resolution
#
#   # 4. Save the image using the 3-argument version of save_image
#   success = cv.save_image(file_name, width_px, height_px)
#
#   # 5. Provide feedback
#   if success
#     mw.message("✅ Layout saved to '#{file_name}' (#{width_px} x #{height_px} pixels).")
#   else
#     mw.message("❌ Failed to save layout image.")
#   end
# end


# # DRC Script to Merge All Shapes in Layer (1, 0)
#
# # Load the layer with indices (1, 0)
# l1 = input(1, 0)
#
# # Merge overlapping or adjacent shapes
# merged_l1 = l1.merged
#
# # Output the merged shapes back to the same layer
# merged_l1.output(1, 0)



# # DRC Script to Rotate All Shapes in Layer (1, 0) by 90 Degrees
#
# # Load the specific layer (1, 0)
# original_layer = input(1, 0)
#
# # Define a 90-degree rotation transformation
# rotation = RBA::ICplxTrans::new(1.0, 90, false, 0, 0)
#
# # Apply the transformation to all shapes in the layer
# rotated_layer = original_layer.transformed(rotation)
#
# # Output the transformed shapes to the original layer
# rotated_layer.output(1, 0)


# Python file to save current gds to cif text file
#
# import pya
#
#
# def save_current_layout_as_cif(filename=r"C:\Users\shai\Documents\my_layout.cif"):
#     main_window = pya.MainWindow.instance()
#     view = main_window.current_view()
#     if view is None:
#         raise RuntimeError("No layout view is open.")
#
#     cell_view = view.active_cellview()
#     layout = cell_view.layout()
#     if layout is None:
#         raise RuntimeError("No layout associated with the active cell view.")
#
#     opts = pya.SaveLayoutOptions()
#     # Use CIF as the export format (which is textual)
#     opts.format = "CIF"
#
#     layout.write(filename, opts)
#     print(f"Layout saved to CIF: {filename}")
#
#
# # Example usage:
# save_current_layout_as_cif()


# Python to save and copy to clipboard
#
# import pya
# import os
#
# def save_current_layout_as_cif_and_copy(filename=r"C:\Users\shai\Documents\my_layout.cif"):
#     """
#     Saves the currently open layout to a CIF (text) file and
#     copies the entire CIF content to the Windows clipboard using 'clip'.
#     """
#     main_window = pya.MainWindow.instance()
#     view = main_window.current_view()
#     if view is None:
#         raise RuntimeError("No layout view is open.")
#
#     cell_view = view.active_cellview()
#
#     layout = cell_view.layout()
#     if layout is None:
#         raise RuntimeError("No layout associated with the active cell view.")
#
#     # Prepare the SaveLayoutOptions for CIF
#     opts = pya.SaveLayoutOptions()
#     opts.format = "CIF"
#
#     # Write the layout to the specified file in CIF format
#     layout.write(filename, opts)
#     print(f"Layout successfully saved in CIF format to: {filename}")
#
#     # Read the CIF file back as text
#     with open(filename, "r", encoding="utf-8", errors="replace") as f:
#         cif_data = f.read()
#
#     # Copy the CIF text to the Windows clipboard using 'clip'
#     copy_text_to_clipboard_windows(cif_data)
#     print("All CIF text has been copied to the clipboard (Windows).")
#
#
# def copy_text_to_clipboard_windows(text):
#     """
#     Uses the Windows 'clip' command to put 'text' onto the system clipboard.
#     """
#     with os.popen('clip', 'w') as pipe:
#         pipe.write(text)
#
#
# # Example usage:
# save_current_layout_as_cif_and_copy()


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


def create_spring(c, cross_section, start_pos):
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

    # Horizontal large supports
    support1 = c.add_ref(gf.components.straight(length=8.5, width=dy+3, layer=layer))
    support1.dmove((cnt2[0] - 5, cnt2[1] - dy))
    refs.append(support1)

    taper_to_support1 = c.add_ref(gf.components.taper(length=4.5, width1=0.5, width2=dy+3, layer=layer))
    taper_to_support1.connect(port="o2", other=support1.ports["o1"],allow_width_mismatch=True)
    refs.append(taper_to_support1)

    support2_l=17
    support2 = c.add_ref(gf.components.straight(length=support2_l, width=dy+3, layer=layer))
    support2.dmove((cnt1[0] - support2_l + 4, cnt1[1] -dy))
    refs.append(support2)

    taper_to_support2 = c.add_ref(gf.components.taper(length=4.5, width1=dy+3, width2=0.5, layer=layer))
    taper_to_support2.connect(port="o1", other=support2.ports["o2"], allow_width_mismatch=True)
    refs.append(taper_to_support2)

    support3_l=32.5+dy*2.5
    support3 = c.add_ref(gf.components.straight(length=support3_l, width=10, layer=layer))
    support3.dmove((cnt1[0] - support3_l + 34, cnt1[1] + 6.5))
    refs.append(support3)

    circle_support = c.add_ref(gf.components.circle(radius=7, layer=layer))
    circle_support.dmove((cnt1[0] + dy*2+2.8, cnt1[1] + 3.5))
    refs.append(circle_support)

    return refs





def create_dc_design(resonator="fish", width_resonator=0.54,coupler_l=0.42,clearance_width=50):
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
    taper1_length, taper1_width2 = 3, 0.6
    taper1 = gf.components.taper(
        length=taper1_length,
        width1=wg_width,
        width2=taper1_width2,
        layer=layer_main
    )

    taper_small_in = gf.components.taper(
        length=10, width1=0.08, width2=wg_width, layer=layer_main
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

    opposing_comb_spine_down_taper = c.add_ref(gf.components.taper(length=.82, width1=dy+3,width2=0.5, layer=layer_main))
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
    spring_refs = create_spring(
        c=c,
        cross_section=spring_cs,
        start_pos=(comb_base.ports["o2"].x / 1000 -0.25, comb_base.ports["o2"].y / 1000 + tooth_length+0.3)
    )
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

    # --- Subtract combined waveguide from a large rectangle to get final geometry ---
    bounding_rect = gf.components.straight(
        length=sbend_length * 2 + N_teeth*x_spacing+25.24-0.209+clearance_width+coupler_l,
        width=dy * 2.5 + 16,
        layer=layer_main
    )
    bounding_rect_ref = gf.Component().add_ref(bounding_rect)
    bounding_rect_ref.dmovex(-21.6-clearance_width)
    bounding_ext = c.add_ref(gf.components.straight(length=clearance_width,width=50,layer=layer_main)).dmovex(-21.6-clearance_width)
    bounding_rect_ref = gf.boolean(A=bounding_rect_ref, B=bounding_ext, operation="or", layer=layer_main)

    dc_positive = gf.boolean(A=bounding_rect_ref, B=combined_dc, operation="A-B", layer=layer_main)


    return dc_positive






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
            # Skip the first instance since it’s already added as merged_device
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
    add_scalebar(component=c, size=10, position=(offset_x + 5, offset_y - 5), font_size=5)

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

def create_resonator_or_smw(component_type: str, taper_length: float = 10, taper_width1: float = 0.08, taper_width2: float = 0.25,
        layer: tuple = (1, 0), y_spacing: float = 0, arc_radius: float = 5, short_taper_length: float = 2, short_taper_width: float = 0.6,
        short_taper_width2_right: float = 0.25, clearance = 50):
    """
    Creates a GDS component with tapers and either fish or an arc based on the component type.

    Args:
        component_type (str): The type of component to create ('extractor', 'fish', or 'smw').
        taper_length (float): The length of the taper. Default is 10.
        taper_width1 (float): The width1 of the taper. Default is 0.08.
        taper_width2 (float): The width2 of the taper. Default is 0.25.
        layer (tuple): The GDS layer for the taper. Default is (1, 0).
        y_spacing (float): Vertical spacing adjustment for the tapers. Default is 0.
        arc_radius (float): Radius for the 180-degree arc when component_type is 'smw'. Default is 5.
        short_taper_length (float): Length of the short taper. Default is 2.
        short_taper_width (float): Width of the short taper. Default is 0.6.

    Returns:
        gf.Component: The created component with tapers and either fish or an arc.
    """
    component = gf.Component()
    circle_ref=None
    # Create initial tapers
    tpr1 = component.add_ref(
        gf.components.taper(length=taper_length, width1=taper_width1, width2=taper_width2, layer=layer)
    ).dmovey(1.5 + y_spacing if component_type != "smw" else y_spacing + arc_radius * 2 - 1.5)

    tpr2 = component.add_ref(
        gf.components.taper(length=taper_length, width1=taper_width1, width2=taper_width2, layer=layer)
    ).dmovey(-1.5 + y_spacing)

    # Create the first short taper (right)
    short_taper = gf.components.taper(
        length=short_taper_length, width1=short_taper_width2_right, width2=short_taper_width, layer=layer
    )
    short_taper_ref1 = component.add_ref(short_taper)
    short_taper_ref1.connect(port="o1", other=tpr1.ports["o2"], allow_width_mismatch=True)

    # Left
    right_short_taper = gf.components.taper(
        length=short_taper_length, width1=taper_width2, width2=short_taper_width, layer=layer
    )
    short_taper_ref2 = component.add_ref(right_short_taper)
    short_taper_ref2.connect(port="o1", other=tpr2.ports["o2"], allow_width_mismatch=True)


    # Create the second short taper (reuse short taper but flipped direction)
    short_taper_ref3 = component.add_ref(short_taper)
    short_taper_ref3.connect(port="o2", other=short_taper_ref1.ports["o2"], allow_width_mismatch=True)
    short_taper_ref4 = component.add_ref(short_taper)
    short_taper_ref4.connect(port="o2", other=short_taper_ref2.ports["o2"], allow_width_mismatch=True)

    if component_type == "extractor":
        # Add fish components and connect them to the second short tapers
        fish_refs = add_fish_components(component, 'QT10.gds', 20, 10, 5)
        fish_refs[0].connect(port="o1", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
        fish_refs[1].connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
    elif component_type == "fish":
        # Add fish components and connect them to the second short tapers
        fish_refs = add_fish_components(component, 'QT14.gds', 20, 10, 5)
        fish_refs[0].connect(port="o1", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
        fish_refs[1].connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
    elif component_type == "smw":
        # Add a 180-degree arc connecting the second short tapers
        arc = gf.components.bend_circular(radius=arc_radius, angle=180, layer=layer, width=taper_width2)
        arc_ref = component.add_ref(arc)
        arc_ref.connect(port="o2", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
        arc_ref.connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
        component.add_ref(gf.components.straight(length=0.3, width=6)).dmovex(taper_length + 2 - 0.15).dmovey(y_spacing + arc_radius * 2)
        if arc_radius > 7.9: # Add support structure in the middle if arc_radius > 7.9
            component.add_ref(gf.components.straight(length=6, width=0.3, layer=layer)).dmovex(taper_length + 2 - 0.15+ arc_radius).dmovey(y_spacing-1.5+arc_radius)

            # Replace the short tapers in the middle with bent tapers
            bent_taper1 = create_bent_taper(
                taper_length=short_taper_length,
                taper_width1=short_taper_width2_right*0.8,
                taper_width2=short_taper_width*0.8,
                bend_radius=arc_radius,
                bend_angle=10  # Adjust angle for smooth transition
            )

            component.add_ref(bent_taper1).drotate(80).dmovex(taper_length + 3.8165 + arc_radius).dmovey(y_spacing-1.5+ arc_radius-short_taper_length)
            component.add_ref(bent_taper1).mirror_x().drotate(100).dmovex(taper_length + 3.8165 + arc_radius).dmovey(y_spacing - 1.5+ arc_radius +short_taper_length)
        if arc_radius < 5.2:  # Add a circle in the arc center if radius is small
            circle_ref = gf.Component().add_ref(gf.components.circle(radius=arc_radius-.5, layer=layer)).dmovex(taper_length + 4 - 0.15).dmovey(
                y_spacing-1.5+ arc_radius)
            circle_ref=gf.boolean(A=circle_ref,B=gf.Component().add_ref(gf.components.straight(length=taper_length+3,
                                                                                               width=arc_radius*2-.57)).dmovey(
                y_spacing-1.5+arc_radius),operation='or')
            # component.show()

    support = component.add_ref(gf.components.straight(length=0.3, width=6)).dmovex(taper_length + 2 - 0.15).dmovey(0)
    component.add_ref(gf.components.taper(width1=0.3, width2=1, length=3)).drotate(90).dmovex(taper_length + short_taper_length).dmovey(-1.5+y_spacing) #
    # Taper supports
    component.add_ref(gf.components.taper(width1=0.3, width2=1, length=3)).drotate(90).dmovex(taper_length + short_taper_length).mirror_y().dmovey(
        -1.5+y_spacing)

    # Corrected layer handling for merging and subtracting
    layers_to_merge = [layer] if isinstance(layer, tuple) else [tuple(layer)]
    merged_component = component.extract(layers=layers_to_merge)

    # Create bounding box

    if component_type == "smw":
        bbox = component.add_ref(
            gf.components.straight(length=taper_length + 4, width=5)
        ).dmovey(y_spacing - 1.5)

        # Add second bounding box for arc/taper
        bbox_arc = component.add_ref(
            gf.components.bend_circular(radius=arc_radius, angle=180, layer=layer, width=5)
        ).dmovey(y_spacing + 1.5)

        bbox_arc.connect(port="o2", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)

        bbox=component.add_ref(gf.boolean(A=bbox, B=bbox_arc, operation="or", layer=layer))

        bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=taper_length + 4, width=2)).dmovey(y_spacing + arc_radius * 2 - 1.5),
                          B=bbox, operation="or", layer=layer)

        bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=20, width=10)).dmovey(y_spacing + arc_radius * 2 - 1.5).dmovex(-20),
                          B=bbox, operation="or", layer=layer)

    else:
        bbox = component.add_ref(
            gf.components.straight(length=taper_length + 9.3, width=5)
        ).dmovey(y_spacing - 1.5)

    bbox=gf.boolean(A=component.add_ref(gf.components.straight(length=clearance, width=10)).dmovey(y_spacing - 1.5).dmovex(-clearance),B=bbox,operation="or",layer=layer)

    # Subtract merged component from bbox
    c = gf.Component()
    bbox_subtracted = gf.boolean(A=bbox, B=merged_component, operation="A-B", layer=layer)

    if circle_ref:
        bbox_subtracted = gf.boolean(A=bbox_subtracted, B=circle_ref, operation="or", layer=layer)
    c.add_ref(bbox_subtracted)

    return c





def create_long_waveguide(start: tuple, end: tuple, length: float, width: float = 0.5,
                          layer: tuple = (1, 0), arc_radius: float = 22,
                          support_width: float = 0.6, support_length: float = 3, support_spacing: float = 20,
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
        num_supports = int(length // support_spacing)  # Calculate number of supports
        # Create support component
        support = gf.components.taper(length=support_length, width1=width, width2=support_width, layer=layer)
        for i in range(1, num_supports + 1 + (1 if is_vertical else 0)):
            if is_vertical:
                support_x = x_start  # X remains the same
                support_y = y_start + i * support_spacing  # Increment Y for vertical section
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

    # Add supports in first horizontal section
    add_supports_along_straight(start[0] + taper_length, start[1], first_straight_length, is_vertical=False)

    # Add supports in vertical section
    upward_section_start_x = start[0] + first_straight_length + arc_radius+taper_length
    upward_section_start_y = start[1] + arc_radius / 2
    add_supports_along_straight(upward_section_start_x, upward_section_start_y, vertical_straight_length, is_vertical=True)

    # Add supports in last horizontal section
    last_section_start_x = start[0]
    last_section_start_y = upward_section_start_y + vertical_straight_length + arc_radius * 3 / 2
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




def create_design(clearance_width=50):
    length_mmi = 79
    total_width_mmi = 10
    width_mmi = 6
    offset_y = 0
    y_spacing = 15
    directional_coupler_l = 0.42

    c = gf.Component()


    config = {"N_Bulls_eye": 0, "add_logo": True, "add_rectangle": True, "add_scalebar": True, }
    config = {"N_Bulls_eye": 0, "add_logo": True, "add_rectangle": False, "add_scalebar": True, }


    params = {"is_resist_positive": True, "resonator_type": "fish", "length_mmi": length_mmi, "width_mmi": width_mmi, "total_width_mmi": 30,
        "taper_length_in": 20, "y_spacing": y_spacing / 2, }

    bbox_component = create_bbox_component(length_mmi=length_mmi, total_width_mmi=total_width_mmi,taper_length=params["taper_length_in"],
                                           clearance_width=clearance_width)

    arc_radius = 35
    wg_length = 520
    offset_step = 9
    length_step = 70

    for i in range(3):
        start_y = offset_y - (35.5 - i * offset_step)
        end_y = offset_y + (161 - i * offset_step)
        c.add_ref(create_long_waveguide(start=(0, start_y), end=(0, end_y), length=wg_length, width=0.25, arc_radius=arc_radius,clearance_width=clearance_width)).flatten()
        wg_length -= length_step


    width_resonator = 0.42 if params["resonator_type"]=="fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y-y_spacing/2,
                                      short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

    params["resonator_type"] = "extractor"
    offset_y+=y_spacing
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,
                                      short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

    bbox_component = create_bbox_component(length_mmi, total_width_mmi,clearance_width=clearance_width)
    params["taper_length_in"] = 10
    offset_y += y_spacing
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y , short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,
                                      short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

    params["resonator_type"] = "fish"
    offset_y += y_spacing
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,
                                      short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

    offset_y += y_spacing
    params["weird_support"]=True
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,
                                      short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()

    offset_y += y_spacing
    params["resonator_type"] = "extractor"
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - y_spacing/2,
                                      short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"],clearance=clearance_width)).flatten()


    #######################################        DIRECTIONAL COUPLER           ###################
    offset_y += 12
    params["resonator_type"] = "fish"
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"],width_resonator=width_resonator,coupler_l=directional_coupler_l)).dmovey(offset_y).dmovex(21.6).flatten()

    # offset_y += 26
    # width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    # c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()
    #
    offset_y += 34
    params["resonator_type"] = "extractor"
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator,coupler_l=directional_coupler_l)).dmovey(offset_y).dmovex(21.6).flatten()
    #
    # offset_y += 11
    # width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    # c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()


    if config["N_Bulls_eye"] > 0:
        add_bulls_eye(c, config["N_Bulls_eye"], 150)

    if config["add_logo"]:
        c.add_ref(add_logos(c)).dmovex(60).dmovey(offset_y-100).flatten()

    if config["add_scalebar"]:
        add_scalebars(c, 25, offset_y-70)

    ###############################    CIRCULAR TEST PATTERN    #############

    circ=gf.boolean(
            A=gf.components.circle(radius=3, layer=(1, 0)),
            B=gf.components.circle(radius=1, layer=(1, 0)),
            operation="A-B",
            layer=(1, 0),
        )
    c.add_ref(unite_array(circ,3,3,(5,5),layer=(1,0))).dmovex(100).dmovey(offset_y-10).flatten()

    circ = gf.boolean(
        A=gf.components.circle(radius=6, layer=(1, 0)), #        B=gf.components.circle(radius=3, layer=(1, 0)),
        B=gf.components.straight(length=2,width=3,layer=(1,0)),
        operation="A-B",
        layer=(1, 0),
    )
    c.add_ref(unite_array(circ, 3, 3, (8, 8), layer=(1, 0))).dmovex(90).dmovey(offset_y - 50).flatten()

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
    # Extract all polygons in the given layer
    layer_shapes = component.extract(layers=[layer])

    # Check if there are any polygons in the layer
    if not layer_shapes or not layer_shapes.get_polygons():
        print(f"⚠️ Warning: No shapes found in layer {layer}. Skipping merge operation.")
        return component  # Return the original component

    # Merge adjacent or overlapping polygons
    merged_shapes = gf.boolean(A=layer_shapes, B=layer_shapes, operation="or", layer=layer)

    # Create a new component to store the merged result
    merged_component = gf.Component("Merged_Design")
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




def main():
    clearance_width = 50
    today_date = datetime.now().strftime("%d-%m-%y")
    base_directory = r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM"

    # c=gf.Component()
    # c.add_ref(create_dc_design(coupler_l=0.42))

    if True:
        c = merge_layer(create_design(clearance_width=clearance_width), layer=(1, 0))
        c.add_ref(gf.components.straight(length=10,width=50)).dmovey(-65.5).dmovex(-clearance_width).flatten()
        c.add_ref(gf.components.straight(length=10, width=50)).dmovey(191).dmovex(-clearance_width).flatten()

        # a=gf.Component().add_ref(gf.components.straight(length=50,width=120,layer=(2,0))).dmovex(40.7)
        # b=gf.Component().add_ref(gf.components.straight(length=50, width=30, layer=(2, 0))).dmovex(46).dmovey(29)
        # a=gf.boolean(A=a,B=b,operation="A-B",layer=(2,0))
        # b=gf.Component().add_ref(gf.components.straight(length=50, width=30, layer=(2, 0))).dmovex(46).dmovey(-29)
        # a = gf.boolean(A=a, B=b, operation="A-B", layer=(2, 0))
        # b=gf.Component().add_ref(gf.components.straight(length=50, width=20, layer=(2, 0))).dmovex(52).dmovey(30)
        # a = gf.boolean(A=a, B=b, operation="A-B", layer=(2, 0))
        # b=gf.Component().add_ref(gf.components.straight(length=50, width=20, layer=(2, 0))).dmovex(52).dmovey(-30)
        # a = gf.boolean(A=a, B=b, operation="A-B", layer=(2, 0))
        # c.add_ref(a)

        # Save GDS file
        gds_output_file = os.path.join(base_directory, f"Left MDM-{today_date}.gds")
        c.write_gds(gds_output_file)
        print(f"GDS saved to {gds_output_file}")
        c.show()

        # Create rotated versions and save them
        def save_rotated(original, angle, name):
            rotated = gf.Component()
            ref = rotated.add_ref(original)
            ref.rotate(angle)
            gds_file = os.path.join(base_directory, f"{name} MDM-{today_date}.gds")
            rotated.write_gds(gds_file)
            print(f"GDS saved to {gds_file}")
            rotated.show()

        save_rotated(c, 90, "Bottom")
        save_rotated(c, 180, "Right")
        save_rotated(c, 270, "Top")


    # Labels to create
    labels = ["300", "290", "280", "270", "260"]

    # Function to create text labels component
    def create_labels_component(labels, chip_name, size, spacing, position, horizontal=False, add_or_sub=True, include_ti=True):
        label_component = gf.Component()
        label_component.add_ref(gf.components.text(text=chip_name, size=130, layer=(1, 0))).move((1020, 1700)).flatten()

        if include_ti:
            label_component.add_ref(gf.components.text(text="Ti", size=130, layer=(1, 0))).move((1400, 1400)).flatten()

        label_component.add_ref(gf.components.straight(length=250, width=150, layer=(1, 0))).move((1370, 1100)).flatten()

        for i, label in enumerate(labels):
            text = label_component.add_ref(gf.components.text(text=str(label), size=size, layer=(1, 0)))

            if horizontal:
                device = label_component.add_ref(gf.components.straight(length=310, width=250, layer=(2, 0)))
                text.move((position[0] + i * spacing, position[1])).flatten()  # Move horizontally
                device.move((position[0] + i * spacing - 80, position[1] + (300 if add_or_sub else -210))).flatten()  # Move horizontally
            else:
                device = label_component.add_ref(gf.components.straight(length=250, width=310, layer=(2, 0)))
                text.move((position[0], position[1] - i * spacing)).flatten()  # Move vertically
                device.move((position[0] + (300 if add_or_sub else -330), position[1] - i * spacing + 50)).flatten()  # Move vertically
        return label_component

    # Define positions for Left, Right, Top, Bottom
    positions = {
        "Left": (750, 2050, False, False),  # Vertical
        "Right": (2000, 2050, False, True),  # Vertical
        "Top": (800, 2150, True, True),  # Horizontal
        "Bottom": (810, 750, True, False),  # Horizontal
    }

    # Function to create and save different versions
    def save_label_gds(chip_name, include_ti=True):
        label_component = gf.Component()

        # Background layers
        label_component.add_ref(gf.components.straight(length=3000, width=3000, layer=(3, 0))).dmovey(1500).flatten()
        label_component.add_ref(gf.components.straight(length=2200, width=2200, layer=(4, 0))).dmovey(1500).dmovex(400).flatten()

        # Add all label sets
        for _, (x, y, is_horizontal, add_or_sub) in positions.items():
            label_component.add_ref(
                create_labels_component(
                    labels, chip_name, size=70, spacing=310, position=(x, y), horizontal=is_horizontal,
                    add_or_sub=add_or_sub, include_ti=include_ti
                )
            ).flatten()

        # Save the GDS file
        labels_gds_file = os.path.join(base_directory, f"{chip_name}-{today_date}.gds")
        label_component.write_gds(labels_gds_file)
        print(f"GDS saved to {labels_gds_file}")
        label_component.show()

    # Save three different label GDS files
    save_label_gds("QT-MDM3.4")
    save_label_gds("QT-MDM3.5")
    save_label_gds("QT-MDM3.6", include_ti=False)  # Exclude "Ti" for 3.6



if __name__ == "__main__":
    main()



