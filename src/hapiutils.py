from hapiclient.hapitime import hapitime2datetime, datetime2hapitime
import numpy.lib.recfunctions as nrecfun
import numpy as np
import pandas as pd
import copy
from datetime import datetime, timedelta


def nparray_unpack_to_list(arr) -> list:
    if type(arr) == np.ndarray:
        return arr.tolist()
    else:
        return arr


def merge_dtypes(dataA, dataB, trim="Time"):
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


def hapi_to_df(dataA, round_to_sec=False, clean_time=False):
    # automatically 'cleans' hapitimes as well

    # if round_to_sec:
    #    dataA['Time'] = round_hapitime(dataA['Time'])

    has_multiD = False
    multiD = {}
    namelist = list(dataA.dtype.names)
    for name in dataA.dtype.names:
        try:
            if dataA[name].shape[1]:
                has_multiD = True
                multiD[name] = True
        except:
            multiD[name] = False

    if has_multiD:
        dfA = pd.DataFrame({"Time": dataA["Time"]})  # ,dtype='string')
        namelist.remove("Time")
        for name in namelist:
            if multiD[name]:
                # dfA[name] = pd.Series(dtype='object')
                dfA[name] = list(dataA[name])  # list or tuple work
                # dfA[name] = dataA[name].astype(object)
                # ",".join([str(val) for val in dataA[name]])
            else:
                dfA[name] = dataA[name]
    else:
        # easy case, all 1-D data so no fussing needed
        dfA = pd.DataFrame(dataA)

    # clean times
    dfA["Time"] = pd.to_datetime(
        dfA["Time"].str.decode("utf-8")
    )  # hapitime2datetime(np.array(dfA['Time']),**ops)
    if round_to_sec:
        dfA["Time"] = dfA["Time"].dt.round("S")
    dfA["Time"] = dfA["Time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return dfA


def merge_hapi(
    dataA, metaA, dataC, metaC, round_to_sec=False, fill_nan=False, join_all=True
):
    metaAC = copy.deepcopy(metaA)
    for ele in metaC["parameters"]:
        if ele["name"] != "Time" and (join_all or (ele not in metaA["parameters"])):
            # adjust both dataframe name and hapi metadata
            if ele in metaA["parameters"]:
                name = ele["name"]
                new_name = (
                    f"{name}_{metaC['x_dataset']}"  # does x_dataset always exist?
                )
                dataC = nrecfun.rename_fields(dataC, {name: new_name})
                ele["name"] = new_name
            metaAC["parameters"].append(ele)

    dfA = hapi_to_df(dataA, round_to_sec=round_to_sec)
    dfC = hapi_to_df(dataC, round_to_sec=round_to_sec)
    dt = merge_dtypes(dataA, dataC, trim="Time")
    dfAC = pd.merge_ordered(dfA, dfC)  # Works!

    # walk through dfAC and fill all numeric 'NaN' with 'fill' from meta
    if fill_nan:
        for ele in metaAC["parameters"]:
            name = ele["name"]
            try:
                if ele["fill"] != None:
                    fill = float(ele["fill"])
                    print("Filling with: ", fill, ele)
                    dfAC[name] = dfAC[name].fillna(fill)
            except:
                print("NO fill for ", ele["fill"], ele)
                pass

    newAC = dfAC.to_records(index=False, column_dtypes={"Time": "S30"})
    newAC = np.array(
        [tuple([nparray_unpack_to_list(e) for e in elm]) for elm in newAC], dtype=dt
    )
    newAC = np.array([tuple(i) for i in newAC], dtype=dt)

    return newAC, metaAC
