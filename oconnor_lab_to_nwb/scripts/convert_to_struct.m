function data_path = convert_to_struct(dir_path, file_name, file_full_path, dataset_name, msessionexplorer_path)
    % dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitData/';
    % file_name = 'MSessionExplorer_KS0125B1.mat';
    % msessionexplorer_path = '/home/luiz/storage/taufferconsulting/client_ben/project_oconnor/MSessionExplorer';

    warning('off', 'MATLAB:MKDIR:DirectoryExists');

    % Add MSessionExplorer to matlab path
    addpath(genpath(msessionexplorer_path));

    % Load data with MSessionExplorer
    base_time_offset = 0;
    if file_full_path
        load([file_name]);
    else
        load([dir_path, file_name]);
    end

    % Export to Struct and save to mat file
    data = se.ToStruct();
    mkdir([dir_path, 'tmp']);

    if strcmp(dataset_name, 'seqlick')
        % Convert session start time from datetime format to string format
        session_start_time = datestr(se.userData.sessionInfo.sessionDatetime, 'yyyy-mm-dd HH:MM:SS');
        save([dir_path, 'tmp/data_struct.mat'], 'data', 'session_start_time', 'base_time_offset');
    else
        save([dir_path, 'tmp/data_struct.mat'], 'data');
    end
    
    % Return extracted data path
    data_path = [dir_path, 'tmp/data_struct.mat'];