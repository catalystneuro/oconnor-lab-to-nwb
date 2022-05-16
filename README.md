# oconnor-lab-to-nwb


## Installation
Create a separate environment for your project (MATLAB Engine for Python will require Python 3.7 or 3.8):
```bash
conda create -n env_oconnor python=3.8 pip
conda activate env_oconnor
```

Install requirements:
```bash
pip install .
```

Install matlab engine for python ([reference](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)):
```bash
cd "matlabroot/extern/engines/python"
python setup.py install
```

## DANDI

DANDI set: https://gui.dandiarchive.org/#/dandiset/000226

To download DANDI set:
```bash
dandi download https://dandiarchive.org/dandiset/000226/draft
```

To update DANDI set: [documentation](https://www.dandiarchive.org/handbook/10_using_dandi/#uploading-a-dandiset)
```bash
dandi upload --sync
```