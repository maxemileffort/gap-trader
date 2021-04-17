from pathlib import Path
import os

def setup_folders():
    folder_names = ["csv's", "csv's/monitors", "csv's/reports", "csv's/trades", "csv's/watches", "logs", "tokens"]

    for folder in folder_names:
        _file = Path(f'./{folder}')
        if _file.exists():
            pass
        else:
            os.mkdir(f'./{folder}')

if __name__ == "__main__":
    setup_folders()
