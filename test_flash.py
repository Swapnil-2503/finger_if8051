#!/usr/bin/env python3
"""
Serial Port Finder and Tester
Helps identify and test serial connections to P89V51RD2 devices
"""

import serial
import serial.tools.list_ports
import sys
import time
import argparse


def list_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("[-] No serial ports found")
        return []
    
    print("[*] Available serial ports:")
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port.device}")
        print(f"     Description: {port.description}")
        print(f"     Manufacturer: {port.manufacturer or 'Unknown'}")
        print()
    
    return ports


def test_port(port_name: str, baud_rate: int = 9600):
    """Test basic connectivity on serial port"""
    print(f"[*] Testing port {port_name} at {baud_rate} baud...")
    
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=2)
        print(f"[+] Successfully opened {port_name}")
        
        # Try to send sync pattern (like ISP)
        print("[*] Sending ISP sync pattern...")
        ser.write(b'\x1A' * 10)
        ser.flush()
        
        time.sleep(0.2)
        
        # Try to read response
        response = ser.read(100)
        
        if response:
            print(f"[+] Received response ({len(response)} bytes):")
            print(f"    Hex: {response.hex().upper()}")
            print("[+] Device may be responding!")
            return True
        else:
            print("[-] No response (device might not be in ISP mode)")
            print("    Try holding RST low and reapply power")
            return False
    
    except serial.SerialException as e:
        print(f"[-] Failed to open port: {e}")
        return False
    
    except Exception as e:
        print(f"[-] Error: {e}")
        return False
    
    finally:
        try:
            ser.close()
        except:
            pass


def test_all_ports(baud_rates: list = None):
    """Test all ports at various baud rates"""
    if baud_rates is None:
        baud_rates = [9600, 19200, 38400, 57600]
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("[-] No serial ports found")
        return
    
    print(f"[*] Testing {len(ports)} port(s) at {len(baud_rates)} baud rate(s)...\n")
    
    for port in ports:
        print(f"[*] Port: {port.device} ({port.description})")
        
        for baud in baud_rates:
            if test_port(port.device, baud):
                print(f"[+] Success at {baud} baud!\n")
                return port.device
            
            print()
    
    print("[-] No device detected on any port")
    return None


def interactive_test():
    """Interactive port testing"""
    ports = list_ports()
    
    if not ports:
        return
    
    try:
        choice = int(input("\n[?] Select port number (0 to skip): "))
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(ports):
            port = ports[choice - 1].device
            baud = input("[?] Enter baud rate (default 9600): ").strip()
            baud = int(baud) if baud else 9600
            
            test_port(port, baud)
        else:
            print("[-] Invalid selection")
    
    except ValueError:
        print("[-] Invalid input")
    except KeyboardInterrupt:
        print("\n[!] Interrupted")


def main():
    parser = argparse.ArgumentParser(
        description='Serial Port Finder and Tester for P89V51RD2'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available serial ports'
    )
    
    parser.add_argument(
        '-t', '--test',
        metavar='PORT',
        help='Test specific port (e.g., /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '-b', '--baud',
        type=int,
        default=9600,
        help='Baud rate for testing (default: 9600)'
    )
    
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Test all ports at various baud rates'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.list, args.test, args.all, args.interactive]):
        parser.print_help()
        print("\n[*] No options specified. Running in interactive mode...\n")
        interactive_test()
        return
    
    if args.list:
        list_ports()
    
    if args.test:
        test_port(args.test, args.baud)
    
    if args.all:
        test_all_ports()
    
    if args.interactive:
        interactive_test()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(0)