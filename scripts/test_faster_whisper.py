
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fw():
    logger.info("Starting faster-whisper test...")
    try:
        from faster_whisper import WhisperModel
        logger.info("Imported WhisperModel")
    except ImportError as e:
        logger.error(f"Failed to import faster_whisper: {e}")
        return

    model_size = "large-v3" # Use production model for accuracy check
    
    try:
        # GPU Support: Load NVIDIA DLLs if installed
        try:
            import nvidia.cudnn
            import nvidia.cublas
            import os
            import sys
            
            # Add DLL directories for Windows
            if sys.platform.startswith("win"):
                for lib in [nvidia.cudnn, nvidia.cublas]:
                    paths = getattr(lib, "__path__", [])
                    for p in paths:
                        possible_paths = [
                            p,
                            os.path.join(p, "bin"),
                            os.path.join(p, "lib")
                        ]
                        for pp in possible_paths:
                            if os.path.exists(pp):
                                logger.info(f"Adding DLL path: {pp}")
                                os.add_dll_directory(pp)
                                os.environ["PATH"] = pp + os.pathsep + os.environ["PATH"]
        except ImportError:
            logger.warning("NVIDIA libraries not found via pip")
        except Exception as e:
            logger.warning(f"Failed to load NVIDIA DLLs: {e}")

        # Check for zlibwapi.dll (critical for cuDNN on Windows)
        import ctypes
        try:
            ctypes.CDLL("zlibwapi.dll")
            logger.info("Found zlibwapi.dll, proceeding with GPU/auto.")
            target_device = "auto"
        except Exception as e:
            logger.warning(f"Could not load zlibwapi.dll ({e}). This is required for NVIDIA cuDNN on Windows.")
            logger.warning("Falling back to CPU to prevent runtime crash.")
            target_device = "cpu"

        try:
            logger.info(f"Loading model {model_size} on {target_device}...")
            model = WhisperModel(model_size, device=target_device, compute_type="float16")
            logger.info(f"Model loaded successfully, ready for transcription.")
        except Exception as e:
            logger.warning(f"Init failed: {e}")
            return

        # Create a dummy file or use existing

        
        # Create a dummy file or use existing
        file_path = r"A:\010101\test\A001_08071102_C026.mov"
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return

        logger.info(f"Transcribing {file_path}...")
        segments, info = model.transcribe(file_path, beam_size=5)
        
        logger.info(f"Detected language: {info.language}")
        
        count = 0
        for segment in segments:
            logger.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            # count += 1
            # if count >= 3:
            #     logger.info("Stopping after 3 segments for test.")
            #     break
                
        logger.info("Test complete.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fw()
