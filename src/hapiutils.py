from hapiclient.hapitime import hapitime2datetime, datetime2hapitime
import numpy.lib.recfunctions as nrecfun
import numpy as np
import pandas as pd
import copy
from datetime import datetime, timedelta


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
    dataA, metaA, dataB, metaB, round_to_sec: bool = False, fill_nan: bool = False, join_all: bool = True
):
    """Merge two hapi data arrays to a single array. Returns merged hapi data and meta objects.

    Args:
        data1 (_type_): Left hapi array to merge
        meta1 (_type_): Meta corresponding with data1
        data2 (_type_): Right hapi array to merge
        meta2 (_type_): Meta corresponding with data2
        round_to_sec (bool, optional): Rounds time to nearest second. Defaults to False.
        fill_nan (bool, optional): Fill NaNs according to fill_value from meta. Defaults to False.
        join_all (bool, optional): _description_
    """
    metaAB = copy.deepcopy(metaA)
    for ele in metaB["parameters"]:
        if ele["name"] != "Time" and (join_all or (ele not in metaA["parameters"])):
            # adjust both dataframe name and hapi metadata
            if ele in metaA["parameters"]:
                name = ele["name"]
                new_name = (
                    f"{name}_{metaB['x_dataset']}"  # does x_dataset always exist?
                )
                dataB = nrecfun.rename_fields(dataB, {name: new_name})
                ele["name"] = new_name
            metaAB["parameters"].append(ele)

    dfA = hapi_to_df(dataA, round_to_sec=round_to_sec)
    dfB = hapi_to_df(dataB, round_to_sec=round_to_sec)
    dt = merge_dtypes(dataA, dataB, trim="Time")
    dfAB = pd.merge_ordered(dfA, dfB)  # Works!

    # walk through dfAC and fill all numeric 'NaN' with 'fill' from meta
    if fill_nan:
        for ele in metaAB["parameters"]:
            name = ele["name"]
            try:
                if ele["fill"] != None:
                    fill = float(ele["fill"])
                    print("Filling with: ", fill, ele)
                    dfAB[name] = dfAB[name].fillna(fill)
            except:
                print("NO fill for ", ele["fill"], ele)
                pass

    dataAB = dfAB.to_records(index=False, column_dtypes={"Time": "S30"})
    dataAB = np.array(
        [tuple([nparray_unpack_to_list(e) for e in elm]) for elm in dataAB], dtype=dt
    )
    dataAB = np.array([tuple(i) for i in dataAB], dtype=dt)

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


