# DualColors

A tool for managing your DualSense controller's RGB lighting.

## Features

- Set custom colors on your DualSense controller
- RGB Mode (Rainbow)
- Gradient Mode 

## Requirements

- Python
- pydualsense library
- hidapi library

## Installation

```bash
pip install pydualsense hidapi
```

## Usage

### Powershell
```bash
cd "The path of the folder"
python main.py
```

## Color File

Colors are defined in `colors.txt` in a specific format:
```
color_name=r,g,b
```
You can always add more colors to the file, but make sure to follow the format.

## Controller Connection

Make sure your DualSense controller is connected via USB or Bluetooth __before__ running the script.
