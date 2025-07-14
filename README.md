# ladderlogic-gen
Universal CLI tool to generate ladder logic code for Siemens, Allen-Bradley, Mitsubishi, and Omron PLCs from simple text descriptions—including support for timers, counters, and complex logic.
Uniiversal Ladder Logic Generator for PLCs
Features
Generate ladder logic for Siemens, Allen-Bradley, Mitsubishi, and Omron PLCs
Supports AND, OR, NOT, parentheses, comparisons, timers (TON/TOF), and counters (CTU/CTD)
Simple text-based input
CLI interface, cross-platform (Python 3.7+)

Installation
git clone https://github.com/yourusername/logicladder-gen.git
cd logicladder-gen
pip install -r requirements.txt

Usage
Prepare a logic file, e.g. logic.txt:

IF Start AND NOT Stop THEN Motor
IF (Start OR Reset) THEN TON Timer1, 5s
IF Timer1 THEN Lamp
IF CountBtn THEN CTU Counter1, 10
IF Counter1 > 5 THEN Alarm
IF (Button1 OR (Button2 AND NOT Button3)) THEN Lamp, Buzzer

Generate ladder logic for your platform:
python logicladder.py --input logic.txt --platform siemens --output output.lad
python logicladder.py --input logic.txt --platform allen-bradley --output output.lad
python logicladder.py --input logic.txt --platform mitsubishi --output output.lad
python logicladder.py --input logic.txt --platform omron --output output.lad

Example Output
# For Siemens
// Rung
|----[ ] Start----[/] Stop----( )----|
     Motor

// Rung
|----[ ] Start----( )----|
     TON Timer1 Time: 5s

...
