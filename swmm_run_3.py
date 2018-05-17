#from swmm_objects import *
from swmm_read_3 import *
from subprocess import call
from datetime import datetime
from random import uniform

def random_interval(lowFract,highFract):
    r1 = uniform(lowFract,highFract)
    r2 = uniform(lowFract,highFract)
    if r1 > r2:
        upper = r1
        lower = r2
    else:
        lower = r1
        upper = r2
    rangeDict = {}
    rangeDict["lower"] = lower
    rangeDict["upper"] = upper
    return rangeDict


def runswmm(swmmInpFileNameStr,swmmRptFileNameStr):
    # Create dictionary to store starting datetime and elapsed time to run the model
    timeStatsDict = {}
    # Run the SWMM input file
    startTime = datetime.now()   # obtain the starting time of the run
    startTimeStr = str(startTime)
    call(["swmm5.exe", swmmInpFileNameStr, swmmRptFileNameStr])
    endTime = datetime.now()   # obtain the ending time of the run
    elapsedTime = endTime - startTime
    minAndSec = divmod(elapsedTime.total_seconds(), 60)
    elapsedTimeStr = "%s min, %0.2f sec" % minAndSec
    timeStatsDict['startTimeStr'] = startTimeStr
    timeStatsDict['elapsedTimeStr'] = elapsedTimeStr
    print(elapsedTimeStr)
    return timeStatsDict

def total_impervious_area(swmmInpFileNameStr):  
  # Takes the INP FILE NAME, reads the file, calc. total imperv area
  swmmInpStr = read_inp_file(swmmInpFileNameStr)
  (section_names,sections) = read_inp(swmmInpStr)
  model = swmm_model("Model",section_names,sections) 
  subcatNameList = model.getSubcatchmentNameList() 
  totalImpervArea = 0.0
  for subcat in subcatNameList:
      subcatArea = model.getSubcatchmentArea(subcat)
      pctImperv = model.getSubcatchmentPctImperv(subcat)
      subcatImpervArea = subcatArea*pctImperv/100.0
      totalImpervArea += subcatImpervArea
  return totalImpervArea

def cso_reduction_and_greened_acres(lid,swmmRptDict,lidDict,thresholdOutflowCFS,zeroLIDCSOVolumeMGal):
  swmmInputFileStr = swmmRptDict["swmmInpFileStr"]   # retrieve the SWMM inp file used for this run as string
  totalGreenedAcreByLidDict = greened_acres_deployed(swmmInputFileStr,lidDict) # extract greened acres for each LID
  csoVolumeMgal = get_cso_volume_mgal(swmmRptDict,thresholdOutflowCFS)
  csoReductionMgal = zeroLIDCSOVolumeMGal - csoVolumeMgal
  greenedAcres = totalGreenedAcreByLidDict[lid]
  return greenedAcres, csoReductionMgal

def run_swmm_and_return_results(swmmInpFileStr):
    f = open("SWMM_modified.inp",'w')
    f.write(swmmInpFileStr)  # write out the swmmInputFileStr for modified problem
    f.close()   
    timeStatsDict = runswmm("SWMM_modified.inp","SWMM_modified.rpt")
    swmmRptFileStr = read_rpt_file("SWMM_modified.rpt")
    swmmRptDict = read_report(swmmRptFileStr)
    if type(swmmRptDict) is dict:
        # Augment the report returned by read_report() for storage in database
        swmmRptDict["timeStatsDict"] = timeStatsDict  # report when run and how much time
        swmmRptDict["swmmInpFileStr"] = swmmInpFileStr # store the input file
        swmmRptDict["swmmRptFileStr"] = swmmRptFileStr # store the output file
        return swmmRptDict
    else:
        return {'SWMM ERROR: SEE RPT FILE'}


def calculate_cso(outflowCFSList, thresholdCFS):  # for 15 minute flow data in cfs
    csoFlow = 0
#    hours = 0
    for outflowCFS in outflowCFSList: 
        if outflowCFS > thresholdCFS:  #threshold method--- 
            csoCFS = outflowCFS - thresholdCFS # subtracting treated from total outflow
            csoFlow += csoCFS 
#            hours += 1
    csoVolumeMGal = csoFlow*900*7.48052/1.0e6 # Million Gallons for seconds in 15 minutes
    return csoVolumeMGal

def get_cso_threshold(swmmInpFileNameStr, treatmentRatio):
    watershedImpervAreaAcre = total_impervious_area(swmmInpFileNameStr)
    thresholdOutflowCFS = treatmentRatio*watershedImpervAreaAcre
    return thresholdOutflowCFS

def get_cso_volume_mgal(runDict,thresholdOutflowCFS):
    outflowCFSList = runDict["outflow_seriesCFS"]
    csoVolumeMGal = calculate_cso(outflowCFSList,thresholdOutflowCFS)
    return csoVolumeMGal


