import numpy as np
import gdstk
import gdsfactory as gf
from functools import partial
from pathlib import Path
from datetime import datetime
import os

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

    def add_taper(self,c, taper_length, taper_width, taper_separation, length_mmi, width2):
        taper_up = c.add_ref(
            gf.components.taper(length=taper_length - 4, width1=taper_width, width2=width2, layer=(1, 0))
        )
        taper_up.dmove((length_mmi + taper_length, taper_separation / 2))

        taper_down = c.add_ref(
            gf.components.taper(length=taper_length - 4, width1=taper_width, width2=width2, layer=(1, 0))
        )
        taper_down.dmove((length_mmi + taper_length, -taper_separation / 2))
        return taper_up, taper_down

    def add_fish_components(self,c, gds_file, length_mmi, taper_length, taper_separation):
        fish_component = gf.import_gds(Path(gds_file))
        c.add_ref(fish_component).dmove((length_mmi + taper_length * 2 - 4, taper_separation / 2))
        c.add_ref(fish_component).dmove((length_mmi + taper_length * 2 - 4, -taper_separation / 2))

    def create_mmi(self, resonator_type="fish", length_mmi=73.5, name=None):
        """
        Creates a 2x2 MMI structure with specified parameters.

        Returns:
            gf.Component: The MMI component with input and output tapered sections.
        """

        width = 6
        taper_separation = 2.0308
        taper_length = 10
        taper_width = 1.2
        waveguide_width = 0.35
        corner_support_width = 1

        # Create a new component for the MMI
        c = gf.Component()

        # Define the main MMI region
        mmi_section = gf.components.straight(length=length_mmi, width=width, layer=(1, 0))
        mmi_ref = c.add_ref(mmi_section)
        mmi_ref.dmove((taper_length, 0))  # Position the MMI after the input tapers

        # Define the taper structure with the wide end set to taper_width
        taper_in = gf.components.taper(length=taper_length, width1=waveguide_width,  # Narrow end of the taper
                                       width2=taper_width,  # Wide end of the taper, set to connect to MMI width
                                       layer=(1, 0))

        # Place the input tapers on the left side of the MMI
        taper_in1 = c.add_ref(taper_in)
        taper_in1.dmove((0, taper_separation / 2))  # Position above the MMI centerline

        taper_in2 = c.add_ref(taper_in)
        taper_in2.dmove((0, -taper_separation / 2))  # Position below the MMI centerline

        # Load and add the selected type structure on the right side of the MMI
        if resonator_type == "fish":
            self.add_taper(c, taper_length, taper_width, taper_separation, length_mmi, width2=0.68)
            self.add_fish_components(c, 'FISHi_200nm.gds', length_mmi, taper_length, taper_separation)

        elif resonator_type == "extractor":
            self.add_taper(c, taper_length, taper_width, taper_separation, length_mmi, width2=0.592)
            self.add_fish_components(c, 'QT10i_180nm.gds', length_mmi, taper_length, taper_separation)

        x = gf.CrossSection(sections=[gf.Section(width=waveguide_width, layer=(1, 0), port_names=("in", "out"))])

        out_taper_length = 3
        coupler_down = c.add_ref(gf.components.taper(length=out_taper_length, width2=waveguide_width, width1=0.08, layer=(1, 0))).dmovey(
            -taper_separation / 2).dmovex(-out_taper_length)
        coupler_up = c.add_ref(gf.components.taper(length=out_taper_length, width2=waveguide_width, width1=0.08, layer=(1, 0))).dmovey(
            taper_separation / 2).dmovex(-out_taper_length)
        coupler = gf.boolean(A=coupler_up, B=coupler_down, operation="or", layer=(1, 0))

        # MMI Supports
        c.add_ref(gf.components.taper(length=1.5, width1=0.4 + corner_support_width, width2=corner_support_width, layer=(1, 0))).drotate(90).dmove(
            (10 + corner_support_width/2, -width + 1.5))
        c.add_ref(gf.components.taper(length=1.5, width1=0.4 + corner_support_width, width2=corner_support_width, layer=(1, 0))).drotate(
            90).mirror_y().dmove((10 + corner_support_width/2, width - 1.5))

        c.add_ref(gf.components.taper(length=1.5, width1=0.6, width2=0.2, layer=(1, 0))).drotate(90).dmove((10 + length_mmi / 3, -width + 1.5))

        c.add_ref(gf.components.taper(length=1.5, width1=0.6, width2=0.2, layer=(1, 0))).drotate(90).mirror_y().dmove(
            (10 + length_mmi / 3, width - 1.5))
        c.add_ref(gf.components.taper(length=1.5, width1=0.6, width2=0.2, layer=(1, 0))).drotate(90).dmove((10 + length_mmi * 2 / 3, -width + 1.5))
        c.add_ref(gf.components.taper(length=1.5, width1=0.6, width2=0.2, layer=(1, 0))).drotate(90).mirror_y().dmove(
            (10 + length_mmi * 2 / 3, width - 1.5))

        c.add_ref(gf.components.taper(length=1.5, width1=0.4 + corner_support_width, width2=corner_support_width, layer=(1, 0))).drotate(90).dmove(
            (length_mmi + 9 + corner_support_width/2, -width + 1.5))
        c.add_ref(gf.components.taper(length=1.5, width1=0.4 + corner_support_width, width2=corner_support_width, layer=(1, 0))).drotate(
            90).mirror_y().dmove((length_mmi + 9 + corner_support_width/2, width - 1.5))

        Device = gf.boolean(A=c, B=coupler, operation="or", layer=(1, 0))

        # Set the name if provided
        if name:
            Device.name = name

        return Device

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
        scalebar_ref.dmove(position)

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
        component.add_ref(label)

    def create_design(self, is_resist_positive=True):
        quick_run = True
        quick_run = False
        y_spacing = 9  # Fixed vertical spacing
        gap_between_fish_and_extractor = 40
        additional_patterns_offset = -40
        rect_clearance_length = 50
        length_mmi = 74

        c = self.component

        # Configuration settings
        config = {"N_rows_MMI": 4, "N_cols_MMI": 1, "N_Bulls_eye": 0, "add_logo": True, "add_rectangle": True, "add_scalebar": True}
        resonator_types = ["fish", "extractor"]
        is_resist_positive = True

        if quick_run:
            config.update({"N_rows_MMI": 4, "N_cols_MMI": 1, "N_Bulls_eye": 0, "add_logo": False, "add_scalebar": True})
            resonator_types = ["fish"]
            is_resist_positive = True

        n_rows = config["N_rows_MMI"]


        # Create and arrange MMI structures if applicable
        if n_rows > 0:
            straight_comps = [{"length": length_mmi + 26, "width": y_spacing, "offset_x": -5, "offset_y": 0},]

            # Combine all components into a single geometry
            combined_geometry = None
            for i, comp in enumerate(straight_comps):
                straight = gf.components.straight(length=comp["length"], width=comp["width"], layer=(1, 0))
                tmp_ref = gf.Component().add_ref(straight).dmovex(comp["offset_x"]).dmovey(comp["offset_y"])
                combined_geometry = tmp_ref if combined_geometry is None else gf.boolean(A=combined_geometry, B=tmp_ref, operation="or", layer=(1, 0))

            # Initialize final geometry for all resonators
            global_geometry = gf.Component()

            # Add MMI patterns with different resonator types
            for i, resonator_type in enumerate(resonator_types):
                mmi = self.create_mmi(resonator_type=resonator_type, length_mmi=length_mmi)
                if is_resist_positive:
                    mmi = gf.boolean(A=combined_geometry, B=mmi, operation="A-B", layer=(1, 0))
                array_ref = gf.Component().add_ref(self.unite_array(mmi, rows=n_rows, cols=config["N_cols_MMI"], spacing=(0, y_spacing),
                                                                    name=f"mmi_{resonator_type}"))
                array_ref.dmovey(((n_rows + 1) * y_spacing - 7 + gap_between_fish_and_extractor) * i)
                # c.add_ref(gf.boolean(A=array_ref, B=array_ref, operation="or", layer=(1, 0)))

                # Parameters for adding rectangles

                rect_params = [
                    (rect_clearance_length, y_spacing * n_rows, -4.5, -rect_clearance_length - 5),
                    (64.8, 1.5, y_spacing * n_rows - 5.25, -rect_clearance_length - 5),
                    (length_mmi / 3 - 1.5, 1.5, y_spacing * n_rows - 5.25, -rect_clearance_length + 64.8 - 3.6),
                    (length_mmi / 3 - 0.6, 1.5, y_spacing * n_rows - 5.25, -rect_clearance_length + 64.8 - 4.5 + length_mmi / 3),
                    (length_mmi / 3 - 1.5, 1.5, y_spacing * n_rows - 5.25, -rect_clearance_length + 64.8 - 4.5 + length_mmi * 2 / 3),
                    (10.8, 1.5, y_spacing * n_rows - 5.25, -rect_clearance_length + 64.8 - 4.6 + length_mmi),
                    (64.8, 1.5, -5.25, -rect_clearance_length - 5),
                    (length_mmi / 3 - 1.5, 1.5, -5.25, -rect_clearance_length + 64.8 - 3.6),
                    (length_mmi / 3 - 0.6, 1.5, -5.25, -rect_clearance_length + 64.8 - 4.5 + length_mmi / 3),
                    (length_mmi / 3 - 1.5, 1.5, -5.25, -rect_clearance_length + 64.8 - 4.5 + length_mmi * 2 / 3),
                    (10.8, 1.5, -5.25, -rect_clearance_length + 64.8 - 4.6 + length_mmi)
                ]

                # List to collect individual rectangles
                rectangles = []

                # Add rounded rectangles to the layout
                for idx, param in enumerate(rect_params):
                    # length, width, y_base_offset, y_shift, x_offset = param
                    length, width, y_offset, x_offset = param

                    corner_radius = 0.75 if idx != 0 else 0.0  # No rounded corners for the first rectangle

                    rect = create_rounded_rectangle(
                        length=length,
                        width=width,
                        corner_radius=corner_radius,
                        layer=(1, 0)  # Set the appropriate layer
                    )
                    rect_ref = gf.Component().add_ref(rect)

                    y_position = y_offset + (gap_between_fish_and_extractor + y_spacing * n_rows + 2) * i

                    rect_ref.dmovey(y_position).dmovex(x_offset)
                    rectangles.append(rect_ref)
                    # c.add_ref(rect).dmovey(y_position).dmovex(x_offset)

                # Merge all rectangles into a single geometry
                if len(rectangles) > 1:
                    # Start merging with the first rectangle
                    merged_geometry = rectangles[0]
                    for rect in rectangles[1:]:
                        # Perform the boolean operation to merge each rectangle
                        merged_geometry = gf.boolean(A=merged_geometry, B=rect, operation="or", layer=(1, 0))
                else:
                    merged_geometry = rectangles[0]  # If only one rectangle, no need to merge

                # Merge the array_ref and merged rectangles
                final_geometry = gf.boolean(A=array_ref, B=merged_geometry, operation="or", layer=(1, 0))

                # Combine final_geometry into the global layout
                global_geometry = gf.boolean(A=global_geometry, B=final_geometry, operation="or", layer=(1, 0))

        # Add the final merged geometry to the layout
        c.add_ref(global_geometry)

        ############### Bulls eye #################
        if config["N_Bulls_eye"] > 0:
            a = gf.components.circle(radius=5.8, layer=(1, 0))
            s1 = gf.Component().add_ref(gf.components.straight(length=0.2, width=20, layer=(1, 0))).dmovex(-0.1)
            a = gf.boolean(A=a, B=s1, operation="A-B", layer=(1, 0))

            gds_file = Path('Bulls_Eye_Layout_v1.1.gds')
            b = gf.import_gds(gds_file)
            b.name = "GDS_Import"

            if is_resist_positive:
                b = gf.boolean(A=a, B=b, operation="A-B", layer=(1, 0))
            c.add_ref(self.unite_array(b, cols=config["N_Bulls_eye"], rows=1, spacing=(12.5, 12.5), name="Bulls-eye")).dmovey(-20).dmovex(
                additional_patterns_offset + 32)

        ################ Logo #################
        if config["add_logo"]:
            c.add_ref(self.logo(name="Logo")).dmovey(-20).dmovex(additional_patterns_offset)


        # Adding the scalebar to your component
        if config["add_scalebar"] > 0:
            self.add_scalebar(component=c, size=100, position=(additional_patterns_offset + 25, -25), font_size=10)
            self.add_scalebar(component=c, size=10, position=(additional_patterns_offset + 30, -30), font_size=5)

        c.show()
        return c

def main():
    design = PhotonicDesign(name="PhotonicDesign_CSAR")
    c = design.create_design(is_resist_positive=True)

    ToSave = True
    # Get today's date in the desired format (DD-MM-YY)
    today_date = datetime.now().strftime("%d-%m-%y")

    # Define the base directory for saving the GDS files
    base_directory = r"Q:\QT-Nano_Fabrication\6 - Project Workplan & Layouts\GDS_Layouts\Shai GDS Layout\MDM"

    if ToSave:
        output_file = os.path.join(base_directory, f"MDM-C-{today_date}.gds")
        design.component.write_gds(output_file)
        print(f"Design saved to {output_file}")

    # design = PhotonicDesign(name="PhotonicDesign_neg_resist")  # c = design.create_design(is_resist_positive=False)  #  # if ToSave:  #     output_file = f"MDM-{today_date}_neg_resist_BR16.gds"  #     design.component.write_gds(output_file)  #     print(f"Design saved to {output_file}")


if __name__ == "__main__":
    main()
