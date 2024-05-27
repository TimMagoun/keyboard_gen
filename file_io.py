import json
import logging
from pathlib import Path
import re


def make_output_folder(output_folder: str, layout_name: str):
    base_path = Path(output_folder) / layout_name
    scad_folder_path = base_path / "scad"
    stl_folder_path = base_path / "stl"

    base_path.mkdir(parents=True, exist_ok=True)
    scad_folder_path.mkdir(parents=True, exist_ok=True)
    stl_folder_path.mkdir(parents=True, exist_ok=True)

    return scad_folder_path, stl_folder_path


def config_logger(console_logging_level, file_logging_level):
    # Get root logger and set main logger level to DEBUG
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create formatters
    console_formatter = logging.Formatter(
        "%(name)s %(levelname)s: %(funcName)s: [%(lineno)d]: %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(funcName)s: [%(lineno)d]: %(message)s"
    )

    # Create console handler and set level to info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_logging_level)

    # Add formatter to console_handler
    console_handler.setFormatter(console_formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    # Get file info that will be used to creat log file
    script_location = Path(__file__).resolve().parent
    log_file_name = "generator.log"
    log_file_path = script_location / log_file_name

    # Create file handler and set level to info
    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setLevel(file_logging_level)

    # Add formatter to file_handler
    file_handler.setFormatter(file_formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

    return logger


def load_keyboard_layout(input_file_path: Path):
    # Pattern and Replacement strings to be used when trying to turn keyboard-layout-editor raw output into valid JSON
    json_key_pattern = "([{,])([xywha1]+):"
    json_key_replace = '\\1"\\2":'

    keyboard_layout = input_file_path.read_text()
    # If json comes from Keyboard Layout Editor, it needs to be modified to be valid JSON
    keyboard_layout = re.sub(json_key_pattern, json_key_replace, keyboard_layout)
    return json.loads(keyboard_layout)
