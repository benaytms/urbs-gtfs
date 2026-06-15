import hashlib
import os

ZIP_FILE=r'../../output/gtfs_curitiba.zip'
HASH_FILE=r'../../output/last_hash.txt'

def compute_file_hash(algorithm='sha256'):
    hash_func = hashlib.new(algorithm)

    if os.path.exists(ZIP_FILE):
        with open(ZIP_FILE, 'rb') as zfile:
            while chunk := zfile.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

def diff_check() -> bool:
    new_hash = compute_file_hash()
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as hfile:
            old_hash = hfile.read().strip()
        if old_hash == new_hash:
            print("No changes detected, skipping...")
            return False
            
    with open(HASH_FILE, 'w') as hfile:
        hfile.write(new_hash)
    print("Changes detected, publishing...")
    return True


if __name__ == '__main__':
    diff_check()