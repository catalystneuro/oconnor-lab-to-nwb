import pynwb
import math
import numpy as np
from pathlib import Path


def get_all_mat_files(path_base, exclude_dirs=["Supporting files"]):
    all_files = list()
    for p in Path(path_base).iterdir():
        # If it is subdir
        if p.is_dir() and p.name not in exclude_dirs:
            all_files.extend(get_all_mat_files(path_base=p))
        # If it is .mat file
        if p.is_file() and p.suffix == ".mat" and "seArray.mat" not in p.name:
            all_files.append(str(p.resolve()))
    return all_files


def get_trials_recordings_time_offsets(data, dataset_name, base_time_offset=0):
    table_timeseries = data["tableData"][np.where(data["tableType"] == "timeSeries")[0][0]]
    if dataset_name == "crossmodal":
        offsets = list()
        for tr in table_timeseries:
            offsets.append(tr.time[0])
    else:
        offsets = np.zeros(len(table_timeseries)) - base_time_offset
    return np.array(offsets)


def make_trials_times(data, trials_recordings_time_offsets, dataset_name):
    # Make trials (start, stop) times list
    if dataset_name == "tg":
        reference_times = data["referenceTime"][0]
    else:
        reference_times = np.array(data["referenceTime"][0]) + trials_recordings_time_offsets

    trial_duration_increase = 0.
    if dataset_name == "seqlick" and len(np.where(data["tableName"] == "LFP")[0]) > 0:
        timeseries_data = data["tableData"][np.where(data["tableName"] == "LFP")[0][0]]
        trial_duration_increase = 0.01  # some spikes occurred in brief periods inter-intervals
    else:
        timeseries_data = data["tableData"][np.where(data["tableType"] == "timeSeries")[0][0]]
    
    if dataset_name == "tg":
        last_time = 0
    else:
        last_time = reference_times[0]

    trials_times = list()
    for i, td in enumerate(timeseries_data):
        duration = td.time[-1] - td.time[0] + trial_duration_increase
        trials_times.append((float(last_time), float(last_time + duration)))
        if dataset_name == "tg":
            last_time = last_time + duration + 2.
        elif len(reference_times) == i + 1:
            pass
        else:
            last_time = reference_times[i + 1]

    return trials_times


def convert_trials(trials_data, trials_times, nwbfile):
    # Add stimulus attributes as trials columns
    exclude_attributes = ['_fieldnames', 'trialNums', 'trialNum', 'bct_trialNum']
    stim_attributes_names = [k for k in trials_data[0].__dict__.keys() if k not in exclude_attributes]
    for at in stim_attributes_names:
        nwbfile.add_trial_column(name=at, description='no description')

    for i, tr in enumerate(trials_data):
        extra_params = dict()
        for a in stim_attributes_names:
            val = getattr(tr, a)
            if a == "posIndex" or isinstance(val, (list, tuple, np.ndarray)):  # if value is an array, it must be converted to string to fit cell in table
                extra_params[a] = str(a)
            elif isinstance(val, str):
                extra_params[a] = val
            elif math.isnan(val):
                extra_params[a] = np.nan
            else:
                extra_params[a] = float(val)

        tr_dict = dict(
            start_time=trials_times[i][0], 
            stop_time=trials_times[i][1],
            **extra_params
        )
        nwbfile.add_trial(**tr_dict)



def convert_spike_times(spiking_data, trials_times, trials_recordings_time_offsets, dataset_name, nwbfile):
    if dataset_name == "crossmodal":
        obs_intervals=[[start - 0.001, stop + 0.001] for start, stop in trials_times]
    else:
        obs_intervals = trials_times

    units_names = [k for k in spiking_data[0].__dict__.keys() if k != "_fieldnames"]
    for ui, uid in enumerate(units_names):
        all_spkt = list()
        for i, tr in enumerate(spiking_data):
            spkt = getattr(tr, uid)
            if isinstance(spkt, np.ndarray) and len(spkt) > 0:
                spkt += trials_times[i][0] - trials_recordings_time_offsets[i]
                all_spkt.extend(list(spkt))
        nwbfile.add_unit(
            id=ui, 
            spike_times=all_spkt,
            obs_intervals=obs_intervals,
        )


def convert_behavior_continuous_variables(
    ts_data, 
    trials_times, 
    nwbfile, 
    units_map,
    time_column="time"
):
    # Create processing module and timeseries data interface
    if "behavior" not in nwbfile.processing:
        nwbfile.create_processing_module(
            name="behavior",
            description=f"processed behavioral data"
        )

    # Store timeseries data in BehavioralTimeSeries data interface
    ts_names = [k for k in ts_data[0].__dict__.keys() if k not in ["_fieldnames", time_column]]
    for tsn in ts_names:
        ts = pynwb.behavior.BehavioralTimeSeries(name=f"BehavioralTimeSeries_{tsn}")
        nwbfile.processing["behavior"].add(ts)

        physical_unit=units_map.get(tsn, "unknown")
        for ti, tr in enumerate(ts_data):
            rate = 1. / np.diff(getattr(tr, time_column)).mean()
            ts.create_timeseries(
                name=f"{tsn}_{ti}", 
                data=getattr(tr, tsn), 
                unit=physical_unit,
                starting_time=trials_times[ti][0], 
                rate=rate, 
                description="no description", 
                continuity="continuous"
            )


def convert_ecephys(
    ts_data, 
    trials_times, 
    nwbfile, 
    extra_data,
    dataset_name,
    time_column="time"
):
    if dataset_name == "crossmodal":
        channel_ids = extra_data["sessionInfo"]["channel_map"]["chanMap"]
        channel_x = extra_data["sessionInfo"]["channel_map"]["xcoords"]
        channel_y = extra_data["sessionInfo"]["channel_map"]["ycoords"]
        elec_location = extra_data["sessionInfo"]["recSite"]

    # Create device and electrode group
    device = nwbfile.create_device(
        name='ecephys_device',
        description='ecephys_device'
    )

    electrode_group = nwbfile.create_electrode_group(
        name="electrode_group",
        description="no description",
        device=device,
        location=elec_location
    )

    # Add electrodes to the electrode table
    for i, (elec_id, x, y) in enumerate(zip(channel_ids, channel_x, channel_y)):
        nwbfile.add_electrode(
            x=np.nan, 
            y=np.nan, 
            z=np.nan, 
            imp=np.nan,
            location='unknown',
            filtering='unknown',
            group=electrode_group,
            id=int(elec_id),
            rel_x=float(x), 
            rel_y=float(y), 
        )

    # Create processing module and timeseries data interface
    nwbfile.create_processing_module(
        name="ecephys",
        description=f"processed ecephys data"
    )

    lfp = pynwb.ecephys.LFP(name="LFP")
    nwbfile.processing["ecephys"].add(lfp)

    # Loop through trials to create electrical series
    channel_names = [k for k in ts_data[0].__dict__.keys() if k not in ["_fieldnames", time_column]]
    for ti, tr in enumerate(ts_data):
        sampling_rate = 1. / np.diff(getattr(tr, time_column)).mean()

        all_data_trial = list()
        elecs_region = list()
        for ci in channel_ids:
            all_data_trial.append(getattr(tr, f"channel_{ci}"))
            elecs_region.append(np.where(ci == nwbfile.electrodes.id[:])[0][0])

        elecs_table_region = nwbfile.create_electrode_table_region(
            region=elecs_region,
            description='all electrodes'
        )
        
        lfp.create_electrical_series(
            name=f"ElectricalSeries_{ti}", 
            data=np.array(all_data_trial).T, 
            electrodes=elecs_table_region, 
            conversion=1e-6,  # in CrossModal LFP is in microvolt 
            starting_time=trials_times[ti][0],
            rate=float(sampling_rate), 
            description='no description', 
        )
