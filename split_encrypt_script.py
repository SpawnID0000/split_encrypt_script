import os
import subprocess
import argparse
import zipfile
import shlex
import logging
import time
from pathlib import Path

# Initialize logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file = f"{script_name}_log.txt"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Start time for duration calculation
start_time = time.time()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Split and encrypt audio files. \n\nUsage: python3 split_encrypt_script.py path/to/Music path/to/output',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('input_dir', type=str, help='Path to the input directory')
parser.add_argument('output_dir', type=str, help='Path to the output directory')
args = parser.parse_args()

# Supported audio formats
audio_formats = ['.mp3', '.m4a', '.flac', '.opus']

# Function to copy directory structure
def copy_directory_structure(src, dest):
    for root, dirs, files in os.walk(src):
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            relative_path = os.path.relpath(dir_path, src)
            output_dir_path = os.path.join(dest, relative_path)
            os.makedirs(output_dir_path, exist_ok=True)

# Copying directory structure
print("Copying directory structure...")
copy_directory_structure(args.input_dir, args.output_dir)

# Process each file
print("Processing files...")
file_count = 0
for root, dirs, files in os.walk(args.input_dir):
    for file in files:
        if file.startswith('.') or file.lower() == 'folder.jpg':  # Skip hidden files and 'Folder.jpg'
            continue

        if any(file.endswith(ext) for ext in audio_formats):
            try:
                print(f"Processing audio file: {file}")
                file_path = os.path.join(root, file)
                output_root = os.path.relpath(root, args.input_dir)
                output_dir = os.path.join(args.output_dir, output_root)
                file_name_no_ext, file_ext = os.path.splitext(file)

                # Split file - Use shlex.quote() for safe shell execution
                file_name_part_ = os.path.join(output_dir, file_name_no_ext + "_part_")
                split_command = "split -b 475k {} {}".format(shlex.quote(file_path), shlex.quote(file_name_part_))
                subprocess.run(split_command, shell=True)

                # Encrypt file
                passphrase = file_name_no_ext  # Filename as passphrase
                gpg_path = "/usr/local/bin/gpg"  # Replace with your actual path to gpg

                encrypted_files_to_delete = []

                for part_file in os.listdir(output_dir):
                    if part_file.startswith(file_name_no_ext + "_part_"):
                        full_path = os.path.join(output_dir, part_file)
                        result = subprocess.run([gpg_path, "-c", "--cipher-algo", "AES256", "--batch", "--yes", "--passphrase", passphrase, full_path])

                        # If successful, store the encrypted file path
                        if result.returncode == 0:
                            encrypted_files_to_delete.append(full_path + '.gpg')

                # Create ZIP package for each audio file
                output_zip_path = os.path.join(output_dir, file_name_no_ext + '.zip')
                with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for encrypted_file in encrypted_files_to_delete:
                        zipf.write(encrypted_file, os.path.basename(encrypted_file))
                        os.remove(encrypted_file)  # Delete the encrypted file after adding to ZIP

                # Delete the original unencrypted split parts
                for part_file in os.listdir(output_dir):
                    if part_file.startswith(file_name_no_ext + "_part_") and not part_file.endswith('.gpg'):
                        os.remove(os.path.join(output_dir, part_file))

                print(f"Created ZIP package: {output_zip_path}")
                #logging.info(f"Processed file: {output_zip_path}")
                file_count += 1

            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")

# Calculate total duration
total_duration = time.time() - start_time

# Log total files processed and total duration
logging.info(f"Total files processed: {file_count}")
logging.info(f"Total script execution duration: {total_duration:.2f} seconds")

print("Processing complete!")
