function data_path = convert_to_struct(dir_path, file_name, msessionexplorer_path)
    % dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitData/';
    % file_name = 'MSessionExplorer_KS0125B1.mat';
    % msessionexplorer_path = '/home/luiz/storage/taufferconsulting/client_ben/project_oconnor/MSessionExplorer';

    % Add MSessionExplorer to matlab path
    addpath(genpath(msessionexplorer_path));

    % Load data with MSessionExplorer
    load([dir_path, file_name]);

    % Export to Struct and save to mat file
    data = se.ToStruct();
    mkdir([dir_path, 'tmp']);
    save([dir_path, 'tmp/data_struct.mat'], 'data');
    
    % Return extracted data path
    data_path = [dir_path, 'tmp/data_struct.mat'];