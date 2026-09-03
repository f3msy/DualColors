# Astro

A tool for managing your PS5 DualSense controller's RGB lighting.

## Features

- Set custom colors on your DualSense controller
- RGB mode (Rainbow)

## Requirements

- Python 3.7+
- pydualsense library
- hidapi library

## Installation

```bash
pip install pydualsense hidapi
```

## Usage

```bash
python main.py
```

## Color File

Colors are defined in `colors.txt` in the format:
```
color_name=r,g,b
```
You can always add more colors to the file, but make sure to follow the format.

## Controller Connection

Make sure your DualSense controller is connected via USB or Bluetooth before running the script.
