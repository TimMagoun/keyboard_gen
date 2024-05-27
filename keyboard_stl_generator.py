#!/usr/bin/env python3

import argparse
from asyncio import subprocess
import json

from file_io import config_logger, load_keyboard_layout, make_output_folder

# import math
from pathlib import Path
import logging

# import time
from solid import union

from solid.utils import right, up


from parameters import Parameters
from keyboard import Keyboard
from cable import Cable
from solid import scad_render_to_file

# Set logger level variables
console_logging_level = logging.WARN
file_logging_level = logging.DEBUG


logger = config_logger(console_logging_level, file_logging_level)


# Helper for parser to wnsure filename argument has to correct extension
def CheckExt(choices):
    class Act(argparse.Action):
        def __call__(self, parser, namespace, fname, option_string=None):
            ext = Path(fname).suffix[1:].lower()
            if ext not in choices:
                option_string = "({})".format(option_string) if option_string else ""
                parser.error(
                    "file doesn't end with one of {}{}".format(choices, option_string)
                )
            else:
                setattr(namespace, self.dest, fname)

    return Act


def main():

    parser = argparse.ArgumentParser(
        description="Build custom keyboard SCAD file using keyboard layout editor format"
    )
    parser.add_argument(
        "-i",
        "--input-file",
        metavar="layout_json_file_name.json",
        help="A path to a keyboard layout editor json file",
        required=True,
        action=CheckExt({"json"}),
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        default="output",
        help="A path to a folder to store the generated files",
    )

    parser.add_argument(
        "-p",
        "--parameter-file",
        metavar="parameters.json",
        help="A JSON file containing paramters for the object buing made",
        default=None,
        action=CheckExt({"json"}),
    )
    parser.add_argument(
        "-s",
        "--section",
        metavar="section_num",
        help="The number of the section that should be built",
        type=int,
        default=-1,
    )
    parser.add_argument(
        "-a",
        "--all-sections",
        help="Output all the parts for all possible sections in separate files",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--exploded",
        help="Create test file with each section shown as an exploded view",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--fragments",
        metavar="num_fragments",
        help="The number of fragments to be used when creating curves",
        type=int,
        default=8,
    )
    parser.add_argument(
        "-r",
        "--render",
        help="Render an STL from the generated scad file",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--switch-type-in-filename",
        help="Add the switch type name and stabilizer type name to the filname",
        default=False,
        action="store_true",
    )

    # Parse command line arguments
    args = parser.parse_args()
    logger.debug(vars(args))

    # Create Path object from input file argument
    input_file_path = Path(args.input_file)
    layout_name = input_file_path.stem
    scad_folder_path, stl_folder_path = make_output_folder(
        args.output_folder, layout_name
    )
    logger.debug("scad_folder_path: %s", scad_folder_path)
    logger.debug("stl_folder_path: %s", stl_folder_path)

    # define output file extensions
    scad_postfix = ".scad"
    stl_postfix = ".stl"

    # Open JSON layout file
    logger.debug("Open layout file %s", input_file_path)
    keyboard_layout_dict = load_keyboard_layout(input_file_path)
    logger.debug("keyboard_layout_dict: %s", str(keyboard_layout_dict))

    # Read parameter file
    parameter_dict = {}
    if args.parameter_file is not None:
        with open(args.parameter_file) as f:
            parameter_dict = json.load(f)
    # Set parameters from imput file
    parameters = Parameters(parameter_dict)

    # Create Keyboard instance
    keyboard = Keyboard(parameters)

    # Process the keyboard layout object
    keyboard.process_keyboard_layout(keyboard_layout_dict)
    keyboard.process_custom_shapes()

    logger.debug("kerf: %f", keyboard.kerf)

    # Dictionary of SolidPython solid objects that need to be rendered to SCAD and to STL if desired
    solid_object_dict = {}

    # Create objects for each of the generated sections
    if args.all_sections:
        # Iterate over all sections generated and add all sections to solid_object_dict
        for section in range(keyboard.get_top_section_count()):
            # Set current section for generator
            keyboard.set_section(section)

            # Create dict for section
            solid_object_dict[section] = {}

            # Add top assembly, plate, and all assembly to section dict
            solid_object_dict[section]["top"] = keyboard.get_assembly(top=True)
            solid_object_dict[section]["all"] = keyboard.get_assembly(all=True)
            solid_object_dict[section]["plate"] = keyboard.get_assembly(plate_only=True)

            # If there is a bottom section for the current section add it to section dict
            if section < keyboard.get_bottom_section_count():
                solid_object_dict[section]["bottom"] = keyboard.get_assembly(
                    bottom=True
                )

    # Create exploded object
    elif args.exploded:
        solid_object_dict[-1] = {}
        solid_object_dict[-1]["top"] = union()
        solid_object_dict[-1]["plate"] = union()
        solid_object_dict[-1]["bottom"] = union()
        for section in range(keyboard.get_top_section_count()):
            keyboard.set_section(section)
            solid_object_dict[-1]["top"] += up(5 * section)(
                right(10 * section)(keyboard.get_assembly(top=True))
            )
            solid_object_dict[-1]["plate"] += up(5 * section)(
                right(10 * section)(keyboard.get_assembly(plate_only=True))
            )
            if section < keyboard.get_bottom_section_count():
                solid_object_dict[-1]["bottom"] += up(5 * section)(
                    right(10 * section)(keyboard.get_assembly(bottom=True))
                )

    # Create objects for a specified section
    elif args.section > -1:
        # Set desired section to create
        keyboard.set_section(args.section)

        # Create dict for section
        solid_object_dict[args.section] = {}

        # Add top assembly, plate, and all assembly to section dict
        solid_object_dict[args.section]["top"] = keyboard.get_assembly(top=True)
        solid_object_dict[args.section]["all"] = keyboard.get_assembly(all=True)
        solid_object_dict[args.section]["plate"] = keyboard.get_assembly(
            plate_only=True
        )

        # If there is a bottom section for the current section add it to section dict
        if args.section < keyboard.get_bottom_section_count():
            solid_object_dict[args.section]["bottom"] = keyboard.get_assembly(
                bottom=True
            )

    # Create an objects that are not split into sections. No other options were specified
    else:
        logger.debug("Create whole object. No other options specified")
        solid_object_dict["all"] = {}
        solid_object_dict["all"]["top"] = keyboard.get_assembly(top=True)
        solid_object_dict["all"]["bottom"] = keyboard.get_assembly(bottom=True)
        solid_object_dict["all"]["all"] = keyboard.get_assembly(all=True)
        solid_object_dict["all"]["plate"] = keyboard.get_assembly(plate_only=True)

    # Add global items that are not dependant on the sctions or parts of the item to build
    solid_object_dict["global"] = {}

    # Generate a strain relief piece for the cable hole
    if parameters.cable_hole:
        cable = Cable(parameters)
        solid_object_dict["global"]["cable_holder_main"] = cable.holder_main()
        solid_object_dict["global"]["cable_holder_clamp"] = cable.holder_clamp()
        solid_object_dict["global"]["cable_holder_all"] = cable.holder_all()

    print(parameters)
    print(
        "Case Height: %f, Case Width: %f\n"
        % (parameters.real_case_height, parameters.real_case_width)
    )

    logger.info(
        "Case Height: %f, Case Width: %f",
        parameters.real_case_height,
        parameters.real_case_width,
    )
    logger.info("Sections In Top: %d", keyboard.get_top_section_count())
    logger.info("Sections In Bottom: %d", keyboard.get_bottom_section_count())

    ############################################################
    # Render SCAD and STL files
    ############################################################
    subprocess_dict = {}

    switch_type_for_filename = ""
    stab_type_for_filename = ""

    for section in solid_object_dict.keys():

        if args.switch_type_in_filename:
            switch_type_for_filename = "_" + parameters.switch_type
            stab_type_for_filename = "_" + parameters.stabilizer_type

        section_postfix = ""

        # Creating global items that have no relaton to switch type
        if isinstance(section, str) and section == "global":
            switch_type_for_filename = ""
            stab_type_for_filename = ""

        # If the current object dict section is an int greater than -1 add the section number to the filename
        if isinstance(section, int) and section > -1:
            section_postfix = "_section_%d" % (section)

        if args.exploded:
            section_postfix = "_exploded"

        for part_name in solid_object_dict[section].keys():
            part_name_formatted = "_" + part_name

            scad_file_name = scad_folder_path / (
                layout_name
                + section_postfix
                + part_name_formatted
                + switch_type_for_filename
                + stab_type_for_filename
                + scad_postfix
            )
            stl_file_name = stl_folder_path / (
                layout_name
                + section_postfix
                + part_name_formatted
                + switch_type_for_filename
                + stab_type_for_filename
                + stl_postfix
            )

            # Set fragments to be used when creating curves
            if solid_object_dict[section][part_name] is not None:
                logger.info("Generate scad file with name %s", scad_file_name)
                # Generate SCAD file from assembly
                scad_render_to_file(
                    solid_object_dict[section][part_name],
                    scad_file_name,
                    file_header=f"$fn = {args.fragments};",
                )
                print("Generated scad file with name", scad_file_name)

                # Render STL if option is chosen
                if args.render:
                    logger.debug("Render STL from SCAD")
                    logger.info(
                        "Generate stl file with name %s from %s",
                        stl_file_name,
                        scad_file_name,
                    )

                    openscad_command_list = [
                        "openscad",
                        "-o",
                        "%s" % (stl_file_name),
                        "%s" % (scad_file_name),
                    ]
                    subprocess_dict[stl_file_name] = subprocess.Popen(
                        openscad_command_list
                    )

    ################################################################
    #  Wait for render processes to complete
    ################################################################
    if args.render:
        logger.debug(subprocess_dict)
        running = True
        while running:
            running = False
            for stl_file_name in subprocess_dict.keys():
                p = subprocess_dict[stl_file_name]
                if p is not None:
                    # running = True
                    rcode = None
                    try:
                        rcode = p.wait(0.1)
                    except subprocess.TimeoutExpired as err:
                        logger.error(err)
                        running = True
                    if rcode is not None:
                        logger.info("Render Complete: file: %s", stl_file_name)
                        print("Render Complete: file:", stl_file_name)
                        subprocess_dict[stl_file_name] = None
            # time.sleep(1)

    logger.info("Generation Complete")


if __name__ == "__main__":
    main()
