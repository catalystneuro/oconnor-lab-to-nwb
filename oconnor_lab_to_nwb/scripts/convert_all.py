import matlab.engine
from .load_mat_struct import loadmat


msessionexplorer_path = '/home/luiz/storage/taufferconsulting/client_ben/project_oconnor/MSessionExplorer'
dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitData/'
file_name = 'MSessionExplorer_KS0125B1.mat'

eng = matlab.engine.start_matlab()
data_path = eng.convert_to_struct(dir_path, file_name, msessionexplorer_path)
print(f"{file_name} data extracted to {data_path}")

data = loadmat(data_path)["data"]