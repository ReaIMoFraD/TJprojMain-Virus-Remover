"""
TJprojMain Virus Remover - A tool to detect and remove the TJprojMain.exe virus
that infects PE files and uses system resources for cryptocurrency mining.

Author: [Your Name]
GitHub: [Your GitHub URL]
License: MIT
Version: 1.0.0
"""

import os
import sys
import struct
import shutil
import datetime
import ctypes
import time
import json
from pathlib import Path
from typing import List, Tuple, Optional, Set
import win32api
from colorama import init, Fore, Style

init(autoreset=True)


class VirusScannerAndFixer:
    """Main class for scanning and removing TJprojMain virus from PE files."""
    
    # Virus signatures
    VIRUS_FILENAME = "tjprojmain.exe"
    MZ_SIGNATURE = b'MZ\x90\x00\x03'
    PE_SIGNATURE = b'PE\0\0'
    
    # Configuration
    BACKUP_FOLDER = r"C:\Virus_Backup"
    SCAN_DRIVES = ["C:\\", "E:\\", "F:\\"]
    SCAN_CHUNK_SIZE = 500  # Log progress every N files
    
    # Version info keys
    VERSION_INFO_KEY = '\\VarFileInfo\\Translation'
    ORIGINAL_FILENAME_KEY = '\\StringFileInfo\\{lang}\\OriginalFilename'
    
    def __init__(self):
        """Initialize the scanner with default settings."""
        self.found_files: List[str] = []
        self.found_files_set: Set[str] = set()
        self.scanned_count: int = 0
        self.fixed_files: List[str] = []
        self.failed_files: List[Tuple[str, str]] = []
        self.start_time: float = time.time()
        
        # Create backup directory if it doesn't exist
        Path(self.BACKUP_FOLDER).mkdir(parents=True, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_file = f"Virus_Fix_Report_{timestamp}.txt"
        
        # Initialize report
        self._write_header()
    
    def _write_header(self):
        """Write the report header with system information."""
        header = [
            "=" * 80,
            "TJprojMain Virus Scanner & Fixer Report",
            f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"System: {os.name} {sys.platform}",
            "=" * 80,
            ""
        ]
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header))
    
    def log(self, msg: str, level: str = "INFO"):
        """Log messages to both console and report file.
        
        Args:
            msg: Message to log
            level: Log level (INFO, WARNING, ERROR, SUCCESS, OK)
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Fore.CYAN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "SUCCESS": Fore.GREEN,
            "OK": Fore.GREEN,
            "FOUND": Fore.RED
        }
        
        color = colors.get(level, Fore.WHITE)
        line = f"[{timestamp}] [{level}] {msg}"
        
        # Print with color
        print(f"{color}{line}{Style.RESET_ALL}")
        
        # Write to file without colors
        with open(self.report_file, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    
    def add_to_found(self, filepath: str) -> bool:
        """Add a file to the found list if it's not a duplicate.
        
        Args:
            filepath: Path to the infected file
            
        Returns:
            True if added, False if duplicate
        """
        normalized_path = os.path.normpath(filepath)
        
        if normalized_path not in self.found_files_set:
            self.found_files_set.add(normalized_path)
            self.found_files.append(normalized_path)
            return True
        return False
    
    def get_file_version_info(self, filepath: str) -> Optional[str]:
        """Extract the OriginalFilename from version info.
        
        Args:
            filepath: Path to the executable file
            
        Returns:
            OriginalFilename string or None if not found
        """
        try:
            # Get translation info
            translation = win32api.GetFileVersionInfo(filepath, self.VERSION_INFO_KEY)
            if not translation:
                return None
            
            # Use first language/codepage
            lang = translation[0]
            lang_key = f'\\StringFileInfo\\{lang[0]:04x}{lang[1]:04x}'
            
            # Get OriginalFilename
            key = f'{lang_key}\\OriginalFilename'
            return win32api.GetFileVersionInfo(filepath, key)
            
        except Exception:
            return None
    
    def is_virus_file(self, filepath: str) -> bool:
        """Check if a file is infected with TJprojMain virus.
        
        Args:
            filepath: Path to the executable file
            
        Returns:
            True if infected, False otherwise
        """
        try:
            # Check filesize to avoid huge files
            if os.path.getsize(filepath) > 100 * 1024 * 1024:  # 100MB
                return False
            
            # Check version info
            orig_name = self.get_file_version_info(filepath)
            if orig_name and orig_name.lower() == self.VIRUS_FILENAME:
                return True
                
        except Exception:
            pass
        
        return False
    
    def scan_folder(self, folder_path: str) -> None:
        """Recursively scan a folder for infected files.
        
        Args:
            folder_path: Path to the folder to scan
        """
        try:
            for root, dirs, files in os.walk(folder_path):
                # Skip system folders to avoid permission issues
                skip_dirs = {'Windows', 'System32', 'System', 'WinSxS', '$Recycle.Bin'}
                if any(skip in root for skip in skip_dirs):
                    continue
                
                for file in files:
                    if not file.lower().endswith('.exe'):
                        continue
                    
                    filepath = os.path.join(root, file)
                    self.scanned_count += 1
                    
                    # Log progress
                    if self.scanned_count % self.SCAN_CHUNK_SIZE == 0:
                        self.log(f"Scanned: {self.scanned_count} files...", "INFO")
                    
                    if self.is_virus_file(filepath):
                        if self.add_to_found(filepath):
                            self.log(f"🚨 VIRUS FOUND: {filepath}", "FOUND")
                            self.log(f"   Original Filename: {self.VIRUS_FILENAME}", "INFO")
                        else:
                            self.log(f"ℹ️  Duplicate found (skipped): {filepath}", "INFO")
                            
        except PermissionError:
            # Skip folders without permission
            pass
        except Exception as e:
            self.log(f"Error scanning {folder_path}: {e}", "WARNING")
    
    def scan_drive(self, drive_path: str) -> None:
        """Scan an entire drive for infected files.
        
        Args:
            drive_path: Path to the drive (e.g., "C:\\")
        """
        self.log(f"🔍 Scanning drive: {drive_path}", "INFO")
        self.log("=" * 60, "INFO")
        
        if not os.path.exists(drive_path):
            self.log(f"❌ Drive {drive_path} does not exist!", "ERROR")
            return
        
        try:
            # Get all folders on the drive
            for item in os.listdir(drive_path):
                item_path = os.path.join(drive_path, item)
                if os.path.isdir(item_path):
                    self.log(f"📁 Scanning: {item_path}", "INFO")
                    self.scan_folder(item_path)
            
            # Scan root directory
            self.log(f"📁 Scanning: {drive_path} (root)", "INFO")
            self.scan_folder(drive_path)
            
        except Exception as e:
            self.log(f"Error scanning drive {drive_path}: {e}", "ERROR")
    
    def find_embedded_pe(self, data: bytes) -> List[int]:
        """Find all embedded PE files within binary data.
        
        Args:
            data: Binary data to search
            
        Returns:
            List of offset positions where PE files start
        """
        pe_offsets = []
        size = len(data)
        
        # Search for MZ signature
        for i in range(size - 5):
            if data[i:i+5] == self.MZ_SIGNATURE:
                # Verify it's a valid PE header
                if i != 0 and self._is_valid_pe(data, i):
                    pe_offsets.append(i)
        
        return pe_offsets
    
    def _is_valid_pe(self, data: bytes, offset: int) -> bool:
        """Check if a valid PE header exists at the given offset.
        
        Args:
            data: Binary data
            offset: Offset to check
            
        Returns:
            True if valid PE header found
        """
        try:
            # Check MZ signature
            if data[offset:offset+2] != b'MZ':
                return False
            
            # Get PE header offset
            e_lfanew = struct.unpack('<I', data[offset+0x3C:offset+0x40])[0]
            pe_offset = offset + e_lfanew
            
            # Check PE signature
            if data[pe_offset:pe_offset+4] != self.PE_SIGNATURE:
                return False
                
            return True
            
        except Exception:
            return False
    
    def extract_pe(self, data: bytes, offset: int, output_path: str) -> bool:
        """Extract PE file from binary data at the given offset.
        
        Args:
            data: Binary data containing the PE
            offset: Offset where PE starts
            output_path: Path to save the extracted PE
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the next MZ signature to determine the end
            end_offset = len(data)
            next_mz = data.find(self.MZ_SIGNATURE, offset + 1)
            if next_mz != -1:
                end_offset = next_mz
            
            # Extract PE data
            pe_data = data[offset:end_offset]
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(pe_data)
                
            return True
            
        except Exception:
            return False
    
    def fix_file(self, virus_file: str) -> bool:
        """Fix one infected file by extracting and replacing with clean PE.
        
        Args:
            virus_file: Path to the infected file
            
        Returns:
            True if fixed successfully, False otherwise
        """
        self.log(f"🔧 Fixing: {os.path.basename(virus_file)}", "INFO")
        
        # 1. Read the infected file
        try:
            with open(virus_file, 'rb') as f:
                data = f.read()
        except Exception as e:
            self.log(f"Failed to read file: {e}", "ERROR")
            self.failed_files.append((virus_file, "Read Error"))
            return False
        
        # 2. Find embedded PE files
        offsets = self.find_embedded_pe(data)
        if not offsets:
            self.log("No embedded PE found!", "WARNING")
            self.failed_files.append((virus_file, "No PE found"))
            return False
        
        self.log(f"Found {len(offsets)} embedded PE(s)", "OK")
        
        # 3. Create backup
        backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(virus_file)}"
        backup_path = os.path.join(self.BACKUP_FOLDER, backup_name)
        
        try:
            shutil.copy2(virus_file, backup_path)
            self.log(f"Backup created: {backup_path}", "OK")
        except Exception as e:
            self.log(f"Backup failed: {e}", "WARNING")
        
        # 4. Extract first PE and replace original
        temp_file = virus_file + ".tmp"
        
        if self.extract_pe(data, offsets[0], temp_file):
            try:
                # Replace original with extracted PE
                os.remove(virus_file)
                os.rename(temp_file, virus_file)
                self.log(f"✅ Fixed successfully!", "SUCCESS")
                self.fixed_files.append(virus_file)
                return True
                
            except Exception as e:
                self.log(f"Replace failed: {e}", "ERROR")
                self.failed_files.append((virus_file, str(e)))
                
                # Clean up temp file if it exists
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return False
        else:
            self.log("Extract failed", "ERROR")
            self.failed_files.append((virus_file, "Extract failed"))
            return False
    
    def fix_all_files(self) -> None:
        """Fix all detected infected files."""
        if not self.found_files:
            self.log("No virus files to fix!", "INFO")
            return
        
        self.log(f"\n🔧 Fixing {len(self.found_files)} files...", "INFO")
        self.log("=" * 60, "INFO")
        
        success_count = 0
        for i, filepath in enumerate(self.found_files, 1):
            self.log(f"\n[{i}/{len(self.found_files)}]", "INFO")
            if self.fix_file(filepath):
                success_count += 1
        
        # Generate final report
        self._generate_final_report(success_count)
    
    def _generate_final_report(self, success_count: int) -> None:
        """Generate the final report after fixing.
        
        Args:
            success_count: Number of successfully fixed files
        """
        elapsed_time = time.time() - self.start_time
        
        report = [
            "\n" + "=" * 60,
            "FINAL REPORT",
            "=" * 60,
            f"✅ Successfully fixed: {success_count}",
            f"❌ Failed: {len(self.found_files) - success_count}",
            f"📊 Total scanned: {self.scanned_count}",
            f"🕐 Time elapsed: {elapsed_time:.2f} seconds",
            f"💾 Backup folder: {self.BACKUP_FOLDER}",
            f"📄 Report file: {self.report_file}",
            ""
        ]
        
        if self.failed_files:
            report.append("FAILED FILES:")
            for filepath, error in self.failed_files:
                report.append(f"  ❌ {filepath} - {error}")
        
        report.append("=" * 60)
        
        for line in report:
            if line.startswith("✅") or line.startswith("Successfully"):
                self.log(line, "SUCCESS")
            elif line.startswith("❌") or line.startswith("Failed"):
                self.log(line, "ERROR")
            else:
                self.log(line, "INFO")
    
    def scan_and_fix(self) -> None:
        """Main method to scan and optionally fix infected files."""
        # Scan all drives
        for drive in self.SCAN_DRIVES:
            self.scan_drive(drive)
            self.log("-" * 60, "INFO")
        
        # Display scan results
        self.log("=" * 60, "INFO")
        self.log(f"📊 Scan Results:", "INFO")
        self.log(f"  • Total EXE files scanned: {self.scanned_count}", "INFO")
        self.log(f"  • Unique infected files found: {len(self.found_files)}", "INFO")
        self.log("=" * 60, "INFO")
        
        if self.found_files:
            self.log("\n🚨 List of infected files:", "FOUND")
            for i, filepath in enumerate(self.found_files, 1):
                self.log(f"  {i}. {filepath}", "INFO")
            
            # Ask user for fix confirmation
            self.log("\n" + "=" * 60, "INFO")
            response = input(f"{Fore.YELLOW}Do you want to fix these infected files? (y/n): ")
            
            if response.lower() == 'y':
                self.fix_all_files()
            else:
                self.log("Fix operation cancelled.", "WARNING")
        else:
            self.log("\n✅ Congratulations! No infected files found!", "SUCCESS")
        
        self.log("\n" + "=" * 60, "INFO")
        self.log("✅ Operation completed!", "SUCCESS")
        input("\nPress Enter to exit...")


def check_admin() -> bool:
    """Check if the program is running with administrator privileges.
    
    Returns:
        True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def main() -> None:
    """Main entry point of the program."""
    print("=" * 80)
    print(f"{Fore.CYAN}🛡️  TJprojMain Virus Scanner & Fixer")
    print(f"{Fore.YELLOW}Version 1.0.0")
    print(f"{Fore.YELLOW}Full scan of Drives C, E, and F")
    print("=" * 80)
    
    # Check for administrator privileges
    if not check_admin():
        print(f"{Fore.RED}⚠️  Please run this program with Administrator privileges!")
        print(f"{Fore.RED}   Right-click and select 'Run as administrator'")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    try:
        scanner = VirusScannerAndFixer()
        scanner.scan_and_fix()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()