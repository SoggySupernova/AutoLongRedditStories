# Prerequisites
---
Tested on Python 3.11.9 and pip 23.0.1. Make sure you have the right version, this will save you many headaches!
---
You need ffmpeg, ollama, and ImageMagick correctly installed and configured. You need to download a specific LLM as well:
```shell
ollama pull ministral-3:8b-instruct-2512-q4_K_M
```






1. Install the python install manager (py)

2. Clone and navigate to this repository

3. in regular cmd window, not powershell:
```
py install 3.10
py -3.10 -m venv chatter
.\chatter\Scripts\activate.bat
pip install -r requirements.txt
```
(environment variables are stupid)
## Install PyTorch
NVIDIA GPU
```
# Install pytorch with your CUDA version, e.g.
pip install torch==2.6.0+cu124 torchaudio==2.6.0+cu124 --extra-index-url https://download.pytorch.org/whl/cu124
```
AMD GPU (not tested)
```
# Install pytorch with your ROCm version (Linux only), e.g.
pip install torch==2.5.1+rocm6.2 torchaudio==2.5.1+rocm6.2 --extra-index-url https://download.pytorch.org/whl/rocm6.2
```
Intel GPU (not tested)
```
# Install pytorch with your XPU version, e.g.
# Intel® Deep Learning Essentials or Intel® oneAPI Base Toolkit must be installed
pip install torch torchaudio --index-url https://download.pytorch.org/whl/test/xpu

# Intel GPU support is also available through IPEX (Intel® Extension for PyTorch)
# IPEX does not require the Intel® Deep Learning Essentials or Intel® oneAPI Base Toolkit
# See: https://pytorch-extension.intel.com/installation?request=platform
```
Apple Silicon (not tested)
```
# Install the stable pytorch, e.g.
pip install torch torchaudio
```



