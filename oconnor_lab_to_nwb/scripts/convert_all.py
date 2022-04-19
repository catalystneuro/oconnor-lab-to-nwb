import pynwb
import matlab.engine
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
from pathlib import Path
import uuid

from oconnor_lab_to_nwb.scripts.load_mat_struct import loadmat
from oconnor_lab_to_nwb.scripts.misc_data import (
    tg_units, 
    crossmodal_units,
    seqlick_units
)
from oconnor_lab_to_nwb.scripts.utils import (
    get_all_mat_files,
    make_trials_times,
    convert_behavior_continuous_variables, 
    convert_ecephys, 
    convert_spike_times, 
    convert_trials,
    get_trials_recordings_time_offsets
)


eng = matlab.engine.start_matlab()
msessionexplorer_path = '/home/luiz/storage/taufferconsulting/client_ben/project_oconnor/MSessionExplorer'
dataset_name = "seqlick"  # tg, crossmodal, seqlick

# Each dataset has its metadata extracted in a different way
if dataset_name == "tg":
    units_map = tg_units
    # dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitData/'
    dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitDataEMG/'
    output_dir = "/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/converted/"    
    experimenters = ["Kyle S Severson", "Duo Xu"]
    related_publications = ["DOI: 10.1016/j.neuron.2017.03.045"]
    metadata_df = pd.read_csv('/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/seversonxu2017_metadata.csv')

elif dataset_name == "crossmodal":
    units_map = crossmodal_units
    dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/CrossModal/'
    output_dir = "/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/CrossModal/converted/"
    experimenters = ["Yi-Ting Chang"]

elif dataset_name == "seqlick":
    units_map = seqlick_units
    dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/SeqLick/'
    output_dir = "/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/SeqLick/converted/"
    experimenters = ["Duo Xu"]
    related_publications = ["DOI: 10.1038/s41586-022-04478-7"]
    metadata_df = pd.read_csv('/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/SeqLick/metadata.csv')

# Get all .mat files for conversion
if dataset_name == "seqlick":
    all_files = get_all_mat_files(path_base=dir_path, exclude_dirs=["Supporting files"])
else:
    all_files = list()
    for pp in Path(dir_path).glob("*"):
        if pp.name.endswith(".mat"):
            all_files.append(pp.name)

for file_name in all_files:
    if dataset_name == "tg":
        data_path = eng.convert_to_struct(dir_path, file_name, False, dataset_name, msessionexplorer_path)
        print(f"{file_name} data extracted to {data_path}")
        data = loadmat(data_path)["data"]
    elif dataset_name == "seqlick":
        data_path = eng.convert_to_struct(dir_path, file_name, True, dataset_name, msessionexplorer_path)
        print(f"{file_name} data extracted to {data_path}")
        data = loadmat(data_path)["data"]
        session_start_datetime_str = loadmat(data_path)["session_start_time"]
    else:
        data_path = dir_path + file_name
        data = loadmat(data_path)["struct_version"]

    # First checks of content
    for n in ['tableName', 'tableType', 'tableData', 'referenceTime', 'epochInd', 'userData']:
        if n not in data.keys():
            raise Exception(f"{n} nor found in data: {data_path}")
    print(f"All checks OK for data: {data_path}")

    # Get metadata
    if dataset_name == "tg":
        recording_id = file_name.split("MSessionExplorer_KS0")[1][0:4]
        recording_df = metadata_df[metadata_df["recording_id"] == recording_id]
        if len(recording_df) == 0:
            print(f"Metadata not found for {recording_id}. Skipping it...")
            print()
            continue
        
        session_start_time = datetime.strptime(recording_df["recording_date"].values[0] + " 12:00:00", "%m/%d/%y %H:%M:%S").replace(tzinfo=tz.gettz("US/Eastern"))
        init_metadata = dict(
            session_description=data["userData"]["sessionName"],
            identifier=data["userData"]["sessionName"],
            session_start_time=session_start_time,
            lab="O'Connor lab",
            institution="Johns Hopkins University",
            experimenter=experimenters,
            related_publications=related_publications
        )

        subject_metadata = dict(
            subject_id=recording_df["mouse_id"].values[0],
            date_of_birth=datetime.strptime(recording_df["dob"].values[0], "%m/%d/%y").replace(tzinfo=tz.gettz("US/Eastern")),
            description="no description",
            species="Mus musculus",
            sex=recording_df["sex"].values[0],
            strain=recording_df["mouse_line"].values[0]
        )

    elif dataset_name == "crossmodal":
        recording_id = file_name.split(".mat")[0]
        session_start_date_str = data["userData"]["sessionInfo"]["seshDate"]  #yymmdd
        session_start_time_str = data["userData"]["sessionInfo"]["session_start_time"]  #hhmmss
        session_start_time = datetime.strptime(session_start_date_str + " " + session_start_time_str, "%y%m%d %H%M%S").replace(tzinfo=tz.gettz("US/Eastern"))
        init_metadata = dict(
            session_description=data["userData"]["sessionInfo"]["MouseName"] + "_" + data["userData"]["sessionInfo"]["seshDate"],
            identifier=str(uuid.uuid4()),
            session_start_time=session_start_time,
            lab="O'Connor lab",
            institution="Johns Hopkins University",
            experimenter=experimenters,
        )

        subject_metadata = dict(
            subject_id=data["userData"]["sessionInfo"]["MouseName"],
            date_of_birth=datetime.strptime(data["userData"]["sessionInfo"]["DoB"], "%y%m%d").replace(tzinfo=tz.gettz("US/Eastern")),
            description="no description",
            species="Mus musculus",
            genotype=data["userData"]["sessionInfo"]["Genotype"],
            sex="M" if data["userData"]["sessionInfo"]["sex"] == "male" else "F"
        )

    elif dataset_name == "seqlick":
        subject_id = data["userData"]["sessionInfo"]["animalId"]
        recording_df = metadata_df[metadata_df["subject_id"] == subject_id]
        if len(recording_df) == 0:
            print(f"Metadata not found for {subject_id}. Skipping it...")
            print()
            continue
        
        recording_id = file_name.split("/")[-1].replace(".mat", "").replace(" ", "")
        session_description = file_name.split("SeqLick/")[-1].replace(".mat", "").replace("/", " - ")
        session_start_time = datetime.strptime(session_start_datetime_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz.gettz("US/Eastern"))
        init_metadata = dict(
            session_description=session_description,
            identifier=str(uuid.uuid4()),
            session_start_time=session_start_time,
            lab="O'Connor lab",
            institution="Johns Hopkins University",
            experimenter=experimenters,
        )

        dob = datetime.strptime(recording_df["dob"].values[0] + " 12:00:00", "%m/%d/%y %H:%M:%S").replace(tzinfo=tz.gettz("US/Eastern"))
        subject_metadata = dict(
            subject_id=subject_id,
            date_of_birth=dob,
            description="no description",
            species="Mus musculus",
            sex=recording_df["sex"].values[0],
            genotype=recording_df["genotype"].values[0],
        )


    # Create nwbfile with initial metadata
    nwbfile = nwbfile = pynwb.NWBFile(**init_metadata)

    # Add subject
    nwbfile.subject = pynwb.file.Subject(**subject_metadata)

    # Convert trials data
    trials_recordings_time_offsets = get_trials_recordings_time_offsets(
        data=data, 
        dataset_name=dataset_name
    )
    trials_times = make_trials_times(
        data=data, 
        trials_recordings_time_offsets=trials_recordings_time_offsets,
        dataset_name=dataset_name
    )
    trials_data = data["tableData"][np.where(data["tableType"] == "eventValues")[0][0]]
    convert_trials(
        trials_data=trials_data, 
        trials_times=trials_times,
        nwbfile=nwbfile
    )

    # Convert timeseries data
    for n, t, d in zip(data["tableName"], data["tableType"], data["tableData"]): 
        if t == "timeSeries":
            if n == "LFP": 
                if dataset_name == "crossmodal":
                    convert_ecephys(
                        ts_data=d, 
                        trials_times=trials_times,
                        nwbfile=nwbfile, 
                        extra_data=data["userData"],
                        dataset_name=dataset_name,
                        time_column="time"
                    )
            else:
                convert_behavior_continuous_variables(
                    ts_data=d, 
                    trials_times=trials_times,
                    nwbfile=nwbfile, 
                    units_map=units_map,
                    time_column="time"
                )
    
    # Convert spiking data
    ind_t = np.where(data["tableType"] == "eventTimes")[0]
    ind_n = np.where([tn in ["spikeTime", "spikeTimes"] for tn in data["tableName"]])[0]
    ind_spks = np.intersect1d(ind_t, ind_n)
    if len(ind_spks) > 0:
        spiking_data = data["tableData"][ind_spks[0]]
        convert_spike_times(
            spiking_data=spiking_data, 
            trials_times=trials_times,
            trials_recordings_time_offsets=trials_recordings_time_offsets,
            nwbfile=nwbfile
        )           

    # Save nwb file
    output_file = output_dir + f"{dataset_name}_{recording_id}.nwb"
    with pynwb.NWBHDF5IO(output_file, "w") as io:
        io.write(nwbfile)

    print(f"Data successfully converted: {output_file}")
    print()