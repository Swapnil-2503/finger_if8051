# P89V51RD2 ISP Flashing Tool

A Python-based replacement for FlashMagic on Linux, specifically designed for Philips/NXP P89V51RD2 microcontroller with **automatic reset detection** (exactly like FlashMagic).

## Installation

### Prerequisites
```bash
# Install required Python packages
pip install pyserial --break-system-packages

# Make script executable
chmod +x p89_flasher.py
```

## Usage (Just like FlashMagic!)

```bash
# Run the tool - it will ask you to reset
python3 p89_flasher.py firmware.hex

# With custom port
python3 p89_flasher.py firmware.hex -p /dev/ttyUSB0

# With custom baud rate
python3 p89_flasher.py firmware.hex -b 19200
```

## How It Works (Like FlashMagic)

### Step 1: Connect Device
- Connect P89V51RD2 via USB-to-Serial adapter

### Step 2: Run Tool
```bash
python3 p89_flasher.py firmware.hex
```

### Step 3: Reset MCU When Prompted
```
======================================================================
[!] *** RESET YOUR MCU NOW ***
======================================================================

[*] Please perform ONE of the following:
    • Press RESET button on your board
    • Cycle power (disconnect/reconnect)
    • Hold RST LOW for 100ms then release

[*] The tool will automatically detect reset and enter ISP mode...
[*] Waiting for reset signal...
```

### Step 4: Tool Detects Reset and Programs

The tool **automatically**:
1. ✓ Detects when MCU resets (RX activity)
2. ✓ Controls DTR/RTS to enter ISP mode
3. ✓ Synchronizes with bootloader
4. ✓ Erases and programs flash
5. ✓ Verifies programming
6. ✓ Done!

## Example Output

```
$ python3 p89_flasher.py firmware.hex

[*] Opened port /dev/ttyUSB0 at 9600 baud

======================================================================
[!] *** RESET YOUR MCU NOW ***
======================================================================

[*] Please perform ONE of the following:
    • Press RESET button on your board
    • Cycle power (disconnect/reconnect)
    • Hold RST LOW for 100ms then release

[*] The tool will automatically detect reset and enter ISP mode...
[*] Waiting for reset signal...
................................[+] Reset detected! (2 bytes, after 3.2s)
[*] Entering ISP mode via DTR/RTS...
[+] ISP mode sequence completed
[*] Synchronizing with device...
[+] Device sync successful
[+] Device detected: P89V51RD2
[+] Signature: 58A5
[*] Parsing hex file: firmware.hex
[*] Found 1 memory block(s)
[*] Address range: 0x0000 - 0x3FFF
[*] Erasing flash...
[+] Flash erased successfully
[*] Programming block at 0x0000 (4096 bytes)... OK
[+] Programmed 4096 bytes successfully
[*] Verifying...
[+] Verification passed
[+] All done! Device programmed successfully
```

## Hardware Setup

### Required Connections
```
P89V51RD2 Pin    → USB Serial Adapter
=========================================
RXD (P3.0)       → TX
TXD (P3.1)       → RX
GND              → GND
+5V              → +5V (power)
RST (Pin 9)      → DTR (for automatic reset)
```

### DTR Connection Circuit
```
P89V51RD2 RST pin
    ↑
    │
   [10kΩ resistor]
    │
    ├─→ DTR signal from USB-Serial
    │
   [Optional: 100nF cap to GND]
    │
   GND
```

## Features

✅ **Automatic reset detection** (like FlashMagic)  
✅ **DTR/RTS control** for ISP mode entry  
✅ Hex file parsing (Intel HEX format)  
✅ Flash memory programming  
✅ Flash erase before programming  
✅ Device detection and signature reading  
✅ Optional verification after programming  
✅ Command-line interface  
✅ Works with standard USB-to-Serial adapters  

## Supported Devices

- P89V51RD2 ✓
- P89V51RB2 (experimental)
- P89V51RC2 (experimental)

## Command-Line Options

```bash
# Basic usage
python3 p89_flasher.py firmware.hex

# Specify serial port
python3 p89_flasher.py firmware.hex -p /dev/ttyUSB0

# Specify baud rate
python3 p89_flasher.py firmware.hex -b 19200

# Skip verification (faster)
python3 p89_flasher.py firmware.hex --no-verify

# Show help
python3 p89_flasher.py -h
```

## Troubleshooting

### "No reset detected within 5 seconds"

**Check 1: Device powered?**
- Make sure P89V51RD2 has power (3.3V or 5V)
- LED should be on if present

**Check 2: Try different reset method**
- Press RESET button (if available)
- Cycle power (disconnect/reconnect)
- Manually hold RST LOW and release

**Check 3: Serial connection OK?**
```bash
# Test port with minicom
minicom -D /dev/ttyUSB0 -b 9600
# Should show nothing, then Ctrl+A X to exit
```

**Check 4: Try different baud rate**
```bash
python3 p89_flasher.py firmware.hex -b 19200
python3 p89_flasher.py firmware.hex -b 38400
```

### "Failed to read device signature"

- Device not responding to ISP commands
- Bootloader may be damaged
- Check hex file format
- Verify power supply to device

### "Sync failed"

- DTR/RTS signals not reaching device properly
- USB adapter may not support DTR/RTS
- Check wiring: RST pin should be connected to DTR
- Try a different USB-to-Serial adapter

### No response in minicom

- Check RX/TX not crossed (TX→RX, RX→TX)
- Check GND connection
- Verify baud rate
- Device may not send data until reset

## Recommended USB-to-Serial Adapters

**Best (Full DTR/RTS support):**
- FT232RL (FTDI)
- CP2102 (Silicon Labs)
- CH340G (cheap & reliable)

**Avoid:**
- Counterfeit PL2303 (often no DTR/RTS)
- Very cheap no-name adapters (unreliable)

## Advanced Options

### Custom Baud Rates
```bash
# Try if default 9600 doesn't work
python3 p89_flasher.py firmware.hex -b 19200
python3 p89_flasher.py firmware.hex -b 38400
python3 p89_flasher.py firmware.hex -b 57600
```

### Batch Flashing Script
```bash
#!/bin/bash
for hexfile in *.hex; do
    echo "Flashing $hexfile..."
    python3 p89_flasher.py "$hexfile" -p /dev/ttyUSB0 || exit 1
done
```

### Create Alias
```bash
# Add to ~/.bashrc
alias flash_p89='python3 /path/to/p89_flasher.py'

# Usage: flash_p89 firmware.hex
```

## Comparison: FlashMagic vs This Tool

| Feature | FlashMagic | This Tool |
|---------|-----------|-----------|
| OS | Windows only | Linux/Windows/Mac |
| Reset Detection | ✓ | ✓ |
| DTR/RTS Control | ✓ | ✓ |
| User Experience | GUI | CLI |
| Speed | Medium | Medium |
| Verification | ✓ | ✓ |
| Cost | Free | Free |
| License | Proprietary | GPL-3.0 |

## Files Included

- `p89_flasher.py` - Main flashing tool
- `find_serial_port.py` - Serial port finder utility
- `README_FLASHING.md` - This documentation

## License

GNU General Public License v3.0

## References

- Philips P89V51RD2 Datasheet
- ISP Bootloader Protocol
- FlashMagic (original Windows tool)