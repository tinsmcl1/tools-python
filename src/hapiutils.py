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


def hapi_to_df(
    data, round_to_sec: bool = False, clean_time: bool = False
) -> pd.DataFrame:
    """Convert hapi data array to a pandas DataFrame while preserving data types.

    Args:
        data (_type_): Hapi data array.
        round_to_sec (bool, optional): Round time to nearest second. Defaults to False.
        clean_time (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame: Hapi data in a pandas DataFrame.
    """
    # automatically 'cleans' hapitimes as well

    # if round_to_sec:
    #    dataA['Time'] = round_hapitime(dataA['Time'])

    has_multiD = False
    multiD = {}
    namelist = list(data.dtype.names)
    for name in data.dtype.names:
        try:
            if data[name].shape[1]:
                has_multiD = True
                multiD[name] = True
        except:
            multiD[name] = False

    if has_multiD:
        df = pd.DataFrame({"Time": data["Time"]})  # ,dtype='string')
        namelist.remove("Time")
        for name in namelist:
            if multiD[name]:
                # dfA[name] = pd.Series(dtype='object')
                df[name] = list(data[name])  # list or tuple work
                # dfA[name] = dataA[name].astype(object)
                # ",".join([str(val) for val in dataA[name]])
            else:
                df[name] = data[name]
    else:
        # easy case, all 1-D data so no fussing needed
        df = pd.DataFrame(data)

    # clean times
    df["Time"] = pd.to_datetime(
        df["Time"].str.decode("utf-8")
    )  # hapitime2datetime(np.array(dfA['Time']),**ops)
    if round_to_sec:
        df["Time"] = df["Time"].dt.round("S")
    df["Time"] = df["Time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

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


def df_round_to_sec(df) -> pd.DataFrame:
    """Rounds 'Time' column in df to nearest second and returns new DataFrame."""
    df["Time"] = pd.to_datetime(df["Time"].str.decode("utf-8"))
    df["Time"] = df["Time"].dt.round("s")
    df["Time"] = df["Time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return df
