# oconnor-lab-to-nwb


# Install
Create a separate environment for your project:
```bash
conda create -n env_oconnor python=3.8 pip
conda activate env_oconnor
```

Install requirements:
```bash
pip install -r requirements.txt
```

Install matlab engine for python ([reference](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)):
```bash
cd "matlabroot/extern/engines/python"
python setup.py install
```