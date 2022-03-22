import pynwb
import numpy as np


def make_trials_times(data):
    # Make trials (start, stop) times list
    reference_times = data["referenceTime"][0]
    timeseries_data = data["tableData"][np.where(data["tableType"] == "timeSeries")[0][0]]
    if len(reference_times) == 0:
        last_time = 0
    else:
        last_time = reference_times[0]

    trials_times = list()
    for i, td in enumerate(timeseries_data):
        duration = td.time[-1] - td.time[0]
        trials_times.append((float(last_time), float(last_time + duration)))
        if len(reference_times) == 0 or len(reference_times) == i - 1:
            last_time = last_time + duration + 2.
        else:
            last_time = reference_times[i + 1]

    return trials_times


def convert_trials(trials_data, trials_times, nwbfile):
    # Add stimulus attributes as trials columns
    stim_attributes_names = [k for k in trials_data[0].__dict__.keys() if k not in ['_fieldnames', 'trialNums', 'bct_trialNum']]
    for at in stim_attributes_names:
        nwbfile.add_trial_column(name=at, description='no description')

    for i, tr in enumerate(trials_data):
        extra_params = {a:getattr(tr, a) for a in stim_attributes_names}
        tr_dict = dict(
            start_time=trials_times[i][0], 
            stop_time=trials_times[i][1],
            **extra_params
        )
        nwbfile.add_trial(**tr_dict)



def convert_spike_times(spiking_data, trials_times, nwbfile):
    units_names = [k for k in spiking_data[0].__dict__.keys() if k != "_fieldnames"]
    for ui, uid in enumerate(units_names):
        all_spkt = list()
        for i, tr in enumerate(spiking_data):
            spkt = getattr(tr, uid)
            if isinstance(spkt, np.ndarray) and len(spkt) > 0:
                spkt += trials_times[i][0]
                all_spkt.extend(list(spkt))
        nwbfile.add_unit(
            id=ui, 
            spike_times=all_spkt,
            obs_intervals=trials_times,
        )


def convert_behavior_continuous_variables(
    ts_data, 
    trials_times, 
    nwbfile, 
    units_map,
    time_column="time"
):
    # Create processing module and timeseries data interface
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
    units_map,
    extra_data,
    time_column="time"
):
    channel_ids = extra_data["userData"]["sessionInfo"]["channel_map"]["chanMap"]
    channel_x = extra_data["userData"]["sessionInfo"]["channel_map"]["xcoords"]
    channel_y = extra_data["userData"]["sessionInfo"]["channel_map"]["ycoords"]
    sampling_rate = extra_data["userData"]["sessionInfo"]["channel_map"]["fs"]
    elec_location = extra_data["userData"]["sessionInfo"]["recSite"]

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
    for i, elec_id, x, y in enumerate(zip(channel_ids, channel_x, channel_y)):
        nwbfile.add_electrode(
            x=np.nan, 
            y=np.nan, 
            z=np.nan, 
            imp=np.nan,
            location='unknown',
            filtering='unknown',
            group=electrode_group,
            id=elec_id,
            rel_x=x, 
            rel_y=y, 
        )

    # Create processing module and timeseries data interface
    nwbfile.create_processing_module(
        name="ecephys",
        description=f"processed ecephys data"
    )

    lfp = pynwb.ecephys.LFP(name="LFP")
    nwbfile.processing["behavior"].add(lfp)

    channel_names = [k for k in ts_data[0].__dict__.keys() if k not in ["_fieldnames", time_column]]
    for ti, tr in enumerate(ts_data):
        for cn in channel_names:
            getattr(tr, cn)
        lfp.create_electrical_series(
            name=f"ElectricalSeries_{ti}", 
            data=trial_data, 
            electrodes, 
            channel_conversion=None, 
            filtering=None, 
            resolution=-1.0, 
            conversion=1.0, 
            starting_time=None, 
            rate=sampling_rate, 
            description='no description', 
        )