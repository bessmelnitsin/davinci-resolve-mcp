
from gradio_client import Client, handle_file
import os

def debug_transcribe():
    file_path = r"A:\010101\test\A001_08071102_C026.mov"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    client = Client("http://127.0.0.1:7860", verbose=False)
    
    inputs = [
        # [0] Upload File
        handle_file(file_path),
        # [1] Input Folder Path
        "",
        # [2] Include Subdirectory Files
        False,
        # [3] Save outputs at same directory
        False,
        # [4] File Format
        "SRT",
        # [5] Add timestamp to filename
        False,
        # [6] Model
        "base",
        # [7] Language
        "Automatic Detection",
        # [8] Translate to English
        False,
        # [9] Beam Size
        5,
        # [10] Log Probability Threshold
        -1.0,
        # [11] No Speech Threshold
        0.6,
        # [12] Compute Type
        "int8",
        # [13] Best Of
        5,
        # [14] Patience
        1.0,
        # [15] Condition On Previous Text
        True,
        # [16] Prompt Reset On Temperature
        0.1,
        # [17] Initial Prompt
        None,
        # [18] Temperature
        0,
        # [19] Compression Ratio Threshold
        2.4,
        # [20] Length Penalty
        1.0,
        # [21] Repetition Penalty
        1.0,
        # [22] No Repeat N-gram Size
        0,
        # [23] Prefix
        None,
        # [24] Suppress Blank
        True,
        # [25] Suppress Tokens
        "-1",
        # [26] Max Initial Timestamp
        1.0,
        # [27] Word Timestamps
        True,
        # [28] Prepend Punctuations
        "\"'“¿([{-",
        # [29] Append Punctuations
        "\"'.。,，!！?？:：”)]}、",
        # [30] Max New Tokens
        None,
        # [31] Chunk Length (s)
        30,
        # [32] Hallucination Silence Threshold (sec)
        None,
        # [33] Hotwords
        None,
        # [34] Language Detection Threshold
        0.5,
        # [35] Language Detection Segments
        1,
        # [36] Batch Size
        16,
        # [37] Offload sub model when finished
        False,
        # [38] Enable Silero VAD Filter
        True,
        # [39] Speech Threshold
        0.6,
        # [40] Minimum Speech Duration (ms)
        250,
        # [41] Maximum Speech Duration (s)
        0,
        # [42] Minimum Silence Duration (ms)
        2000,
        # [43] Speech Padding (ms)
        400,
        # [44] Enable Diarization
        False,
        # [45] Device
        "cuda",
        # [46] HuggingFace Token
        "",
        # [47] Offload sub model when finished (duplicate in UI?)
        False,
        # [48] Enable Background Music Remover Filter
        False,
        # [49] Model (UVR)
        "UVR-MDX-NET-Inst_HQ_4",
        # [50] Device (UVR)
        "cuda",
        # [51] Segment Size
        256,
        # [52] Save separated files to output
        False,
        # [53] Offload sub model when finished (UVR)
        False
    ]

    print("Inputs prepared. Calling predict...")
    try:
        # Debug: print input types
        # for i, inp in enumerate(inputs):
        #    print(f"{i}: {inp} ({type(inp)})")
            
        result = client.predict(
            *inputs,
            api_name="/transcribe_file"
        )
        print("Success!")
        print(result)
    except Exception as e:
        print("Failed!")
        print(e)

if __name__ == "__main__":
    debug_transcribe()
