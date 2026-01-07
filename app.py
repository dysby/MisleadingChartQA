import gradio as gr
import os
import pandas as pd
import json
from PIL import Image
from pathlib import Path

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(BASE_DIR, 'figures')
DATA_DIR = os.path.join(BASE_DIR, 'data')
QA_DIR = os.path.join(BASE_DIR, 'qa')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'screenshots', 'non-misleading')

def get_all_samples():
    """
    Scans the FIGURES_DIR to find all samples.
    Returns a list of sample identifiers (relative paths without extension).
    """
    samples = []
    figures_path = Path(FIGURES_DIR)
    
    for file_path in figures_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            rel_path = file_path.relative_to(figures_path)
            sample_id = str(rel_path.with_suffix(''))
            samples.append(sample_id)
            
    return sorted(samples)

def get_sample_data(sample_id):
    """
    Retrieves paths and content for a given sample_id.
    """
    # 1. Misleading Image
    misleading_path = None
    for ext in ['.jpeg', '.jpg', '.png']:
        p = os.path.join(FIGURES_DIR, sample_id + ext)
        if os.path.exists(p):
            misleading_path = p
            break
    
    # 2. Original Image (Screenshot)
    original_path = None
    possible_paths = [
        os.path.join(SCREENSHOTS_DIR, sample_id + '.jpg'),
        os.path.join(SCREENSHOTS_DIR, sample_id + '.jpeg'),
        os.path.join(SCREENSHOTS_DIR, sample_id + '.png'),
        os.path.join(SCREENSHOTS_DIR, 'code_original', sample_id + '.jpg'),
        os.path.join(SCREENSHOTS_DIR, 'code_original', sample_id + '.jpeg'),
        os.path.join(SCREENSHOTS_DIR, 'code_original', sample_id + '.png'),
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            original_path = p
            break

    # 3. CSV Data
    csv_path = os.path.join(DATA_DIR, sample_id + '.csv')
    df = None
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            df = pd.DataFrame({"Error": [f"Could not read CSV: {e}"]})
    else:
        df = pd.DataFrame({"Info": ["No CSV file found"]})

    # 4. JSON QA
    json_path = os.path.join(QA_DIR, sample_id + '.json')
    json_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
        except Exception as e:
            json_data = {"Error": f"Could not read JSON: {e}"}
    else:
        json_data = {"Info": "No JSON file found"}

    return misleading_path, original_path, df, json_data

# Initialize
samples = get_all_samples()

# # CSS to reduce size of JSON and limit image sizes if needed
# custom_css = """
# .json-holder {
#     height: 300px;
#     overflow-y: auto;
# }
# .table-holder {
#     height: 200px;
#     overflow-y: auto;
# }
# """

# with gr.Blocks(title="Misleading Chart QA Viewer", css=custom_css) as demo:
with gr.Blocks(title="Misleading Chart QA Viewer") as demo:
    gr.Markdown("# Misleading Chart QA Dataset Viewer")
    
    # State to keep track of current index
    current_index = gr.State(0)
    
    with gr.Row():
        prev_btn = gr.Button("Previous", scale=1)
        sample_dropdown = gr.Dropdown(choices=samples, value=samples[0] if samples else None, label="Select Sample", interactive=True, scale=4)
        count_display = gr.Textbox(label="Count", interactive=False, scale=1)
        next_btn = gr.Button("Next", scale=1)
    
    with gr.Row():
        # Left half: Images (side by side)
        with gr.Column(scale=1):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Misleading Image")
                    misleading_image = gr.Image(label="Misleading", type="pil", height=224)
                with gr.Column():
                    gr.Markdown("### Original Image (Screenshot)")
                    original_image = gr.Image(label="Original", type="pil", height=224)

        # Right half: Data Table
        with gr.Column(scale=1):
            gr.Markdown("### Data (CSV)")
            data_table = gr.DataFrame(label="CSV Data", elem_classes="table-holder")

    gr.Markdown("### QA (JSON)")
    json_output = gr.JSON(label="JSON Data", elem_classes="json-holder")


    def load_sample(index):
        if not samples:
            return None, None, pd.DataFrame(), {}, None, 0, "0/0"
        
        # Ensure index is within bounds
        idx = max(0, min(index, len(samples) - 1))
        sample_id = samples[idx]
        
        misleading_path, original_path, df, json_data = get_sample_data(sample_id)
        
        misleading_img = Image.open(misleading_path) if misleading_path else None
        original_img = Image.open(original_path) if original_path else None
        
        count_str = f"{idx + 1} / {len(samples)}"
        
        return misleading_img, original_img, df, json_data, sample_id, idx, count_str

    def on_prev(idx):
        return load_sample(idx - 1)
        
    def on_next(idx):
        return load_sample(idx + 1)
        
    def on_select(val):
        if val in samples:
            return load_sample(samples.index(val))
        return load_sample(0)

    # Event listeners
    prev_btn.click(
        fn=on_prev,
        inputs=[current_index],
        outputs=[misleading_image, original_image, data_table, json_output, sample_dropdown, current_index, count_display]
    )
    
    next_btn.click(
        fn=on_next,
        inputs=[current_index],
        outputs=[misleading_image, original_image, data_table, json_output, sample_dropdown, current_index, count_display]
    )

    sample_dropdown.select(
        fn=on_select,
        inputs=[sample_dropdown],
        outputs=[misleading_image, original_image, data_table, json_output, sample_dropdown, current_index, count_display]
    )
    
    # Load initial data
    demo.load(
        fn=load_sample,
        inputs=[current_index],
        outputs=[misleading_image, original_image, data_table, json_output, sample_dropdown, current_index, count_display]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
