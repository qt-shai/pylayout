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



def create_dc_design(resonator="fish",width_resonator=0.54):

    # Parameters for the S-bend
    width = 0.25  # Waveguide width in micrometers
    length = 5  # Length of the S-bend in micrometers
    dy = 1.1  # Vertical offset in micrometers
    layer = (1, 0)

    # Load fish component
    fish_component = gf.import_gds(Path('QT14.gds' if resonator == 'fish' else 'QT10.gds'))
    fish_component.add_port(name="o1", center=(0, 0), width=0.5, orientation=180, layer=layer)
    fish_component.add_port(name="o2", center=(fish_component.size_info.width, 0), width=0.5, orientation=0, layer=layer)

    x = gf.CrossSection(sections=[gf.Section(width=width, layer=layer, port_names=("in", "out"))])

    # Define tapers
    s1_l, s1_w = 3, 0.6
    s1 = gf.components.taper(length=s1_l, width1=width, width2=s1_w, layer=layer)

    s1_ref = gf.Component().add_ref(s1)
    s1_mirror_x = gf.Component().add_ref(s1).mirror_x()

    taper = gf.Component().add_ref(gf.components.taper(length=10, width1=0.08, width2=width, layer=(1, 0))).dmovex(-length - 10).dmovey(dy - width / 2)
    s1_ref.connect(port="o1", other=taper.ports["o2"])
    s1_mirror_x.connect(port="o2", other=s1_ref.ports["o2"], allow_width_mismatch=True)

    sbend = gf.components.bend_s(cross_section=x, size=(length, dy - width / 2))
    sbend_ref = gf.Component().add_ref(sbend)
    sbend_ref.connect(port="in", other=s1_mirror_x.ports["o1"], allow_width_mismatch=True)

    sbend_mirror_x = gf.Component().add_ref(sbend).mirror_x()
    sbend_mirror_x.connect(port="in", other=sbend_ref.ports["out"])

    s2_ref = gf.Component().add_ref(s1)

    s2_right = gf.components.taper(length=s1_l, width1=s1_w, width2=width_resonator, layer=layer)
    s2_right_ref = gf.Component().add_ref(s2_right)
    s2_ref.connect(port="o1", other=sbend_mirror_x.ports["out"], allow_width_mismatch=True)
    s2_right_ref.connect(port="o1", other=s2_ref.ports["o2"], allow_width_mismatch=True)

    fish = gf.Component().add_ref(fish_component)
    fish.connect(port="o1", other=s2_right_ref.ports["o2"], allow_width_mismatch=True)

    #############   Vertical supports    ################
    cnt1 = s1_ref.ports["o2"].center[0]
    cnt2 = s2_ref.ports["o2"].center[0]

    s3_l = .92
    s3 = gf.components.taper(length=s3_l, width1=0.6, width2=0.2, layer=layer)
    s3_ref = gf.Component().add_ref(s3).drotate(90)
    s3_ref.dmove((cnt1 / 1000, -s3_l / 2 + .3))

    s4 = gf.components.taper(length=s3_l, width1=0.2, width2=0.2, layer=layer)
    s4_ref = gf.Component().add_ref(s4).drotate(270)
    s4_ref.dmove((cnt1 / 1000, s3_l / 2 + 1.6))

    s5_ref = gf.Component().add_ref(s3).drotate(90)
    s5_ref.dmove((cnt2 / 1000, -s3_l / 2 + .3))
    s6_ref = gf.Component().add_ref(s4).drotate(270)
    s6_ref.dmove((cnt2 / 1000, s3_l / 2 + 1.6))



    ###########  Construct waveguides  #############
    top_waveguide = gf.boolean(A=taper, B=s1_ref, operation="or", layer=layer)
    for comp in [s1_mirror_x, sbend_ref, sbend_mirror_x, s2_ref, s2_right_ref, fish,s3_ref,s4_ref,s5_ref,s6_ref]:
        top_waveguide = gf.boolean(A=top_waveguide, B=comp, operation="or", layer=layer)

    bot_waveguide = gf.Component().add_ref(top_waveguide).mirror_y().dmovey(4.12)
    dc = gf.boolean(A=top_waveguide, B=bot_waveguide, operation="or", layer=layer)

    A = gf.Component().add_ref(gf.components.straight(length=length * 2 + 27.3, width=4.4, layer=layer)).dmovex(-15).dmovey(width+1.8)
    dc_positive = gf.boolean(A=A, B=dc, operation="A-B", layer=layer)

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
        short_taper_width2_right: float = 0.25, ):
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
            component.show()

    support = component.add_ref(gf.components.straight(length=0.3, width=6)).dmovex(taper_length + 2 - 0.15).dmovey(y_spacing)

    # Corrected layer handling for merging and subtracting
    layers_to_merge = [layer] if isinstance(layer, tuple) else [tuple(layer)]
    merged_component = component.extract(layers=layers_to_merge)

    # Create bounding box

    if component_type == "smw":
        bbox = component.add_ref(
            gf.components.straight(length=taper_length + 4, width=2)
        ).dmovey(y_spacing - 1.5)

        # Add second bounding box for arc/taper
        bbox_arc = component.add_ref(
            gf.components.bend_circular(radius=arc_radius, angle=180, layer=layer, width=2)
        ).dmovey(y_spacing + 1.5)

        bbox_arc.connect(port="o2", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)

        bbox=component.add_ref(gf.boolean(A=bbox, B=bbox_arc, operation="or", layer=layer))

        bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=taper_length + 4, width=2)).dmovey(y_spacing + arc_radius * 2 - 1.5),
                          B=bbox, operation="or", layer=layer)

        bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=20, width=10)).dmovey(y_spacing + arc_radius * 2 - 1.5).dmovex(-20),
                          B=bbox, operation="or", layer=layer)

    else:
        bbox = component.add_ref(
            gf.components.straight(length=taper_length + 9.3, width=2)
        ).dmovey(y_spacing - 1.5)

    bbox=gf.boolean(A=component.add_ref(gf.components.straight(length=20, width=10)).dmovey(y_spacing - 1.5).dmovex(-20),B=bbox,operation="or",layer=layer)

    # Subtract merged component from bbox
    c = gf.Component()
    bbox_subtracted = gf.boolean(A=bbox, B=merged_component, operation="A-B", layer=layer)

    if circle_ref:
        bbox_subtracted = gf.boolean(A=bbox_subtracted, B=circle_ref, operation="or", layer=layer)
    c.add_ref(bbox_subtracted)

    return c

def create_design(clearance_width=40):
    length_mmi = 79
    total_width_mmi = 10
    width_mmi = 6
    offset_y = 0
    y_spacing = 40/2


    c = gf.Component()

    config = {"N_Bulls_eye": 0, "add_logo": True, "add_rectangle": True, "add_scalebar": True, }


    params = {"is_resist_positive": True, "resonator_type": "fish", "length_mmi": length_mmi, "width_mmi": width_mmi, "total_width_mmi": 30,
        "taper_length_in": 20, "y_spacing": y_spacing / 2, }

    bbox_component = create_bbox_component(length_mmi=length_mmi, total_width_mmi=total_width_mmi,taper_length=params["taper_length_in"],
                                           clearance_width=clearance_width)

    # taper_length
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"]-10).flatten()
    width_resonator = 0.42 if params["resonator_type"]=="fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y-6.5, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y-10.5, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"])).flatten()

    params["resonator_type"] = "extractor"
    offset_y+=y_spacing
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"]-10).flatten()
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 6.5, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 10.5, short_taper_width2_right=width_resonator,
              taper_length=params["taper_length_in"])).flatten()

    bbox_component = create_bbox_component(length_mmi, total_width_mmi,clearance_width=clearance_width)
    params["taper_length_in"] = 10
    offset_y += y_spacing
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"]-10).flatten()
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 6.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 10.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()

    params["resonator_type"] = "fish"
    offset_y += y_spacing
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"]-10).flatten()
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 6.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 10.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()

    bbox_component = create_bbox_component(length_mmi, total_width_mmi-2,clearance_width=clearance_width)

    offset_y += y_spacing
    params["weird_support"]=True
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 6.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 10.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()

    offset_y += y_spacing
    params["resonator_type"] = "extractor"
    c.add_ref(add_mmi_patterns(c, bbox_component, params)).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 6.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()
    c.add_ref(create_resonator_or_smw(component_type=params["resonator_type"], y_spacing=offset_y - 10.5, short_taper_width2_right=width_resonator,
                                      taper_length=params["taper_length_in"])).flatten()


    ##############################             SMW             #########################################

    offset_y += 10
    arc_radius=11
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten()
    offset_y += 3
    arc_radius-=3
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten()
    offset_y += 3
    arc_radius -= 3
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten() # arc_radius=5
    offset_y += 20
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten() # arc_radius=5

    offset_y += 14
    arc_radius = 9
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten()  # arc_radius=6
    offset_y += 3
    arc_radius -= 3
    c.add_ref(create_resonator_or_smw("smw", y_spacing=offset_y, arc_radius=arc_radius)).flatten() # arc_radius=6

    #######################################        DIRECTIONAL COUPLER           ###################
    offset_y += 17
    params["resonator_type"] = "fish"
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"],width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()

    offset_y += 6
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()

    offset_y += 6
    params["resonator_type"] = "extractor"
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()

    offset_y += 6
    width_resonator = 0.42 if params["resonator_type"] == "fish" else 0.54
    c.add_ref(create_dc_design(resonator=params["resonator_type"], width_resonator=width_resonator)).dmovey(offset_y).dmovex(15).flatten()


    if config["N_Bulls_eye"] > 0:
        add_bulls_eye(c, config["N_Bulls_eye"], 150)

    if config["add_logo"]:
        c.add_ref(add_logos(c)).dmovex(20).dmovey(offset_y-40).dmovex(20).flatten()

    if config["add_scalebar"]:
        add_scalebars(c, 30, offset_y-65)

    ###############################    CIRCULAR TEST PATTERN    #############

    circ=gf.boolean(
            A=gf.components.circle(radius=3, layer=(1, 0)),
            B=gf.components.circle(radius=1, layer=(1, 0)),
            operation="A-B",
            layer=(1, 0),
        )
    c.add_ref(unite_array(circ,3,3,(5,5),layer=(1,0))).dmovex(50).dmovey(offset_y-10).flatten()

    circ = gf.boolean(
        A=gf.components.circle(radius=6, layer=(1, 0)), #        B=gf.components.circle(radius=3, layer=(1, 0)),
        B=gf.components.straight(length=2,width=3,layer=(1,0)),
        operation="A-B",
        layer=(1, 0),
    )
    c.add_ref(unite_array(circ, 3, 3, (8, 8), layer=(1, 0))).dmovex(80).dmovey(offset_y - 40).flatten()

    ############################## TEXT !!!!!! #####################

    for i in range(1, 7):  # Loop from 1 to 18
        x_offset = 122  # Fixed x offset for all numbers
        y_offset = -5 + (i - 1) * y_spacing  # Incremental y offset based on the number
        c.add_ref(gf.components.text(text=str(i), size=10)).dmovex(x_offset).dmovey(y_offset).flatten()

    c.add_ref(gf.components.straight(length=clearance_width,width=offset_y+20,layer=(1,0))).dmovex(-clearance_width).dmovey(offset_y/2-3).flatten()

    c.show()
    return c


def main(): 
    component = create_design(clearance_width=40)
    today_date = datetime.now().strftime("%d-%m-%y")
    base_directory = r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM"
    # base_directory = r"C:\PyLayout\PyLayout"
    output_file = os.path.join(base_directory, f"MDMA-{today_date}.gds")
    component.write_gds(output_file)
    print(f"Design saved to {output_file}")

if __name__ == "__main__":
    main()



