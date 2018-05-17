"""
swmmread.py
Read SWMM input file and create objects for each input category
Also read the resulting output file after SWMM is run
2013 Arthur McGarity
Swarthmore College
AEM: Modified 11/2015 to include LID categories in input file
JCOHEN4: Modified multiple times 2015 - 2016
AEM: Modified 4/21/2017 to add read_rpt() function to simply create a text string containing the contents
of the SWMM report file.  Then modify all other functions to accept the text string rather than a file name
so that we read the report file only once for each run
"""
#import sys

from swmm_objects_3 import *

def read_inp_file(fname):
  infile = open(fname,'r')
  inpFileStr = infile.read()
  infile.close()
  return(inpFileStr)

def read_inp(inpFileStr):
# read SWMM inp file fname into a large string
# create a list "section_names" containing the names of the sections found in the file
# create a dictionary "sections" containing the data lines found in each section keyed by section_name
# finally, return "section_names" and "sections"
# NOTE: the calling program is responsible for parsing the data lines in the sections


    data = inpFileStr.split('\n')   # convert the large string into a large list, one line per element
    section_names = []   # we will build this list from section names found in the SWMM .inp file
# remove comment lines and blank lines and identify all section names used in the file
    data1 = []
    for line in data:
        line_ns = line.strip()  # remove whitespace
        if line_ns.startswith('['):
            section_names.append(line_ns)
        elif line_ns.startswith(';;'):  # do not include comment ines
           continue
        elif not line_ns:  # do not include blank lines
           continue
        data1.append(line)  # data1 is a list containing the unstripped lines of the SWMM .inp file
# now find all data lines in each section, store each data line as an entry in a section_list
# then after reading all the data in a section, store the section_list in
# dictionary sections keyed by the section name
    sections = {}  # dictionary to hold all lines in a section, keyed by section_names
    end = False
    for i in range(len(data1)):
        line = data1[i]
        line_ns = line.strip()  # remove whitespace
        if line_ns in section_names:
            name = line_ns
            section_list = []
            try:
               next_line = data1[i+1]  # look ahead at next line
            except IndexError:
               end = True         # end of input file found
            next_line_ns = next_line.strip()  # remove whitespace
            if (end or (next_line_ns in section_names)):  # we have read the entire section
              sections[name] = section_list              # store the list in the dictionary
        else:
           section_list.append(line)    # store section data in section_list
           try:
               next_line = data1[i+1]  # look ahead at next line
           except IndexError:
               end = True
           next_line_ns = next_line.strip()  # remove whitespace
           if (end or (next_line_ns in section_names)):
              sections[name] = section_list  #populate the sections dictionary
#    for i in section_names:
#        sys.stdout.write("%s\n" % i)
#        for j in sections[i]:
#            sys.stdout.write(j)
    return((section_names,sections))  # return the section_names LIST and the sections DICTIONARY (keyed by items in the section_names list)

def greened_acres_deployed(swmmInpStr,lidDict):
  # takes a STRING containing contents of the INP file and returns the total number of greened acres
  # for each LID in lidDict
  (section_names,sections) = read_inp(swmmInpStr)
  model = swmm_model("Model",section_names,sections)
  lidSubcatNameList = model.getLidSubcatchmentNameList()
  totalGreenedAcreByLidDict = {}
  for lid in lidDict:
    totGrnAcr = 0.0
    greenedAcrePerLid = lidDict[lid]['GreenedAcres']
    for subcat in lidSubcatNameList:
      numLidStr = model.getLidNumber(subcat,lid)
      numLid = float(numLidStr)
      totGrnAcr += numLid*greenedAcrePerLid
    totalGreenedAcreByLidDict[lid] = totGrnAcr
  return totalGreenedAcreByLidDict



def read_outflow_series(rptFileStr):
  rptFileList = rptFileStr.split('\n')
  node_results = "Node Results"
  found_outfall = False
  dates = []  #empty lists to be appended with data
  times = []
  outflows = []
  for line in rptFileList:
    if node_results in line:    #starting in node results section
      found_outfall = True
    if found_outfall:
      line_list = line.split()
      if len(line_list) > 2:
        date = line_list[0] # get date from list
        ####   SWMM Version 5.10.10 used date format mmm-dd-yyyy (11 characters)
        ####   but SWMM Version 5.10.12 uses date format mm/dd/yyyy (10 characters)
        if len(date) == 11 or len(date) == 10:  #so that only node results section will be recorded
          dates.append(date)
          time = line_list[1] # get time from list
          times.append(time)
          outflow = line_list[2] #get outflow from list
          outflows.append(float(outflow))
  return (dates,times,outflows)

def read_runoff(rptFileStr):      # Returns annual runoff in INCHES
#  infile = open(fname,'r')
#  data = infile.read()
  outfall_start_index = rptFileStr.find('Runoff Quantity Continuity')
  output_start_index = rptFileStr.find('Surface ',outfall_start_index)
  split = rptFileStr[output_start_index:].split('\n',1)
  output_line = split[0]
  output_list = output_line.split()
  runoff = output_list[4]
  return float(runoff)

def read_evaporation(rptFileStr):    # Returns annual evaporation in INCHES
#  infile = open(fname,'r')
#  data = infile.read()
  outfall_start_index = rptFileStr.find('Runoff Quantity Continuity')
  output_start_index = rptFileStr.find('Evaporation',outfall_start_index)
  split = rptFileStr[output_start_index:].split('\n',1)
  output_line = split[0]
  output_list = output_line.split()
  evaporation = output_list[4]
  return float(evaporation)

def read_infiltration(rptFileStr):   # Returns annual infiltration in INCHES
#  infile = open(fname,'r')
#  data = infile.read()
  outfall_start_index = rptFileStr.find('Runoff Quantity Continuity')
  output_start_index = rptFileStr.find('Infiltration',outfall_start_index)
  split = rptFileStr[output_start_index:].split('\n',1)
  output_line = split[0]
  output_list = output_line.split()
  infiltration = output_list[4]
  return float(infiltration)

def read_precipitation(rptFileStr):   # Returns annual precipitation in INCHES
#  infile = open(fname,'r')
#  data = infile.read()
  outfall_start_index = rptFileStr.find('Runoff Quantity Continuity')
  output_start_index = rptFileStr.find('Total',outfall_start_index)
  split = rptFileStr[output_start_index:].split('\n',1)
  output_line = split[0]
  output_list = output_line.split()
  precipitation = output_list[4]
  return float(precipitation)


def read_rpt_file(fname):
  infile = open(fname,'r')
  rptFileStr = infile.read()
  infile.close()
  return(rptFileStr)

def read_report(rptFileStr):
  # find and parse the LID Performance Summary
  lid_start_index = rptFileStr.find('LID Performance Summary')
  if lid_start_index >= 0:   # The LID Performance Summary section is in the output file
    lid_subcatchment_heading_index = rptFileStr.find('Subcatchment',lid_start_index)
    remaining_lines = rptFileStr[lid_subcatchment_heading_index:].split('\n')
    #line_after_section = '  '
    i = 2
    lid_performance = []
    while True:
      if remaining_lines[i].strip() == '':   # Blank line found
        break
      lid_performance.append(remaining_lines[i])
      i = i + 1
    lid_dict = {}
    series_dict = {}
    for line in lid_performance:
      this_lid_dict = {}
      labels = ['Total Inflow', 'Evap Loss', 'Infil Loss', 'Surface Outflow', 'Drain Outflow',
                'Initial Storage', 'Final Storage', 'Continuity Error']
      wordlist = line.split()
      idx = wordlist[0] + ' ' + wordlist[1]   # string containing subcatchment name and lid name
      values = wordlist[2:]
      i = 0;
      for label in labels:
        this_lid_dict[label] = float(values[i])
        i += 1
      lid_dict[idx] = this_lid_dict  # suitable for storing in a MongoDB database
  else:
    lid_dict = None
    lid_report = None
  # find and parse the Outfall Loading Summary
  outfall_start_index = rptFileStr.find('Outfall Loading Summary')
  if outfall_start_index >= 0:   # The Outfall Loading Summary section is in the output file
    output_start_index = rptFileStr.find('System',outfall_start_index)
    split = rptFileStr[output_start_index:].split('\n',1)
    output_line = split[0]
    output_list = output_line.split()
    peakCFS = float(output_list[3])    # Outfall peak flow in cfs
    volumeMGAL = float(output_list[4])  # Outfall volume in 10^6 Gal
    runoffIN = read_runoff(rptFileStr)
    evaporationIN = read_evaporation(rptFileStr)
    infiltrationIN = read_infiltration(rptFileStr)
    precipitationIN = read_precipitation(rptFileStr)
    dates,times,outflow_seriesCFS = read_outflow_series(rptFileStr)  # ignore dates and times for now
    return {"peakCFS":peakCFS,"volumeMGAL":volumeMGAL,"runoffIN":runoffIN,"evapIN":evaporationIN,\
    "infilIN":infiltrationIN, "precipIN":precipitationIN,"lid_dict":lid_dict, "outflow_seriesCFS":outflow_seriesCFS}
    # values in this dictionary are STRINGS except lid_dict is a dictionary of dicts and outflow_seriesCFS is a list
  else:
    return "failed"
