# Raspberry Pi QR Scanner System - Complete Setup Guide

## Overview

This system replaces your current Google Apps Script QR scanning approach with dedicated Raspberry Pi 5 scanners at each station. Each Pi provides:

- **Dedicated QR scanning** with USB barcode scanners (camera fallback optional)
- **Real-time data validation** to prevent multi-scan conflicts  
- **Direct Google Sheets integration** via API (no manual cell editing)
- **Local AI processing** for error detection and data quality
- **Hardware feedback** (LED status, buzzer alerts)
- **Offline capability** with data sync when connection resumes

## System Architecture

```
Station 1 (CNC) ──┐
Station 2 (H10) ──┤
Station 3 (Edge) ─┤──► Google Sheets API ──► Your Existing Workflow
Station 4 (Dowel) ┤
Station 5 (Sort) ──┤
Station 6 (Pull) ──┘

Each Pi: Barcode Scanner (or Camera) + GPIO + Local AI + WiFi/Ethernet
```

## Hardware Requirements

### Per Station:
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **USB Barcode Scanner** (Honeywell/Xenon or any HID keyboard-style scanner)
- **Optional:** Pi Camera Module or USB Webcam (only if you prefer camera mode)
- **MicroSD Card** (64GB Class 10 minimum)
- **Power Supply** (Official Pi 5 power adapter)
- **Case** with camera mount
- **Optional**: LED, buzzer, pushbutton for feedback

### Recommended Accessories:
- **GPIO Breakout Board** for easy LED/buzzer connections
- **WiFi Adapter** (if using ethernet isn't preferred)
- **Heat Sinks** for continuous operation

## Pre-Installation Setup

### 1. Google Sheets API Setup

**CRITICAL**: You must complete this first before installing on any Pi.

```bash
# Download and run the API setup script
./setup_google_api.sh
```

This will guide you through:
1. Creating Google Cloud Project
2. Enabling Google Sheets API  
3. Creating service account credentials
4. Downloading `credentials.json`
5. Sharing your spreadsheet with the service account

**Save `credentials.json`** - you'll copy this to all 6 Raspberry Pis.

### 2. Prepare Raspberry Pi Images

For each of the 6 Raspberry Pis:

1. **Flash Raspberry Pi OS** (64-bit recommended)
2. **Enable SSH** (add empty `ssh` file to boot partition)
3. **Configure WiFi** (add `wpa_supplicant.conf` to boot partition):

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourWiFiName"
    psk="YourWiFiPassword"
}
```

## Station Installation Process

### Step 1: Basic Pi Setu

For each Raspberry Pi:

```bash
# SSH into the Pi
ssh pi@<pi-ip-address>

# Update system
sudo apt update && sudo apt upgrade -y

# Download installation script
wget https://raw.githubusercontent.com/yourusername/qr-scanner/main/install.sh
chmod +x install.sh

# Run installation
./install.sh
```

The installer will:
- Install all Python dependencies
- Set up camera and GPIO
- Create systemd service 
- Configure logging
- Create directory structure
- Set up the configuration system

### Step 2: Station Configuration

```bash
# Run configuration tool
cd ~/qr-scanner
./configure.sh
```

Configure for each station:

| Station | Code | Description |
|---------|------|-------------|
| 1 | CNC | CNC Station |
| 2 | H10 | CNC Station 2 |
| 3 | Edge | Edge Banding |
| 4 | Dowel | Dowel Insertion |
| 5 | Sort | Parts Sorting |
| 6 | Pull | Parts Pulling |
| 7 | Assembly | Cabinet Assembly |
| 8 | QC | Quality Control |
| 9 | Wrap | Packaging |
| 10 | Ship | Shipping |

After selecting the station, choose **3) Configure Input Source**:

- Leave the default `USB Barcode Scanner` to use any HID-style scanner (auto-detects when left blank)
- Provide a specific device path such as `/dev/input/by-id/usb-Honeywell_Scanner-event-kbd` if you want to lock to one scanner
- Switch to `Camera` only if you plan to run with a Pi Camera/USB webcam

Helpful command to list devices:

```bash
ls /dev/input/by-id | grep -i scanner
```

### Step 3: Copy Credentials

```bash
# Copy Google Sheets credentials to each Pi
scp credentials.json pi@<pi-ip>:~/qr-scanner/config/
```

### Step 4: Test Installation

```bash
# Test all components
./configure.sh
# Select options 6, 7, 8 to test camera, GPIO, and Google Sheets
```

### Step 5: Start Services

```bash
# Start the scanner service
sudo systemctl start qr-scanner

# Enable auto-start on boot
sudo systemctl enable qr-scanner

# Check status
sudo systemctl status qr-scanner
```

## Combined Station Workflow

### Sort + Dowel
- `station_sort` and `station_dowel` now run on a single Pi. Operators must scan the bin QR code **before** scanning any part QR.
- The scanner keeps the last bin scan in a short buffer (see `bin_context_timeout` in `config.json`). If the part scan happens before the timeout expires, the app pairs the bin with the part and records it in the Sheet.
- If the timeout expires, the scanner will ignore the part until a new bin QR is scanned, so encourage operators to keep the bin label handy.

### Pull + Assembly
- `station_pull` and `station_assembly` use the same bin-first flow so the sorter can stage totes for assembly without extra hardware.
- Assembly operators can re-use the same bin QR immediately; just scan the bin, then the part or cabinet label.

### Bin Labels
- Printable bin QR data lives in `bin_labels.csv` (52 Sort bins + 52 Pull bins). Import this CSV into your label software or Google Sheets to generate stickers.
- Labels follow the wording expected by the regex in `qr_scanner.py` (e.g., `Sort Bin 01`, `Pull Bin 14`). Keep this format if you create replacements.
- Mount the labels so the scanner can read them quickly; scanning the wrong side just means re-scanning the correct bin before the part.

## Operator Login Badges
- Any QR that starts with `Operator`, `LOGIN_OP`, or `OPID` (case-insensitive, colon optional) logs the current operator without sending anything to Google Sheets.
- Examples: `Operator: Justin Hoffman`, `LOGIN_OP:JM`, `OpId:TeamA`. Short codes (≤4 letters) are auto-uppercased, longer names keep their capitalization.
- After a badge scan, the name/code is attached to every subsequent part/bin record until another operator badge is scanned or the service restarts.
- You can keep the system headless—no buzzers or blocking prompts. The log file will show `Operator logged in: ...` so you can confirm it stuck.

## Configuration Files

### Main Config: `~/qr-scanner/config.json`

The repo ships `config.example.json`. On a real Pi install, copy it once:

```bash
cp config.example.json config.json
```

```json
{
  "station_id": "Station_CNC",
  "station_code": "CNC",
  "camera": {
    "device_id": 0,
    "resolution": [640, 480],
    "fps": 30
  },
  "input": {
    "mode": "barcode_scanner",
    "barcode_device": ""
  },
  "scanning": {
    "scan_timeout": 5.0,
    "duplicate_timeout": 30.0,
    "auto_advance": true,
    "validation_level": "lenient"
  },
  "bin_context_timeout": 3.0,
  "gpio": {
    "led_pin": 18,
    "buzzer_pin": 16, 
    "button_pin": 21
  },
  "local_ai": {
    "enabled": true,
    "model_path": "models",
    "inference_timeout": 2.0
  }
}
```

## GPIO Wiring Diagram

```
Raspberry Pi GPIO:
                    3V3  (1) (2)  5V
                   GPIO2 (3) (4)  5V  
                   GPIO3 (5) (6)  GND
                   GPIO4 (7) (8)  GPIO14
                     GND (9) (10) GPIO15
                  GPIO17 (11) (12) GPIO18 ── LED (Status)
                  GPIO27 (13) (14) GND
                  GPIO22 (15) (16) GPIO23 ── Buzzer
                     3V3 (17) (18) GPIO24
                  GPIO10 (19) (20) GND
                   GPIO9 (21) (22) GPIO25 ── Button
                  GPIO11 (23) (24) GPIO8
                     GND (25) (26) GPIO7

LED Circuit:
GPIO18 ──[220Ω]── LED ──[GND]

Buzzer Circuit: 
GPIO23 ──[Buzzer]── GND

Button Circuit:
GPIO25 ──[Button]── GND (with internal pull-up)
```

## Troubleshooting

### Barcode Scanner Issues

```bash
# List connected HID devices
ls /dev/input/by-id | grep -i scanner

# Monitor key events from a specific device
sudo evtest /dev/input/by-id/usb-Honeywell_Scanner-event-kbd

# Update config to new device path if needed
./configure.sh  # Option 3 -> Configure Input Source
```

- If no devices are detected, unplug/replug the scanner and check `dmesg | tail`
- Leaving the device path blank in the configurator enables auto-detection on startup
- Ensure the scanner is programmed to send a trailing Enter key (most units do by default)

### Camera Issues

```bash
# Check camera detection
lsusb  # For USB cameras
vcgencmd get_camera  # For Pi camera module

# Test camera manually
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
print('Camera opened:', cap.isOpened())
ret, frame = cap.read()
print('Frame captured:', ret)
cap.release()
"
```

### Google Sheets Connection Issues

```bash
# Test API connection
python3 -c "
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('~/qr-scanner/config/credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('REPLACE_WITH_YOUR_SHEET_ID')
print('Connection successful:', sheet.title)
"
```

### Service Issues

```bash
# View service logs
journalctl -u qr-scanner -f

# View application logs  
tail -f ~/qr-scanner/logs/qr_scanner.log

# Restart service
sudo systemctl restart qr-scanner

# Check service configuration
sudo systemctl cat qr-scanner
```

### GPIO Issues

```bash
# Check GPIO permissions
groups pi  # Should include 'gpio'

# Test GPIO manually
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)  # LED should turn on
print('LED should be on')
"
```

## Data Flow Changes

### Before (Google Apps Script):
1. Operator scans QR code
2. Data goes directly into Scan_Log cell A
3. onEdit trigger processes in real-time
4. Risk of multi-scan conflicts in same cell
5. All processing happens in Google Sheets

### After (Raspberry Pi System):
1. Dedicated Pi camera scans QR code
2. **Local validation** and duplicate detection
3. **Structured API call** to Google Sheets
4. Data written to **specific columns** (not single cell)
5. **Immediate feedback** via LED/buzzer
6. **Local AI** learns patterns and suggests corrections

## Advantages of New System

### Reliability
- **No more multi-scan conflicts** - each scan is validated locally
- **Duplicate detection** prevents accidental double-scans
- **Offline capability** - scans are cached if network is down
- **Hardware feedback** - operators get immediate confirmation

### Data Quality  
- **Real-time validation** catches errors before they reach Google Sheets
- **Structured data** - each field goes to correct column
- **AI-powered suggestions** for data corrections
- **Error pattern learning** identifies recurring issues

### Performance
- **Faster scanning** - no waiting for Google Sheets response
- **Reduced API calls** - only successful scans are sent
- **Local caching** - works even with poor internet
- **Dedicated hardware** - no browser/device dependencies

### Scalability
- **Easy to add stations** - just deploy another Pi
- **Centralized configuration** - update all Pis from one location
- **Individual station analytics** - track performance per station
- **Future AI features** - local processing enables advanced analytics

## Migration Process

### Phase 1: Parallel Operation
1. Keep existing Google Apps Script running
2. Install Raspberry Pi systems at 2-3 stations
3. Compare data accuracy between old and new systems
4. Fine-tune validation rules based on real data

### Phase 2: Gradual Rollout
1. Deploy to remaining stations one by one
2. Monitor each station for 1 week before next deployment
3. Train operators on new LED/buzzer feedback system
4. Update any downstream processes that expect old data format

### Phase 3: Full Migration
1. Disable Google Apps Script onEdit triggers
2. Switch all stations to Raspberry Pi system
3. Archive old scanning workflow
4. Enable advanced AI features (trend detection, predictive maintenance)

## Maintenance

### Daily Tasks
- Check service status on all stations: `./check_all_stations.sh`
- Review error logs for any recurring issues
- Verify Google Sheets data is being updated correctly

### Weekly Tasks  
- Clean camera lenses on all stations
- Check available disk space: `df -h`
- Rotate log files: `sudo logrotate /etc/logrotate.d/qr-scanner`
- Backup configurations: `./backup_configs.sh`

### Monthly Tasks
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review AI analytics reports for all stations
- Update QR scanning patterns if needed
- Test disaster recovery procedures

## Support and Monitoring

### Remote Access
```bash
# SSH to any station
ssh pi@qr-scanner-h08.local  # If mDNS is working
ssh pi@192.168.1.100         # Direct IP

# View status of all stations
./monitor_all_stations.sh
```

### Monitoring Dashboard
The system includes a web-based monitoring dashboard accessible at:
`http://qr-scanner-h08.local:8080/dashboard`

Features:
- Real-time scan statistics
- Error rate tracking  
- Hardware status (camera, GPIO)
- Google Sheets connection status
- AI analytics reports

### Alert System
Configure alerts for:
- High error rates (>10% in 1 hour)
- Google Sheets connection failures
- Hardware malfunctions (camera, GPIO)
- Disk space warnings (<1GB free)
- Service crashes or restarts

## Advanced Features

### Local AI Integration
The system includes a local AI framework that:
- **Learns from scan patterns** to improve accuracy
- **Detects anomalies** in real-time
- **Suggests corrections** for malformed QR codes
- **Predicts maintenance needs** based on error patterns
- **Works offline** - no cloud AI dependencies

### Future Enhancements
- **Voice feedback** for operators
- **Barcode scanning** in addition to QR codes  
- **Integration with ERP systems** beyond Google Sheets
- **Mobile app** for station management
- **Machine learning** for predictive quality control

## Cost Analysis

### One-time Hardware Costs (6 stations):
- 6x Raspberry Pi 5 (8GB): $480
- 6x Pi Camera modules: $180
- 6x MicroSD cards (64GB): $120
- 6x Power supplies: $90
- 6x Cases with mounts: $120
- GPIO components (LEDs, buzzers, etc.): $60
- **Total Hardware: $1,050**

### Ongoing Costs:
- **Electricity**: ~$2/month per Pi = $12/month total
- **Internet bandwidth**: Minimal (only API calls)
- **Maintenance**: ~2 hours/month = $100/month (if outsourced)

### ROI Benefits:
- **Reduced data errors**: Save 5+ hours/week of correction time
- **Improved accuracy**: Reduce waste from misrouted parts
- **Better analytics**: Optimize production flow
- **Scalability**: Easy to add more stations as you grow

## Next Steps

1. **Order Hardware**: Get 6 Raspberry Pi 5 kits
2. **Setup Google API**: Complete the API authentication process  
3. **Pilot Installation**: Start with CNC stations
4. **Train Operators**: Show them new LED/buzzer feedback system
5. **Monitor and Adjust**: Fine-tune settings based on real usage
6. **Scale Up**: Deploy to remaining 4 stations
7. **Advanced Features**: Enable AI analytics and predictive maintenance

## Support Contacts

- **System Administrator**: Your IT team
- **Google Sheets Issues**: Check API quotas and permissions
- **Hardware Issues**: Raspberry Pi Foundation support
- **Custom Development**: Contact the system developer

---

This comprehensive setup provides a robust, scalable QR scanning solution that eliminates your current multi-scan conflicts while adding powerful new capabilities like real-time validation, local AI processing, and detailed analytics.