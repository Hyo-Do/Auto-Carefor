import json
import os


def merge_file():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(current_directory, 'output')
    json_files = [f for f in os.listdir(output_directory) if f.startswith('output_') and f.endswith('.json')]

    all_data = []
    for file in json_files:
        with open(os.path.join(output_directory, file), 'rt', encoding="utf8") as f:
            file_data = json.load(f)
            all_data.append(file_data)

    output_file_path = os.path.join(output_directory, 'combined_output.json')
    with open(output_file_path, 'w', encoding="utf8") as f:
        json.dump(all_data, f, ensure_ascii=False)
    
    
if __name__ == "__main__":
    merge_file()
