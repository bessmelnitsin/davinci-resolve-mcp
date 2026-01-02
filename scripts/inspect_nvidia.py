
import os
import sys

try:
    import nvidia.cudnn
    print(f"nvidia.cudnn imported: {nvidia.cudnn}")
    print(f"nvidia.cudnn file: {getattr(nvidia.cudnn, '__file__', 'Not Found')}")
    print(f"nvidia.cudnn path: {getattr(nvidia.cudnn, '__path__', 'Not Found')}")

    import nvidia.cublas
    print(f"nvidia.cublas imported: {nvidia.cublas}")
    print(f"nvidia.cublas file: {getattr(nvidia.cublas, '__file__', 'Not Found')}")
    print(f"nvidia.cublas path: {getattr(nvidia.cublas, '__path__', 'Not Found')}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
