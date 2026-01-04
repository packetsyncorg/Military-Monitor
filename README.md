# Military Monitor 🛩️

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/Textual-TUI%20Framework-yellow.svg)](https://textual.textualize.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

![Military Monitor Screenshot](https://raw.githubusercontent.com/packetsyncorg/Military-Monitor/main/milmon.png)

A real-time terminal-based application for tracking global military aircraft using live data from ADSB.lol. Features a responsive Terminal User Interface (TUI) with filtering, alerts, and comprehensive logging.

## ✨ Features

- **Real-time Tracking**: Live military aircraft data from ADSB.lol API
- **Responsive TUI**: Terminal-based interface built with Textual framework
- **Smart Filtering**: Filter aircraft by 10+ categories with two-column layout
- **Offensive Aircraft Alerts**: Real-time alerts for fighters and bombers
- **System Logging**: Built-in debug log with timestamped messages
- **Customizable Display**: Zebra-striped tables, color-coded alerts
- **Hotkeys**: Quick actions for refresh, clear logs, and quit

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Install from source

```bash
# Clone the repository
git clone https://github.com/packetsyncorg/military-monitor.git
cd military-monitor

# Install dependencies
pip install -r requirements.txt

# Run the application
python monitor.py

