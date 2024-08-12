# tools-python
Additional tools to support hapiclient, including merge, etc.  Currently consists of 'merge_hapi()' and 'hapi_to_df()'.  Cloud HAPI coming soon.  Assuming you have fetched 2 HAPI datasets and their metadata using hapiclient ( dataA, metaA and dataB, metaB):

    merged_data, merged_meta = hapiutils.merge_hapi(dataA, metaA, dataB, metaB, round_to_sec=True)

Useful to feed into hapi-nn (see https://github.com/hapi-server/application-neuralnetwork-python)

Also, you can cast HAPI data into a Pandas dataframe with:

    hapidf = hapi_to_df(dataA)

Full example:

    from hapiclient import hapi
    from hapiplot import hapiplot
    import hapiutils

    opts = {'logging': False, 'usecache': True, 'cachedir': './hapicache' }
    start      = '2013-01-01T00:00:54Z'
    stop       = '2013-01-01T06:00:54.000Z'
    serverA, datasetA, parametersA = 'https://cdaweb.gsfc.nasa.gov/hapi', 'OMNI2_H0_MRG1HR', 'DST1800'
    serverB, datasetB, parametersB = "https://imag-data.bgs.ac.uk/GIN_V1/hapi", "cki/best-avail/PT1M/hdzf", "Field_Vector"

    dataA, metaA = hapi(serverA, datasetA, parametersA, start, stop, **opts)
    dataB, metaB = hapi(serverB, datasetB, parametersB, start, stop, **opts)
    newAB, metaAB = hapiutils.merge_hapi(dataA, metaA, dataB, metaB, True)
    hapiplot(newAB, metaAB)
