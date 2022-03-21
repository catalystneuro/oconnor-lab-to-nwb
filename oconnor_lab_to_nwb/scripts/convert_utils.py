import pynwb
import numpy as np

from units import tg_units, crossmodal_units


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


def convert_table_trials(trials_data, trials_times, nwbfile):
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



def convert_table_spike_times(spiking_data, trials_times, nwbfile):
    units_names = [k for k in spiking_data[0].__dict__.keys() if k != "_fieldnames"]
    for ui, uid in enumerate(units_names):
        all_spkt = list()
        for i, tr in enumerate(spiking_data):
            spkt = getattr(tr, uid)
            if isinstance(spkt, np.ndarray):
                spkt += trials_times[i][0]
                all_spkt.extend(list(spkt))
        nwbfile.add_unit(
            id=ui, 
            spike_times=all_spkt,
            obs_intervals=trials_times,
        )


def convert_table_continuous_variable(ts_data, trials_times, nwbfile, time_column="time"):
    # Create beahavior processing module and timeseries data interface
    nwbfile.create_processing_module(
        name="behavior",
        description="processed behavioral data"
    )

    # Store timeseries data in BehavioralTimeSeries data interface
    ts_names = [k for k in ts_data[0].__dict__.keys() if k not in ["_fieldnames", time_column]]
    for tsn in ts_names:
        bts = pynwb.behavior.BehavioralTimeSeries(name=f"BehavioralTimeSeries_{tsn}")
        nwbfile.processing["behavior"].add(bts)
        physical_unit=tg_units.get(tsn, "unknown")
        for ti, tr in enumerate(ts_data):
            rate = 1. / np.diff(getattr(tr, time_column)).mean()
            bts.create_timeseries(
                name=f"{tsn}_{ti}", 
                data=getattr(tr, tsn), 
                unit=physical_unit,
                starting_time=trials_times[ti][0], 
                rate=rate, 
                description="no description", 
                continuity="continuous"
            )