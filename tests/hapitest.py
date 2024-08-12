from hapiclient import hapi
from hapiplot import hapiplot
import hapiutils

opts = {'logging': False, 'usecache': True, 'cachedir': './hapicache' }
server     = 'https://cdaweb.gsfc.nasa.gov/hapi'

datasetA = 'NOAA19_POES-SEM2_FLUXES-2SEC'
datasetB = 'NOAA18_POES-SEM2_FLUXES-2SEC'
parametersA = 'lat,lon,br_sat,bp_sat'
parametersB = 'lat,lon,br_sat,bp_sat'
parametersC = 'br_foot,bp_foot'
parametersD = 'br_sat,bt_sat'
start      = '2013-01-01T00:00:54Z' # min 2013-01-01T00:00:54Z
stop       = '2013-01-01T06:00:54.000Z' # max 2024-06-11T10:35:15Z
serverS     = 'http://ec2-54-92-164-109.compute-1.amazonaws.com:8000/hapi'
datasetS    = "data_CKI"
startS      = '2024-05-10T00:00:00Z' # Start and stop times
stopS       = '2024-05-13T00:00:00Z'
parametersS = 'N'   # blank means all parameters
serverO     = 'https://cdaweb.gsfc.nasa.gov/hapi'
datasetO    = 'OMNI2_H0_MRG1HR'
parametersO = 'DST1800'
serverI = "https://imag-data.bgs.ac.uk/GIN_V1/hapi"
datasetI = "cki/best-avail/PT1M/hdzf"
parametersI="Field_Vector"

dataA, metaA = hapi(server, datasetA, parametersA, start, stop, **opts)
dataC, metaC = hapi(server, datasetB, parametersC, start, stop, **opts)
dataD, metaD = hapi(server, datasetB, parametersD, start, stop, **opts)
#dataS, metaS = hapi(serverS, datasetS, parametersS, startS, stopS, **opts)
dataO, metaO = hapi(serverO, datasetO, parametersO, startS, stopS, **opts)
dataI, metaI = hapi(serverI, datasetI, parametersI, startS, stopS, **opts)

dataA=dataA[0:10]
dataC=dataC[0:10]
dataD=dataD[0:10]
#dataS=dataS[0:10]
dataO=dataO[0:10]
dataI=dataI[0:10]

choice = input("Test case AC, AD, CD, AS, AO, AI, SO, SI, OI: ")
if choice == "AC":
    newAC, metaAC = hapiutils.merge_hapi(dataA, metaA, dataC, metaC, True)
elif choice == "AD":
    newAC, metaAC = hapiutils.merge_hapi(dataA, metaA, dataD, metaD, True)
elif choice == "CD":
    newAC, metaAC = hapiutils.merge_hapi(dataC, metaC, dataD, metaD, True)
elif choice == "AS":
    newAC, metaAC = hapiutils.merge_hapi(dataA, metaA, dataS, metaS, True)
elif choice == "AI":
    newAC, metaAC = hapiutils.merge_hapi(dataA, metaA, dataI, metaI, True)
elif choice == "AO":
    newAC, metaAC = hapiutils.merge_hapi(dataA, metaA, dataO, metaO, True)
elif choice == "SO":
    newAC, metaAC = hapiutils.merge_hapi(dataS, metaS, dataO, metaO, True)
elif choice == "SI":
    newAC, metaAC = hapiutils.merge_hapi(dataS, metaS, dataI, metaI, True)
elif choice == "OI":
    newAC, metaAC = hapiutils.merge_hapi(dataO, metaO, dataI, metaI, True)
else:
    exit()
print("\nMerged:",newAC[0:3])
print(metaA['parameters'])
hapiplot(newAC, metaAC)
