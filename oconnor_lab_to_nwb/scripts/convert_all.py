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
    crossmodal_start_times
)
from oconnor_lab_to_nwb.scripts.utils import (
    make_trials_times,
    convert_behavior_continuous_variables, 
    convert_ecephys, 
    convert_spike_times, 
    convert_trials
)


dataset_name = "crossmodal"  # tg, crossmodal
msessionexplorer_path = '/home/luiz/storage/taufferconsulting/client_ben/project_oconnor/MSessionExplorer'

if dataset_name == "tg":
    units_map = tg_units
    dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/SeversonXu2017/UnitData/'
    all_files = list()
    for pp in Path(dir_path).glob("*"):
        if pp.name.endswith(".mat"):
            all_files.append(pp.name)
    output_dir = "/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/converted/"
    metadata_df = pd.read_csv('/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/seversonxu2017_metadata.csv')
    experimenters = ["Kyle S Severson", "Duo Xu"]
    related_publications = ["DOI: 10.1016/j.neuron.2017.03.045"]

elif dataset_name == "crossmodal":
    units_map = crossmodal_units
    dir_path = '/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/CrossModal/'
    all_files = list()
    for pp in Path(dir_path).glob("*"):
        if pp.name.endswith(".mat"):
            all_files.append(pp.name)
    output_dir = "/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/CrossModal/converted/"
    # metadata_df = pd.read_csv('/media/luiz/storage/taufferconsulting/client_ben/project_oconnor/TG/seversonxu2017_metadata.csv')
    experimenters = [""]
    related_publications = [""]


eng = matlab.engine.start_matlab()

for file_name in all_files:
    data_path = eng.convert_to_struct(dir_path, file_name, msessionexplorer_path)
    print(f"{file_name} data extracted to {data_path}")

    data = loadmat(data_path)["data"]

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
            raise Exception(f"Metadata not found for {recording_id}")

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
        recording_id = file_name.split("_")[0]
        session_start_time = datetime.strptime(crossmodal_start_times[file_name.split(".")[0]], "%d/%m/%y %H:%M:%S").replace(tzinfo=tz.gettz("US/Eastern"))
        init_metadata = dict(
            session_description=data["userData"]["sessionInfo"]["MouseName"] + "_" + data["userData"]["sessionInfo"]["seshDate"],
            identifier=str(uuid.uuid4()),
            session_start_time=session_start_time,
            lab="O'Connor lab",
            institution="Johns Hopkins University",
            # experimenter=experimenters,  # TODO
            # related_publications=related_publications  # TODO
        )

        subject_metadata = dict(
            subject_id=data["userData"]["sessionInfo"]["MouseName"],
            date_of_birth=datetime.strptime(data["userData"]["sessionInfo"]["DoB"], "%y%m%d").replace(tzinfo=tz.gettz("US/Eastern")),
            description="no description",
            species="Mus musculus",
            genotype=data["userData"]["sessionInfo"]["Genotype"]
            # sex=recording_df["sex"].values[0],  # TODO
        )

    # Create nwbfile with initial metadata
    nwbfile = nwbfile = pynwb.NWBFile(**init_metadata)

    # Add subject
    nwbfile.subject = pynwb.file.Subject(**subject_metadata)

    # Convert trials data
    trials_times = make_trials_times(data=data)
    trials_data = data["tableData"][np.where(data["tableType"] == "eventValues")[0][0]]
    convert_trials(
        trials_data=trials_data, 
        trials_times=trials_times,
        nwbfile=nwbfile
    )

    for n, t, d in zip(data["tableName"], data["tableType"], data["tableData"]):
        # Convert spiking data
        if t == "eventTimes" and n in ["spikeTime", "spikeTimes"] :
            convert_spike_times(
                spiking_data=d, 
                trials_times=trials_times,
                nwbfile=nwbfile
            )            
        # Convert timeseries data
        elif t == "timeSeries":
            if n == "LFP":
                convert_ecephys(
                    ts_data=d, 
                    trials_times=trials_times,
                    nwbfile=nwbfile, 
                    units_map=units_map,
                    extra_data=data["userData"],
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

    # Save nwb file
    output_file = output_dir + f"{dataset_name}_{recording_id}.nwb"
    with pynwb.NWBHDF5IO(output_file, "w") as io:
        io.write(nwbfile)

    print(f"Data successfully converted: {output_file}")
    print()