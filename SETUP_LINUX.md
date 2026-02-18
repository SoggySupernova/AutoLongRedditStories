# Prerequisites
---
Tested on Python 3.10 and uv 0.10.3. If something breaks, try installing these specific versions!
---
You need ffmpeg and ollama correctly installed and configured. You need to download a specific LLM as well:
```shell
ollama pull ministral-3:8b-instruct-2512-q4_K_M
actually i lied its gemma3:4b
```







1. Clone and navigate to this repository.

2. Follow the instructions in tts_turbo.py.

3. Type these commands:
```
uv venv chatter --python 3.10
source chatter/bin/activate.fish # may be .sh or something else
uv pip install -r requirements.txt
```
There may be errors about missing setuptools or numpy, try installing those then running uv pip install -r requirements.txt --no-build-isolation
## Install PyTorch
NVIDIA GPU
```
# Install pytorch with your CUDA version, e.g.
uv pip install torch==2.6.0+cu124 torchaudio==2.6.0+cu124 --extra-index-url https://download.pytorch.org/whl/cu124
```
AMD GPU (not tested)
```
# Install pytorch with your ROCm version (Linux only), e.g.
uv pip install torch==2.5.1+rocm6.2 torchaudio==2.5.1+rocm6.2 --extra-index-url https://download.pytorch.org/whl/rocm6.2
```
Intel GPU (not tested)
```
# Install pytorch with your XPU version, e.g.
# Intel® Deep Learning Essentials or Intel® oneAPI Base Toolkit must be installed
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/test/xpu

# Intel GPU support is also available through IPEX (Intel® Extension for PyTorch)
# IPEX does not require the Intel® Deep Learning Essentials or Intel® oneAPI Base Toolkit
# See: https://pytorch-extension.intel.com/installation?request=platform
```
Apple Silicon (not tested)
```
# Install the stable pytorch, e.g.
uv pip install torch torchaudio
```



