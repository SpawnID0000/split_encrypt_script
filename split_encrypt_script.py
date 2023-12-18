import os
import subprocess
import argparse
import zipfile
import shlex
import logging
import time
from multiprocessing import Pool
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from pathlib import Path

# AES encryption function
def aes_encrypt(input_data, passphrase):
    backend = default_backend()
    key = passphrase.ljust(32)[:32].encode()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=backend)
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(input_data) + padder.finalize()

    return iv + encryptor.update(padded_data) + encryptor.finalize()

# Function to process a single file
def process_file(file_info):
    input_dir, output_dir, file = file_info
    file_path = os.path.join(input_dir, file)
    file_name_no_ext, file_ext = os.path.splitext(file)

    if file.startswith('.') or file.lower() == 'folder.jpg':
        return f"Skipped file: {file}"

    try:
        file_name_part_ = os.path.join(output_dir, file_name_no_ext + "_part_")
        split_command = f"split -b 475k {shlex.quote(file_path)} {shlex.quote(file_name_part_)}"
        subprocess.run(split_command, shell=True)

        for part_file in os.listdir(output_dir):
            if part_file.startswith(file_name_no_ext + "_part_"):
                full_path = os.path.join(output_dir, part_file)
                with open(full_path, 'rb') as f:
                    file_data = f.read()
                encrypted_data = aes_encrypt(file_data, file_name_no_ext + file_ext)
                encrypted_file_name = f"{part_file}{file_ext}.aes"
                with open(os.path.join(output_dir, encrypted_file_name), 'wb') as f:
                    f.write(encrypted_data)
                os.remove(full_path)

        output_zip_path = os.path.join(output_dir, file_name_no_ext + '.zip')
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for aes_file in os.listdir(output_dir):
                if aes_file.startswith(file_name_no_ext + "_part_") and aes_file.endswith('.aes'):
                    zipf.write(os.path.join(output_dir, aes_file), aes_file)
                    os.remove(os.path.join(output_dir, aes_file))

        print(f"Finished processing: {file}")

        return f"Processed file: {output_zip_path}"

    except Exception as e:
        return f"Error processing file {file}: {e}"

def main():
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_file = f"{script_name}_log.txt"
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    start_time = time.time()

    parser = argparse.ArgumentParser(description='Split and encrypt audio files. \n\nUsage: python3 split_encrypt_script.py path/to/Music path/to/output',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('input_dir', type=str, help='Path to the input directory')
    parser.add_argument('output_dir', type=str, help='Path to the output directory')
    args = parser.parse_args()

    print("Copying directory structure...")
    copy_directory_structure(args.input_dir, args.output_dir)

    files_to_process = []
    for root, dirs, files in os.walk(args.input_dir):
        for file in files:
            if file.startswith('.') or file.lower() == 'folder.jpg' or not any(file.endswith(ext) for ext in ['.mp3', '.m4a', '.flac', '.opus']):
                continue
            files_to_process.append((root, os.path.join(args.output_dir, os.path.relpath(root, args.input_dir)), file))

    print("Processing files...")
    with Pool() as pool:
        results = pool.map(process_file, files_to_process)

    for result in results:
        if "Error" in result:
            logging.error(result)
        else:
            # Uncomment the below line if detailed logging for each file is needed.
            # logging.info(result)
            print(result)

    total_duration = time.time() - start_time
    logging.info(f"Total script execution duration: {total_duration:.2f} seconds")
    print("Processing complete!")

def copy_directory_structure(src, dest):
    for root, dirs, files in os.walk(src):
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            relative_path = os.path.relpath(dir_path, src)
            output_dir_path = os.path.join(dest, relative_path)
            os.makedirs(output_dir_path, exist_ok=True)

if __name__ == "__main__":
    main()
