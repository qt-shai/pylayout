import numpy as np
import gdstk
import gdsfactory as gf
from functools import partial
from pathlib import Path
from datetime import datetime
import os


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

class PhotonicDesign:
    def __init__(self, name="TOP"):
        self.component = gf.Component(name=name)

    def add_electrodes(self, c, params):
        """
        Adds electrodes to the design with elongation always included.

        Args:
            c: The component to which electrodes will be added.
            params (dict): A dictionary containing the following keys:
                - length_mmi (float): Length of the MMI section.
                - taper_length (float): Length of the taper section.
                - fish_center (float): Center alignment for the electrodes.
                - electrode_gap (float): Gap between the electrodes.
                - elongation_length (float): Length of the elongation. Default is 20.
                - downwards (float): Downward offset for electrodes. Default is 0.
                - layer (tuple): GDS layer for the electrodes. Default is (1, 0).

        Returns:
            gf.Component: The modified component with electrodes added.
        """
        # Extract parameters from params
        length_mmi = params.get('length_mmi')
        taper_length = params.get('taper_length')
        fish_center = params.get('fish_center')
        electrode_gap = params.get('electrode_gap')
        elongation_length = params.get('elongation_length', 20)
        downwards = params.get('downwards', 0)
        layer = params.get('layer', (1, 0))
        ele_tip_size = params.get('ele_tip_size', 0.2)



        elongation_width = 4
        ele_taper_length = 4

        # Add the middle straight and taper electrodes
        middle_straight = c.add_ref(gf.components.straight(length=3-ele_tip_size, width=.5, layer=layer)).dmovex(
            length_mmi + taper_length * 2 - fish_center+ele_tip_size/2
        )
        middle_taper = c.add_ref(gf.components.taper(length=.25, width1=2-electrode_gap, width2=.5, layer=layer)).dmovex(
            length_mmi + taper_length * 2 - fish_center+ele_tip_size/2
        )
        c.add_ref(gf.components.straight(length=ele_tip_size, width=2-electrode_gap, layer=layer)).dmovex(
            length_mmi + taper_length * 2 - fish_center-ele_tip_size/2
        )


        x = gf.CrossSection(sections=[gf.Section(width=1, layer=layer, port_names=("in", "out"))])
        x2 = gf.CrossSection(sections=[gf.Section(width=elongation_width, layer=layer, port_names=("in", "out"))])

        # Add elongation to the middle electrode
        middle_elongation_taper = c.add_ref(
            gf.components.taper(length=ele_taper_length, width1=elongation_width, width2=.5, layer=layer)
        )
        middle_elongation_taper.connect("o2", middle_straight.ports["o2"], allow_width_mismatch=True)

        middle_elongation_straight = c.add_ref(
            gf.components.straight(length=elongation_length+200, width=elongation_width, layer=layer)
        )
        middle_elongation_straight.connect("o1", middle_elongation_taper.ports["o1"], allow_width_mismatch=True)

        sbend0 = c.add_ref(
            gf.components.bend_s(size=(40, -87.5-downwards), cross_section=x2)
        )
        sbend0.connect("in", middle_elongation_straight.ports["o2"], allow_width_mismatch=True)

        pad_middle = c.add_ref(
            gf.components.straight(length=150, width=130, layer=layer)
        )
        pad_middle.connect("o1", sbend0.ports["out"], allow_width_mismatch=True)

        # Add upper and lower electrodes
        for direction, y_offset, angle, rot_ang in [("up", 3.42, 90,0), ("down", -3.42, -90, 0)]:
            straight_section = c.add_ref(gf.components.straight(length=2, width=1, layer=layer)).drotate(rot_ang).dmovex(
                length_mmi + taper_length * 2 - 0.7 - fish_center
            ).dmovey(y_offset)
            taper_section = c.add_ref(gf.components.taper(length=1.39, width1=ele_tip_size, width2=1.4, layer=layer)).drotate(angle).dmovex(
                length_mmi + taper_length * 2 - fish_center).dmovey(y_offset + (electrode_gap / 2 - 2.39 if direction == "up" else -electrode_gap /
                                                                                                                                   2 + 2.39))

            sbend1 = c.add_ref(
                gf.components.bend_s(size=(8, 4 if direction == "up" else -4), cross_section=x)
            )
            sbend1.connect("in", straight_section.ports["o2"])

            elongation_taper = c.add_ref(
                gf.components.taper(length=ele_taper_length, width1=elongation_width, width2=1, layer=layer)
            )
            elongation_taper.connect("o2", sbend1.ports["out"], allow_width_mismatch=True)

            elongation_straight = c.add_ref(
                gf.components.straight(length=elongation_length+390 if direction == "up" else elongation_length , width=elongation_width,
                                       layer=layer)
            )
            elongation_straight.connect("o1", elongation_taper.ports["o1"], allow_width_mismatch=True)

            sbend2 = c.add_ref(
                gf.components.bend_s(size=(40, -95-downwards if direction == "up" else -80-downwards), cross_section=x2)
            )
            sbend2.connect("in", elongation_straight.ports["o2"], allow_width_mismatch=True)


            pad1 = c.add_ref(
                gf.components.straight(length=150, width=130, layer=layer)
            )
            pad1.connect("o1", sbend2.ports["out"], allow_width_mismatch=True)

        return c

    def add_fish_components(self, c, gds_file, length_mmi, taper_length, taper_separation):
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

    def create_mmi(self, params=None):
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
            "fish_center": 1.6,
            "extractor_center": 2.2,
            "electrode_gap": 1.5,
            "enable_sbend": True,
            "elongation_length": 20,
            "downwards": 0,
            "ele_tip_size": 0.4,
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

        params_for_ele = {
            "length_mmi": params["length_mmi"] + 4.2,
            "taper_length": params["taper_length_out"],
            "fish_center": params["fish_center"],
            "electrode_gap": params["electrode_gap"],
            "elongation_length": params["elongation_length"],
            "downwards": params["downwards"],
            "layer": params.get("layer", (1, 0)),  # Use a default layer if not in params
            "ele_tip_size": params["ele_tip_size"],
        }

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

            fish_refs = self.add_fish_components(
                c, 'QT14.gds', params["length_mmi"], params["taper_length_out"], params["taper_separation"]
            )

            fish_refs[0].connect(
                port="o1", other=taper_resonator_ref.ports["o2"], allow_width_mismatch=True
            )
            fish_refs[1].connect(
                port="o1", other=taper_resonator_mirror_ref.ports["o2"], allow_width_mismatch=True
            )

            self.add_electrodes(c, params_for_ele)
            params_for_ele["layer"]=(2,0)
            ele = self.add_electrodes(c_ele,params_for_ele)

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

            fish_refs = self.add_fish_components(
                c, 'QT10.gds', params["length_mmi"], params["taper_length_out"], params["taper_separation"]
            )

            fish_refs[0].connect(
                port="o1", other=taper_resonator_ref.ports["o2"], allow_width_mismatch=True
            )
            fish_refs[1].connect(
                port="o1", other=taper_resonator_mirror_ref.ports["o2"], allow_width_mismatch=True
            )

            params_for_ele["Layer"] = (1, 0)
            params_for_ele["fish_center"] = params["extractor_center"]
            self.add_electrodes(
                c,params_for_ele)
            params_for_ele["layer"] = (2, 0)
            ele = self.add_electrodes(
                c_ele,params_for_ele)

        # MMI supports (shortened for brevity)
        def add_corner_taper(c, position, rotate_angle, mirror=False):
            taper = gf.components.taper(
                length=params["mmi_support_length"],
                width1=0.1 * params["mmi_support_length"] + params["corner_support_width"],
                width2=params["corner_support_width"],
                layer=(1, 0),
            )
            taper_ref = c.add_ref(taper)
            taper_ref.drotate(rotate_angle)
            if mirror:
                taper_ref.mirror_y()
            taper_ref.dmove(position)
            return taper_ref

            # Define positions and orientations for corner tapers

        corner_positions = [
            # Bottom left
            (10 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3),
            # Top left
            (10 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3),
            # Bottom right
            (params["length_mmi"] + 9 + params["corner_support_width"] / 2, -params["width_mmi"] - params["mmi_support_length"] + 3),
            # Top right
            (params["length_mmi"] + 9 + params["corner_support_width"] / 2, params["width_mmi"] + params["mmi_support_length"] - 3),
        ]

        # Add corner tapers with correct rotation
        for i, pos in enumerate(corner_positions):
            rotate_angle = 90  # Rotate tapers by 90 degrees
            mirror = (i % 2 == 1)  # Mirror for the top positions
            add_corner_taper(c, pos, rotate_angle, mirror=mirror)

        # Helper function to add and position tapers
        def add_taper(c, position, width1, width2, rotate_angle, mirror=False):
            taper = gf.components.taper(
                length=params["mmi_support_length"],
                width1=width1,
                width2=width2,
                layer=(1, 0),
            )
            taper_ref = c.add_ref(taper)
            taper_ref.drotate(rotate_angle)
            if mirror:
                taper_ref.mirror_y()
            taper_ref.dmove(position)
            return taper_ref

        # Center taper positions and dimensions
        center_positions = [
            (10 + params["length_mmi"] / 3, -params["width_mmi"] - params["mmi_support_length"] + 3),
            (10 + params["length_mmi"] / 3, params["width_mmi"] + params["mmi_support_length"] - 3),
            (10 + params["length_mmi"] * 2 / 3, -params["width_mmi"] - params["mmi_support_length"] + 3),
            (10 + params["length_mmi"] * 2 / 3, params["width_mmi"] + params["mmi_support_length"] - 3),
        ]

        # Add center tapers
        for i, pos in enumerate(center_positions):
            rotate_angle = 90  # Rotate tapers by 90 degrees
            mirror = (i % 2 == 1)  # Mirror for the top positions
            width1 = 0.1 * params["mmi_support_length"] + 0.6
            width2 = 0.2
            add_taper(c, pos, width1, width2, rotate_angle, mirror=mirror)

        # Combine main MMI and coupler
        Device = gf.boolean(A=c, B=coupler, operation="or", layer=(1, 0))

        if params["name"]:  # Set the name if provided
            Device.name = params["name"]

        # return Device, ele

        return Device, ele

    # @gf.cell
    def logo(self, name=None):
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

    def unite_array(self, component, rows=1, cols=1, spacing=(10, 10), name=None, layer=(1,0)):
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

    def add_scalebar(self, component, size=100, position=(0, 0), font_size=15):
        """
        Adds a scalebar to the component with dynamically calculated text offset.

        Parameters:
            component: The component to which the scalebar will be added.
            size: The size of the scalebar in micrometers.
            position: The starting position of the scalebar (x, y).
            font_size: Font size of the scalebar.
        """
        # Add the scalebar line
        scalebar = gf.components.rectangle(size=(size, size / 10),  # 100 µm long and 5 µm thick
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

    def create_bbox_component(self, length_mmi, total_width_mmi,x_offset=-60):
        bbox_component = gf.Component()
        bbox_component.add_ref(
            gf.components.straight(length=length_mmi + 38.3, width=total_width_mmi, layer=(1, 0))
        ).dmovex(-13)

        bbox_component.add_ref(gf.components.straight(length=50, width=70, layer=(1, 0))).dmovex(x_offset)

        return bbox_component

    def add_mmi_patterns(self, c, bbox_component, params=None):
        default_params = {
            "is_resist_positive": True,
            "resonator_type": "fish",
            "length_mmi": 79,
            "width_mmi": 6,
            "total_width_mmi": 30,
            "taper_length_in": 10,
            "y_spacing": 30,
            "elongation_length": 20,
            "downwards": 0,
            "ele_tip_size": 0.4,
        }

        # Update default parameters with input parameters
        if params is not None:
            default_params.update(params)
        params = default_params

        mmi, ele = self.create_mmi(params=params)

        if params["is_resist_positive"]:
            mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

        # c.add_ref(self.unite_array(mmi, cols=1, rows=2, spacing=(0, 60))).dmovey(offset_y).dmovex(params["taper_length_in"]-10)

        return self.unite_array(mmi, cols=1, rows=2, spacing=(0, params["y_spacing"])), ele

    def add_mmi_patterns_with_sbend(self, c, bbox_component, is_resist_positive, resonator_type, offset_y, offset_x):
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
            "electrode_gap": 1,
        }

        # Create MMI
        mmi = self.create_mmi(params=params)

        # Apply boolean operation if resist is positive
        if is_resist_positive:
            mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

        # Subtract custom polygons
        # custom_polygon_points = self.get_custom_polygon_points(resonator_type)
        # mmi = self.subtract_custom_polygon(mmi, custom_polygon_points)

        # Add MMI pattern to the component
        c.add_ref(
            self.unite_array(mmi, cols=1, rows=2, spacing=(0, 60), name=f"mmi_{resonator_type}_s_bend")
        ).dmovey(offset_y).dmovex(offset_x)

    def add_mmi_patterns_fiber(self, c, bbox_component, is_resist_positive, resonator_type):
        params = {
            "resonator_type": resonator_type,
            "length_mmi": 79,
            "width_mmi": 6,
            "total_width_mmi": 30,
            "bend_angle": 30,
            "taper_length_in": 25,
            "enable_sbend": False,
        }
        mmi = self.create_mmi(params=params)

        if is_resist_positive:
            mmi = gf.boolean(A=bbox_component, B=mmi, operation="A-B", layer=(1, 0))

        # custom_polygon_points = self.get_custom_polygon_points(resonator_type)
        # mmi = self.subtract_custom_polygon(mmi, custom_polygon_points)

        remove_polygon_points = self.get_remove_polygon_points()
        mmi = self.subtract_custom_polygon(mmi, remove_polygon_points)

        return self.unite_array(mmi, cols=1, rows=4, spacing=(0, 100), name=f"mmi_{resonator_type}_fiber")

    def add_bulls_eye(self, c, n_bulls_eye, offset_x):
        a = gf.components.circle(radius=5.8, layer=(1, 0))
        s1 = gf.Component().add_ref(gf.components.straight(length=0.2, width=20, layer=(1, 0))).dmovex(-0.1)
        a = gf.boolean(A=a, B=s1, operation="A-B", layer=(1, 0))

        gds_file = Path('Bulls_Eye_Layout_v1.1.gds')
        b = gf.import_gds(gds_file)
        b.name = "GDS_Import"

        c.add_ref(self.unite_array(b, cols=n_bulls_eye, rows=1, spacing=(12.5, 12.5), name="Bulls-eye")).dmovey(-20).dmovex(offset_x + 32)

    def add_logos(self, c):
        return self.unite_array(self.logo(name="Logo"), cols=2, rows=1, spacing=(30, 250), name="logos")

    def add_scalebars(self, c, offset_x, offset_y):
        self.add_scalebar(component=c, size=100, position=(offset_x, offset_y), font_size=10)
        self.add_scalebar(component=c, size=10, position=(offset_x + 5, offset_y - 5), font_size=5)

    def get_custom_polygon_points(self, resonator_type):
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

    def subtract_custom_polygon(self, mmi, polygon_points):
        custom_polygon_component = gf.Component()
        custom_polygon_component.add_polygon(polygon_points, layer=(1, 0))
        mmi = gf.boolean(A=mmi, B=custom_polygon_component, operation="A-B", layer=(1, 0))

        mirrored_polygon_component = gf.Component()
        mirrored_polygon_component.add_polygon(
            [(x, -y) for x, y in polygon_points], layer=(1, 0)
        )
        mmi = gf.boolean(A=mmi, B=mirrored_polygon_component, operation="A-B", layer=(1, 0))
        return mmi

    def create_design(self, debug=True):
        additional_patterns_x_offset = 10
        additional_patterns_y_offset = -40

        length_mmi = 79
        total_width_mmi = 10
        width_mmi = 6
        offset_y = 0
        y_spacing = 40
        y_spacing1=10

        is_resist_positive = not debug
        c = self.component

        config = {
            "N_Bulls_eye": 0,
            "add_logo": True,
            "add_rectangle": True,
            "add_scalebar": True,
        }

        bbox_component = self.create_bbox_component(length_mmi, total_width_mmi)

        params = {
            "is_resist_positive": True,
            "resonator_type": "fish",
            "length_mmi": length_mmi,
            "width_mmi": width_mmi,
            "total_width_mmi": 30,
            "taper_length_in": 20,
            "y_spacing": y_spacing/2,
            "elongation_length": 20,
            "downwards": 0,
            "ele_tip_size": 0.4,
            "electrode_gap": 1,
        }

        mmi , ele = self.add_mmi_patterns(c, bbox_component, params)
        c.add_ref(mmi).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
        c.add_ref(ele).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()

        params["resonator_type"] = "extractor"
        # params["elongation_length"] += 600
        params["elongation_length"] += 390.6
        params["downwards"] += 40.16
        params["electrode_gap"] = 1.2
        offset_y+=y_spacing

        mmi, ele = self.add_mmi_patterns(c, bbox_component, params)
        c.add_ref(mmi).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
        c.add_ref(ele).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()

        bbox_component = self.create_bbox_component(length_mmi, total_width_mmi,x_offset=-50)
        params["taper_length_in"] = 10
        # params["elongation_length"] += 600
        params["elongation_length"] += 400
        params["downwards"] += 40.16
        params["electrode_gap"] = 1.5
        offset_y += y_spacing

        mmi, ele = self.add_mmi_patterns(c, bbox_component, params)
        c.add_ref(mmi).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
        c.add_ref(ele).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()

        params["resonator_type"] = "fish"
        # params["elongation_length"] += 600
        params["elongation_length"] += 389.4
        params["downwards"] += 40.16
        params["electrode_gap"] = 1
        offset_y += y_spacing

        mmi, ele = self.add_mmi_patterns(c, bbox_component, params)
        c.add_ref(mmi).dmovey(offset_y).dmovex(params["taper_length_in"]-10).flatten()
        c.add_ref(ele).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()

        bbox_component = self.create_bbox_component(length_mmi, total_width_mmi-3,x_offset=-50)

        # params["elongation_length"] += 600
        params["elongation_length"] += 390
        params["downwards"] += 40.16
        offset_y += y_spacing
        mmi, ele = self.add_mmi_patterns(c, bbox_component, params)
        c.add_ref(mmi).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()
        c.add_ref(ele).dmovey(offset_y).dmovex(params["taper_length_in"] - 10).flatten()

        offset_y += y_spacing-10
        c.add_ref(self.create_resonator_or_smw("extractor", y_spacing=offset_y, short_taper_width2_right=0.54)).flatten()
        c.add_ref(self.create_resonator_or_smw("extractor", y_spacing=offset_y + 4, short_taper_width2_right=0.54)).flatten()
        c.add_ref(self.create_resonator_or_smw("fish", y_spacing=offset_y + 8, short_taper_width2_right=0.42)).flatten()
        c.add_ref(self.create_resonator_or_smw("fish", y_spacing=offset_y + 12, short_taper_width2_right=0.42)).flatten()
        c.add_ref(self.create_resonator_or_smw("smw", y_spacing=offset_y + 19)).flatten()
        c.add_ref(self.create_resonator_or_smw("smw", y_spacing=offset_y + 16, arc_radius=8)).flatten()





        if config["N_Bulls_eye"] > 0:
            self.add_bulls_eye(c, config["N_Bulls_eye"], additional_patterns_x_offset)

        if config["add_logo"]:
            c.add_ref(self.add_logos(c)).dmovex(additional_patterns_x_offset).dmovey(-20).dmovex(40).flatten()

        if config["add_scalebar"]:
            self.add_scalebars(c, additional_patterns_x_offset, additional_patterns_y_offset)

        circ=gf.boolean(
                A=gf.components.circle(radius=3, layer=(1, 0)),
                B=gf.components.circle(radius=1, layer=(1, 0)),
                operation="A-B",
                layer=(1, 0),
            )
        c.add_ref(self.unite_array(circ,3,3,(5,5),layer=(1,0))).dmovex(40).dmovey(-100).flatten()


        for i in range(1, 6):  # Loop from 1 to 18
            x_offset = -70  # Fixed x offset for all numbers
            y_offset = -8 + (i - 1) * y_spacing  # Incremental y offset based on the number
            c.add_ref(gf.components.text(text=str(i), size=15)).dmovex(x_offset).dmovey(y_offset).flatten()


        c.show()
        return c


    def create_resonator_or_smw(
            self,
            component_type: str,
            taper_length: float = 10,
            taper_width1: float = 0.08,
            taper_width2: float = 0.25,
            layer: tuple = (1, 0),
            y_spacing: float = 0,
            arc_radius: float = 5,
            short_taper_length: float = 2,
            short_taper_width: float = 0.6,
            short_taper_width2_right: float = 0.25,
    ):
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
            fish_refs = self.add_fish_components(component, 'QT10.gds', 20, 10, 5)
            fish_refs[0].connect(port="o1", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
            fish_refs[1].connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
        elif component_type == "fish":
            # Add fish components and connect them to the second short tapers
            fish_refs = self.add_fish_components(component, 'QT14.gds', 20, 10, 5)
            fish_refs[0].connect(port="o1", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
            fish_refs[1].connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
        elif component_type == "smw":
            # Add a 180-degree arc connecting the second short tapers
            arc = gf.components.bend_circular(radius=arc_radius, angle=180, layer=layer, width=taper_width2)
            arc_ref = component.add_ref(arc)
            arc_ref.connect(port="o2", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)
            arc_ref.connect(port="o1", other=short_taper_ref4.ports["o1"], allow_width_mismatch=True)
            component.add_ref(gf.components.straight(length=0.3, width=6)).dmovex(taper_length + 2 - 0.15).dmovey(y_spacing + arc_radius * 2)

        support = component.add_ref(
            gf.components.straight(length=0.3, width=6)
        ).dmovex(taper_length + 2 - 0.15).dmovey(y_spacing)

        # Corrected layer handling for merging and subtracting
        layers_to_merge = [layer] if isinstance(layer, tuple) else [tuple(layer)]
        merged_component = component.extract(layers=layers_to_merge)

        # Create bounding box


        if component_type == "smw":
            bbox = component.add_ref(
                gf.components.straight(length=taper_length + 4, width=1.5)
            ).dmovey(y_spacing - 1.5)

            # Add second bounding box for arc/taper
            bbox_arc = component.add_ref(
                gf.components.bend_circular(radius=arc_radius, angle=180, layer=layer, width=1.5)
            ).dmovey(y_spacing + 1.5)

            bbox_arc.connect(port="o2", other=short_taper_ref3.ports["o1"], allow_width_mismatch=True)

            bbox=component.add_ref(gf.boolean(A=bbox, B=bbox_arc, operation="or", layer=layer))

            bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=taper_length + 4, width=1.5)).dmovey(y_spacing + arc_radius * 2 -
                                                                                                                     1.5),
                              B=bbox, operation="or", layer=layer)

            bbox = gf.boolean(A=component.add_ref(gf.components.straight(length=20, width=10)).dmovey(y_spacing + arc_radius * 2 - 1.5).dmovex(-20), B=bbox,
                              operation="or",
                              layer=layer)

        else:
            bbox = component.add_ref(
                gf.components.straight(length=taper_length + 9.3, width=1.5)
            ).dmovey(y_spacing - 1.5)

        bbox=gf.boolean(A=component.add_ref(gf.components.straight(length=20, width=10)).dmovey(y_spacing - 1.5).dmovex(-20),B=bbox,operation="or",
                        layer=layer)

        # Subtract merged component from bbox
        c = gf.Component()
        bbox_subtracted = gf.boolean(A=bbox, B=merged_component, operation="A-B", layer=layer)
        c.add_ref(bbox_subtracted)

        return c


def main():
    design = PhotonicDesign(name="PhotonicDesign_CSAR")
    # debug = True
    debug=False
    design.create_design(debug=debug)

    if not debug:
        today_date = datetime.now().strftime("%d-%m-%y")
        base_directory = r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM"
        # base_directory = r"C:\PyLayout\PyLayout"
        output_file = os.path.join(base_directory, f"MDMB-{today_date}.gds")
        design.component.write_gds(output_file)
        print(f"Design saved to {output_file}")

if __name__ == "__main__":
    main()
