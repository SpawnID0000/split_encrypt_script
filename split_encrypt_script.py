import os
import subprocess


# Input file for splitting & encrypting

file_name_no_ext = "ba7be4d0-e73f-4ecc-94d9-6658b510c69b_7c0ecbde-84d4-48c7-8cf4-77cecce423af"  # Replace with actual file name (artistMBID_recordingMBID)
file_name_ext = ".mp3"                                                                          # Replace with actual file extension
file_name = file_name_no_ext + file_name_ext
file_path = os.path.join(os.getcwd(), file_name)


# Split file

file_name_part_ = file_name + "_part_"
subprocess.run(["split", "-b", "475k", file_path, file_name_part_])


# Encrypt file

directory = os.path.dirname(file_path)

passphrase = file_name_no_ext  # Use artistMBID_recordingMBID as passphrase (for unprotected files only!)

for file in os.listdir(directory):
    if file.startswith(os.path.basename(file_name_part_)):  # Check if the file starts with the split file name pattern
        full_path = os.path.join(directory, file)
        gpg_path = "/usr/local/bin/gpg"  # Replace with your actual path to gpg
        os.environ["PATH"] += os.pathsep + "/usr/local/bin"

        result = subprocess.run([gpg_path, "-c", "--cipher-algo", "AES256", "--batch", "--yes", "--passphrase", passphrase, full_path])


        # If the encryption was successful, delete the unencrypted file chunk
        if result.returncode == 0:
            os.remove(full_path)
        else:
            print(f"Failed to encrypt {full_path}. Skipping deletion.")