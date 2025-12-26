cd ~
sudo apt update
sudo apt upgrade -y
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev espeak libespeak-dev ffmpeg
wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz
tar -xvf Python-3.10.0.tgz
cd Python-3.10.0
./configure --enable-optimizations
make
sudo make altinstall
python3.10 -m venv venv
source venv/bin/activate
pip install numpy==1.22.4
pip install aeneas