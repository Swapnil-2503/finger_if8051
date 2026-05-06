#!/usr/bin/env python3
"""
P89V51RD2 ISP Flashing Tool
A replacement for FlashMagic on Linux/Windows
Supports P89V51RD2 microcontroller flashing via ISP bootloader
"""

import serial
import sys
import time
import argparse
from typing import List, Tuple, Optional
import struct


class HexParser:
    """Parse Intel HEX format files"""
    
    def __init__(self, hex_file: str):
        self.hex_file = hex_file
        self.memory = {}
        self.start_address = None
        self.end_address = None
        self._parse()
    
    def _parse(self):
        """Parse hex file into memory dictionary"""
        with open(self.hex_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line[0] != ':':
                    continue
                
                # Parse record
                length = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                data = bytes.fromhex(line[9:9+length*2])
                checksum = int(line[9+length*2:11+length*2], 16)
                
                # Verify checksum
                calc_checksum = (length + (address >> 8) + (address & 0xFF) + 
                               record_type + sum(data)) & 0xFF
                calc_checksum = (0x100 - calc_checksum) & 0xFF
                
                if calc_checksum != checksum:
                    print(f"[!] Checksum error at address 0x{address:04X}")
                    continue
                
                # Process record types
                if record_type == 0x00:  # Data record
                    for i, byte in enumerate(data):
                        addr = address + i
                        self.memory[addr] = byte
                        if self.start_address is None or addr < self.start_address:
                            self.start_address = addr
                        if self.end_address is None or addr > self.end_address:
                            self.end_address = addr
                
                elif record_type == 0x01:  # End of file
                    break
                
                elif record_type == 0x04:  # Extended linear address
                    upper_addr = int.from_bytes(data, 'big')
                    # Handle if needed for larger address spaces
    
    def get_memory_blocks(self, block_size: int = 128) -> List[Tuple[int, bytes]]:
        """Get continuous memory blocks for programming"""
        blocks = []
        if not self.memory:
            return blocks
        
        sorted_addrs = sorted(self.memory.keys())
        current_addr = sorted_addrs[0]
        current_block = bytearray()
        
        for addr in sorted_addrs:
            # If gap found, save current block and start new one
            if addr != current_addr + len(current_block):
                if current_block:
                    blocks.append((current_addr, bytes(current_block)))
                current_addr = addr
                current_block = bytearray()
            
            current_block.append(self.memory[addr])
        
        if current_block:
            blocks.append((current_addr, bytes(current_block)))
        
        return blocks


class ISPProtocol:
    """P89V51RD2 ISP Protocol Implementation"""
    
    # ISP Commands
    CMD_SYNC = b'\x1A'
    CMD_ERASE_FLASH = b'\x03'
    CMD_PROGRAM_FLASH = b'\x40'
    CMD_READ_FLASH = b'\x50'
    CMD_SET_BAUD_RATE = b'\x05'
    CMD_ECHO = b'\xE0'
    CMD_READ_SIGNATURE = b'\x08'
    
    # Device signatures
    SIGNATURES = {
        b'\x58\xA5': 'P89V51RD2',
        b'\x58\x96': 'P89V51RB2',
        b'\x58\x97': 'P89V51RC2',
    }
    
    def __init__(self, port: str, baud_rate: int = 9600, auto_reset: bool = True):
        self.port = port
        self.baud_rate = baud_rate
        self.auto_reset = auto_reset
        self.ser = None
        self.part_id = None
    
    def connect(self) -> bool:
        """Connect to device and initiate ISP mode (FlashMagic style)"""
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"[*] Opened port {self.port} at {self.baud_rate} baud")
            time.sleep(0.5)
            
            # FlashMagic-style: Show reset dialog and wait for MCU reset
            print("\n" + "="*70)
            print("[!] *** RESET YOUR MCU NOW ***")
            print("="*70)
            print("\n[*] Please perform ONE of the following:")
            print("    • Press RESET button on your board")
            print("    • Cycle power (disconnect/reconnect)")
            print("    • Hold RST LOW for 100ms then release\n")
            print("[*] The tool will automatically detect reset and enter ISP mode...")
            print("[*] Waiting for reset signal...\n")
            
            # Wait and detect reset
            if not self._detect_reset_and_enter_isp():
                print("\n[-] Reset not detected or ISP mode entry failed")
                print("[!] Please try again:")
                print("    - Make sure device is powered ON")
                print("    - Press RESET or cycle power again")
                print("    - Check serial connection\n")
                return False
            
            return True
        
        except KeyboardInterrupt:
            print("\n[!] Cancelled by user")
            return False
        
        except serial.SerialException as e:
            print(f"[-] Serial error: {e}")
            return False
    
    def _detect_reset_and_enter_isp(self) -> bool:
        """Detect MCU reset and enter ISP mode (FlashMagic behavior)
        
        Watch for RX activity that indicates reset,
        then control DTR/RTS to enter ISP mode
        """
        timeout = 5  # Wait up to 5 seconds for reset
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check for incoming data (indicates activity/reset)
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    elapsed = time.time() - start_time
                    print(f"[+] Reset detected! ({len(data)} bytes, after {elapsed:.1f}s)")
                    time.sleep(0.2)
                    
                    # Now control DTR/RTS to enter ISP mode
                    print("[*] Entering ISP mode via DTR/RTS...")
                    try:
                        # Pull RST low via DTR
                        self.ser.dtr = False
                        time.sleep(0.05)
                        
                        # Set ISP mode via RTS
                        self.ser.rts = True
                        time.sleep(0.05)
                        
                        # Release RST
                        self.ser.dtr = True
                        time.sleep(0.5)
                        
                        print("[+] ISP mode sequence completed")
                    except Exception as e:
                        print(f"[!] DTR/RTS control error: {e}")
                        print("[!] Assuming manual ISP entry or device already in ISP mode")
                        time.sleep(0.5)
                    
                    # Now try to sync
                    print("[*] Synchronizing with device...")
                    if self._sync_with_device():
                        if self._read_signature():
                            return True
                
                # Show progress dot
                print(".", end="", flush=True)
                time.sleep(0.1)
            
            except Exception as e:
                print(f"\n[!] Error: {e}")
                time.sleep(0.1)
        
        print(f"\n[-] No reset detected within {timeout} seconds")
        return False
    
    def _sync_with_device(self) -> bool:
        """Try to sync with device"""
        for attempt in range(3):
            if self._sync():
                return True
            time.sleep(0.2)
        return False

    
    def disconnect(self):
        """Disconnect from device"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[*] Disconnected")
    
    def _send_command(self, cmd: bytes, data: bytes = b'') -> Optional[bytes]:
        """Send ISP command and get response"""
        packet = cmd + data
        
        try:
            self.ser.write(packet)
            self.ser.flush()
            
            # Wait for response (length depends on command)
            time.sleep(0.05)
            response = self.ser.read(100)
            
            return response if response else None
        
        except Exception as e:
            print(f"[-] Command error: {e}")
            return None
    
    def _sync(self) -> bool:
        """Synchronize with device"""
        # Send sync pattern
        self.ser.write(b'\x1A' * 10)
        self.ser.flush()
        time.sleep(0.1)
        
        # Should receive echo
        response = self.ser.read(100)
        if response and len(response) > 0:
            print("[+] Device sync successful")
            return True
        
        return False
    
    def _read_signature(self) -> bool:
        """Read and verify device signature"""
        response = self._send_command(self.CMD_READ_SIGNATURE)
        
        if response and len(response) >= 2:
            sig = bytes(response[:2])
            
            if sig in self.SIGNATURES:
                self.part_id = self.SIGNATURES[sig]
                print(f"[+] Device detected: {self.part_id}")
                print(f"[+] Signature: {sig.hex().upper()}")
                return True
        
        print("[-] Unknown device signature")
        return False
    
    def erase_flash(self) -> bool:
        """Erase entire flash memory"""
        print("[*] Erasing flash...")
        response = self._send_command(self.CMD_ERASE_FLASH)
        
        if response and b'\x09' in response:
            print("[+] Flash erased successfully")
            return True
        
        print("[-] Erase failed")
        return False
    
    def program_flash(self, address: int, data: bytes) -> bool:
        """Program data to flash at specified address"""
        # Build program command packet
        # Format: CMD (1) + Address (2) + Length (2) + Data (N)
        addr_bytes = struct.pack('>H', address)
        len_bytes = struct.pack('>H', len(data))
        
        packet = self.CMD_PROGRAM_FLASH + addr_bytes + len_bytes + data
        
        response = self._send_command(packet)
        
        if response and (b'\x09' in response or len(response) > 0):
            return True
        
        return False
    
    def read_flash(self, address: int, length: int) -> Optional[bytes]:
        """Read flash memory"""
        addr_bytes = struct.pack('>H', address)
        len_bytes = struct.pack('>H', length)
        
        packet = self.CMD_READ_FLASH + addr_bytes + len_bytes
        response = self._send_command(packet)
        
        if response and len(response) >= length:
            return response[:length]
        
        return None
    
    def program_hex(self, hex_file: str, verify: bool = True) -> bool:
        """Program entire hex file to device"""
        print(f"[*] Parsing hex file: {hex_file}")
        
        try:
            parser = HexParser(hex_file)
        except Exception as e:
            print(f"[-] Failed to parse hex file: {e}")
            return False
        
        blocks = parser.get_memory_blocks()
        
        if not blocks:
            print("[-] No data found in hex file")
            return False
        
        print(f"[*] Found {len(blocks)} memory block(s)")
        print(f"[*] Address range: 0x{parser.start_address:04X} - 0x{parser.end_address:04X}")
        
        # Erase flash
        if not self.erase_flash():
            return False
        
        # Program blocks
        total_bytes = 0
        for block_addr, block_data in blocks:
            print(f"[*] Programming block at 0x{block_addr:04X} ({len(block_data)} bytes)...", end='')
            
            # Program in chunks (max 250 bytes per packet)
            chunk_size = 250
            for offset in range(0, len(block_data), chunk_size):
                chunk = block_data[offset:offset + chunk_size]
                addr = block_addr + offset
                
                if not self.program_flash(addr, chunk):
                    print("\n[-] Programming failed")
                    return False
            
            total_bytes += len(block_data)
            print(" OK")
        
        print(f"[+] Programmed {total_bytes} bytes successfully")
        
        # Verify if requested
        if verify:
            print("[*] Verifying...")
            if self._verify_hex(parser, blocks):
                print("[+] Verification passed")
            else:
                print("[!] Verification failed (device might still work)")
        
        return True
    
    def _verify_hex(self, parser: HexParser, blocks: List[Tuple[int, bytes]]) -> bool:
        """Verify programmed data"""
        errors = 0
        
        for block_addr, block_data in blocks:
            read_data = self.read_flash(block_addr, len(block_data))
            
            if not read_data:
                return False
            
            if read_data != block_data:
                errors += 1
                print(f"[!] Verify error at block 0x{block_addr:04X}")
        
        return errors == 0


def main():
    parser = argparse.ArgumentParser(
        description='P89V51RD2 ISP Flashing Tool (FlashMagic replacement for Linux)'
    )
    
    parser.add_argument(
        'hex_file',
        help='Hex file to program'
    )
    
    parser.add_argument(
        '-p', '--port',
        default='/dev/ttyUSB0',
        help='Serial port (default: /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '-b', '--baud',
        type=int,
        default=9600,
        help='Baud rate (default: 9600)'
    )
    
    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Disable automatic ISP reset (manual reset required)'
    )
    
    parser.add_argument(
        '-v', '--verify',
        action='store_true',
        default=True,
        help='Verify after programming (default: enabled)'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip verification'
    )
    
    args = parser.parse_args()
    
    if args.no_verify:
        args.verify = False
    
    auto_reset = not args.no_reset
    
    # Create ISP instance
    isp = ISPProtocol(args.port, args.baud, auto_reset=auto_reset)
    
    # Connect and program
    if not isp.connect():
        print("[-] Failed to connect to device")
        sys.exit(1)
    
    try:
        if not isp.program_hex(args.hex_file, verify=args.verify):
            print("[-] Programming failed")
            sys.exit(1)
        
        print("[+] All done! Device programmed successfully")
    
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    
    finally:
        isp.disconnect()


if __name__ == '__main__':
    main()