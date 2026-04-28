import pandas as pd
import json
import os
from glob import glob

SOURCE=r'../source/'

def json_2_csv() -> None:
    original_files = glob(pathname= SOURCE + '*.json')
    fnames=[f.replace(SOURCE, '').split('.')[0] for f in original_files]
    
    for name in fnames:
        input_path = f"{SOURCE}{name}.json"
        output_path = f"{SOURCE}{name}.csv"
        
        try:
            df = pd.read_json(input_path)
        except ValueError:
            df = pd.read_json(input_path, lines=True)
    
        df.to_csv(output_path, index=False)
        print(f"Saved {output_path}")

def main()->None:
    json_2_csv()


if __name__ == "__main__":
    main()