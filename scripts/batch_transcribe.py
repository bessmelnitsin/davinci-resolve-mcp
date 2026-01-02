import os
import sys
import argparse
import logging
import json
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {'.mov', '.mp4', '.mkv', '.avi', '.m4v', '.webm'}

def load_nvidia_libs():
    """Load NVIDIA DLLs for Windows"""
    if sys.platform.startswith("win"):
        try:
            import nvidia.cudnn
            import nvidia.cublas
            
            for lib in [nvidia.cudnn, nvidia.cublas]:
                paths = getattr(lib, "__path__", [])
                for p in paths:
                    possible_paths = [p, os.path.join(p, "bin"), os.path.join(p, "lib")]
                    for pp in possible_paths:
                        if os.path.exists(pp):
                            os.add_dll_directory(pp)
                            os.environ["PATH"] = pp + os.pathsep + os.environ["PATH"]
            
            # Check zlibwapi
            import ctypes
            try:
                ctypes.CDLL("zlibwapi.dll")
                logger.info("Found zlibwapi.dll, GPU should work.")
                return True
            except:
                logger.warning("zlibwapi.dll not found! GPU might crash.")
                return False
        except Exception as e:
            logger.error(f"Failed to load NVIDIA libs: {e}")
            return False
    return True

def process_directory(directory_path, model_size="large-v3", force=False):
    directory = Path(directory_path)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return

    # Try faster-whisper import
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.error("faster-whisper not installed!")
        return

    # Load libs
    load_nvidia_libs()
    
    # Init Model
    logger.info(f"Loading model {model_size} on GPU (float16)...")
    try:
        # Use beam_size=1 to be safe on VRAM
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
    except Exception as e:
        logger.error(f"Failed to load model on GPU: {e}")
        logger.info("Fallback to CPU (int8)...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    files = [f for f in directory.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS]
    logger.info(f"Found {len(files)} files.")
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"[{i}/{len(files)}] Processing: {file_path.name}")
        
        cache_path = file_path.with_suffix(file_path.suffix + ".whisper.json")
        
        if cache_path.exists() and not force:
            logger.info(f"  Skipping (Cache exists).")
            continue
            
        try:
            logger.info(f"  Transcribing...")
            segments, info = model.transcribe(str(file_path), beam_size=1, word_timestamps=True)
            
            logger.info(f"  Detected language: {info.language}")
            
            # Consume generator
            segments_list = []
            for segment in segments:
                # Print dot for progress
                print(".", end="", flush=True)
                seg_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                }
                segments_list.append(seg_dict)
            print("") # Newline
                
            result = {
                "text": " ".join(s["text"] for s in segments_list),
                "segments": segments_list,
                "language": info.language
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            logger.info(f"  Saved to {cache_path.name}")
            
        except Exception as e:
            logger.error(f"  Failed: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    
    process_directory(args.directory, args.model, args.force)
