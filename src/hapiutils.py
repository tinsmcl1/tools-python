import copy
from typing import Literal

import numpy as np
import numpy.lib.recfunctions as nrecfun
import pandas as pd
from hapiclient.hapi import compute_dt
from hapiclient.hapitime import hapitime2datetime, datetime2hapitime


def nparray_unpack_to_list(arr) -> list:
    """Converts a np.ndarray to a list."""
    if type(arr) == np.ndarray:
        return arr.tolist()
    else:
        return arr


def merge_dtypes(dataA, dataB, trim: str = "Time"):
    """could not use stackoverflow comprehensives of forms a[0],str(a[1]) because
    it fails on 2D items like ('Field_Vector', '<f8', (3,))
    so we do it manually (and also strip out the extra 'Time' field
    """

    a = []
    for name in dataA.dtype.names:
        a.append((name, dataA.dtype.fields[name][0]))
    for name in dataB.dtype.names:
        if name != trim:
            a.append((name, dataB.dtype.fields[name][0]))
    return a


def hapi_to_df(data, round_to_sec: bool = False) -> pd.DataFrame:
    """Convert hapi data array to a pandas DataFrame, preserving data types.

    Args:
        data (_type_): Hapi data array.
        round_to_sec (bool, optional): Round time to nearest second. Defaults to False.

    Returns:
        pd.DataFrame: Hapi data in a pandas DataFrame.
    """
    data_dict = {}
    for name in data.dtype.names:
        column_data = data[name]

        # Check if the field's dtype includes a subarray shape (multi-dimensional)
        if len(column_data.shape) > 1:
            # Convert subarray fields into lists or tuples
            data_dict[name] = [element for element in column_data]
        else:
            # Directly assign the data for 1d dtypes
            data_dict[name] = column_data

    df = pd.DataFrame(data_dict)
    df = clean_time(df, round_to_sec=round_to_sec)
    return df


def merge_hapi(
    dataA,
    metaA,
    dataB,
    metaB,
    how: Literal["left", "right", "outer", "inner"] = "outer",
    round_to_sec: bool = False,
    fill_nan: bool = False,
):
    """Merge two hapi data arrays to single array via specified merge type. Returns 
    merged hapi data and meta objects.

    Args:
        dataA: Left hapi array to merge
        metaA: Meta corresponding with dataA
        dataB: Right hapi array to merge
        metaB: Meta corresponding with dataB
        how (str, optional): Type of merge: 'left', 'right', 'outer', or 'inner'. See 
            documentation for pandas.merge_ordered for descriptions. Defaults to 'outer'.
        round_to_sec (bool, optional): Rounds time to nearest second. Defaults to False.
        fill_nan (bool, optional): Fill NaNs according to fill_value from meta. Defaults 
            to False.
    """
    metaAB = copy.deepcopy(metaA)
    new_names = {}
    for param in metaB["parameters"]:
        if param["name"] != "Time":
            # If the field is already in the left array, change the field name
            if param in metaA["parameters"]:
                new_name = f"{param['name']}_{metaB['x_dataset']}"  # Does x_dataset always exist?
                new_names[param["name"]] = new_name
                param["name"] = new_name
            # Update meta
            metaAB["parameters"].append(param)

    dataB = nrecfun.rename_fields(dataB, new_names)

    # Convert structured arrays to DataFrames and merge on "Time" fields
    dfA = hapi_to_df(dataA, round_to_sec=round_to_sec)
    dfB = hapi_to_df(dataB, round_to_sec=round_to_sec)
    dfAB = pd.merge_ordered(dfA, dfB, on="Time", how=how)

    if fill_nan:
        dfAB = df_fill_nans(dfAB, metaAB)

    dataAB = df_to_hapi(dfAB, metaAB)

    return dataAB, metaAB


def clean_time(df: pd.DataFrame, round_to_sec: bool = False) -> pd.DataFrame:
    """Converts time to hapi specfied format and optionally rounds time to nearest second.

    Args:
        df (pd.DataFrame): DataFrame containing "Time" column to clean.
        round_to_sec (bool, optional): Rounds time to nearest second. Defaults to False.

    Returns:
        pd.DataFrame: DataFrame with "Time" column cleaned.
    """
    df["Time"] = pd.to_datetime(df["Time"].str.decode("utf-8"))
    if round_to_sec:
        df["Time"] = df["Time"].dt.round("s")
    df["Time"] = df["Time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return df


def df_fill_nans(df, meta) -> pd.DataFrame:
    """Returns new hapi DataFrame with all NaN values filled according to fill_value in meta."""
    for param in meta["parameters"]:
        name = param["name"]
        if param["fill"] is None:
            print(f"No fill: {param['name']} --> {param['fill']}")
        else:
            try:
                fill = float(param["fill"])
                df[name] = df[name].fillna(fill)
                print(f"Fill successful: {param['name']} --> {param['fill']}")
            except:
                print(f"Fill failed: {param['name']} -> {param['fill']}")
                pass
    return df


def dtypes_from_data(data) -> list:
    """Returns parameter data types from hapi data array."""
    dt = [(param, data.dtype.fields[param][0]) for param in data.dtype.names]
    return dt


def dtypes_from_meta(meta) -> list:
    """Returns parameter data types from meta."""
    dt, _, _, _, _, _ = compute_dt(meta, {"format": ""})
    return dt


def df_to_hapi(df, meta):
    """Converts a hapi DataFrame to a hapi array."""
    dt = dtypes_from_meta(meta)
    data = df.to_records(index=False, column_dtypes={"Time": "S30"})
    data = np.array(
        [tuple([nparray_unpack_to_list(e) for e in elm]) for elm in data], dtype=dt
    )
    data = np.array([tuple(i) for i in data], dtype=dt)
    return data


def resample_hapi(
    data,
    meta,
    interval: str,
    round_to_sec: bool = False,
    tolerance: float | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int | None = None,
):
    """
    Resample hapi data at specified intervals. If an exact time does not exist,
    substitutes with nearest time.
    """
    df = hapi_to_df(data, round_to_sec=round_to_sec)

    # Format dataframe for pandas resampling
    # df["Time"] = pd.to_datetime(df["Time"])
    df["Time"] = hapitime2datetime(df["Time"].values)
    df = df.set_index("Time")

    if start_time is not None:
        start_time = pd.to_datetime(start_time)
        df = df[df.index >= start_time]

    if end_time is not None:
        end_time = pd.to_datetime(end_time)
        df = df[df.index <= end_time]

    if tolerance:
        target_times = pd.date_range(
            start=df.index.min(), end=df.index.max(), freq=interval
        )
        tolerance_timedelta = pd.to_timedelta(tolerance)

        # Iterate over each target time and find the closest time within the tolerance
        sampled_rows = []
        for target_time in target_times:
            time_diffs = abs((df.index - target_time).total_seconds())
            closest_idx = time_diffs.idxmin()
            if time_diffs[closest_idx] <= tolerance_timedelta:
                sampled_rows.append(df.loc[closest_idx])

        resampled_df = pd.DataFrame(sampled_rows).reset_index()

    else:
        # Resample the DataFrame using the nearest value
        resampled_df = df.resample(interval, origin="start").nearest(limit=limit)
        resampled_df = resampled_df.reset_index()

    resampled_meta = copy.deepcopy(meta)  # Does meta need to be updated?
    resampled_df["Time"] = resampled_df["Time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # resampled_df["Time"] = datetime2hapitime(resampled_df["Time"].values)
    resampled_data = df_to_hapi(resampled_df, resampled_meta)
    return resampled_data, resampled_meta  # , resampled_df
