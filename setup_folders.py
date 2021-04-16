from pathlib import Path

def setup_folders():
    folder_names = ["csv's", "csv's/monitors", "csv's/reports", "csv's/trades", "csv's/watches", "logs", "tokens"]

    for folder in folder_names:
        _file = Path(f'./{folder}')
        if _file.exists():
            pass
        else:
            Path.touch(f'./{folder}')
