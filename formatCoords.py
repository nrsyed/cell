############################################################################################################
# Name: formatCoords.py
#
# Description: Process the text file output of Tasker cell tower CDMA data (for Tasker
#   information/documentation, see http://tasker.dinglisch.net/). Tasker output should be a delimited
#   text file containing the CDMA value, latitude, and longitude. Any delimiter may be used and the
#   columns may be in any order--specify the relevant columns with the corresponding options (see
#   below). If the Tasker output file contains a header row, or if the first N rows are to be
#   skipped, use the option --first-line with the value 1 or (N-1), respectively.
#   
#   This script outputs the latitude and longitude of each point in a tab-delimited text file.
#
# Author: Najam Syed
# Created:  2017-06-18
# Modified:
#           2017-06-25
#           2017-07-06  Added functionality for parsing files in current directory. INCOMPLETE.
#
############################################################################################################

import argparse
import csv
import types
import os
import re   # regex

# IN THE COMMAND LINE, RUN THIS SCRIPT WITH THE OPTION -h TO PRINT HELP MESSAGE. EXAMPLE:
# >> python formatCoords.py -h


# Configure the command line argument parser
parser = argparse.ArgumentParser()

parser.add_argument("input-file", help="File name of the desired file (required)")
parser.add_argument("-n", "--cdma-number", default=0, help="The CDMA of the desired cell tower; default 0")
parser.add_argument("-d", "--delim", type=str, help="Delimiter. For the following special characters:\n" +
    "sp (space)\ttab (tab)\tcr (carriage return)\tnl (newline). Default character is tab.")
parser.add_argument("-c", "--cdma-index", default="2",
     help="The column index that contains the tower CDMA (first column = 0); default 2")
parser.add_argument("-a", "--latitude-index", default=3,
    help="The column index that contains the latitude (first column = 0); default 3")
parser.add_argument("-o", "--longitude-index", default=4,
    help="The column index that contains the longitude (first column = 0); default 4")
parser.add_argument("-f", "--first-line", default=0,
    help="The row index where actual data begins (first row = 0); default 0")
parser.add_argument("-X", "--extract-all", action='store_true',
    help="Extract all CDMAs from the file. Create a text file containing formatted coordinates for each CDMA found.")
parser.add_argument("-D", "--destination", help="Choose the directory where the text file(s) will be placed.")

args = vars(parser.parse_args())

# Set the delimiter
if type(args["delim"]) is types.NoneType:
    delim = "\t"
elif args["delim"] == "tab":
    delim = "\t"
elif args["delim"] == "cr":
    delim = "\r"
elif args["delim"] == "nl":
    delim = "\n"
elif args["delim"] == "sp":
    delim = " "
else:
    delim = args["delim"]

# Set other parameters
cdmaInd = int(args["cdma_index"])
latInd = int(args["latitude_index"])
lonInd = int(args["longitude_index"])
firstLine = int(args["first_line"])

cdma = int(args["cdma_number"])

# Get list of directory contents
directoryContents = os.listdir(os.getcwd())

# Get list of existing formatted coordinate CSV text files in the directory, ie, files that
# match the pattern "[CDMA number]-[file number].txt".
existingFiles = list()
for string in directoryContents:
    fileRegEx = re.search('^[0-9]+-[0-9]+\.txt', string)
    if type(fileRegEx) is not types.NoneType:
        existingFiles.append(fileRegEx.group(0))

# From the filename strings in the list existingFiles, get all unique CDMAs that are
# represented, as well as the largest instance number for each CDMA, and put in cdmaList.
# For example, if existingFiles (and the directory) contains the following:
#   ['385-1.txt', '385-2.txt', '385-3.txt', '832-1.txt', '832-4.txt']
# then the following will be put into cdmaList:
#   [[385, 3], [832, 4]]
#
# Note that cdmaList[0][0] would return the CDMA value of the first unique CDMA, 385.
# cdmaList[0][1] would return the largest instance number, 3, for CDMA 385.
#
# Iterate through existingFiles and evaluate each filename.
cdmaList = list()
currentCdmaFromFilename = 0   # CDMA from string converted to an int; check if already in cdmaList
currentCdmaInstance = 0     # CDMA instance number
alreadyInCdmaList = False   # true if current CDMA is already in cdmaList, else false
charIndex = 0
for fileNameStr in existingFiles:
    alreadyInCdmaList = False

    # Determine index of hyphen "-" in the filename string 
    for charIndex, char in enumerate(fileNameStr):
        if char == '-': break

    hyphenIndex = charIndex
    currentCdmaFromFilename = int(fileNameStr[:hyphenIndex])
        
    # Determine index of period from ".txt". Indices of hyphen and period will
    # be used to extract instance number from filename.
    for charIndex, char in enumerate(fileNameStr):
        if char == '.': break

    dotIndex = charIndex
    currentCdmaInstance = int(fileNameStr[(hyphenIndex + 1):dotIndex])

    # Check if current CDMA is already represented in cdmaList
    for cdmaListIndex in range(len(cdmaList)):
        if cdmaList[cdmaListIndex][0] == currentCdmaFromFilename:
            alreadyInCdmaList = True
            break

    # If current CDMA not in list, append CDMA and instance number to list.
    # Else, if current CDMA is already in list, check if current instance
    # number is larger than instance number in list. Replace if it is larger.
    if not alreadyInCdmaList:
        cdmaList.append([currentCdmaFromFilename, currentCdmaInstance])
    else:
        if currentCdmaInstance > cdmaList[cdmaListIndex][1]:
            cdmaList[cdmaListIndex][1] = currentCdmaInstance

# Function getCDMA(...) extracts the relevant data for a given CDMA value, then writes it to
# a text file in a standardized format.
def getCDMA(cmdaNum):
    # Import Tasker data
    with open(args["input-file"]) as fileName:
        reader = csv.reader(fileName, delimiter=delim)
        fileContents = list(reader)

    # Extract the relevant information and put into the list 'coordList'
    # The cells in the CDMA column contain a string formatted as "CDMA:000" where "000" is the relevant number.
    #   The code "int(fileContents[j][cdmaInd][5:])" extracts the number from the string (char 5 to end) in row
    #   j of the list fileContents, and converts it to an int.
    # The latitude and longitude are converted from str to float and appended to coordList if the CDMA matches.

    coordList = list()   # Initialize coordList
    for j in range(firstLine, len(fileContents)):
        # try/except statement handles case where the CDMA is not an integer by continuing to the next iteration
        try:
            if int(fileContents[j][cdmaInd][5:]) == cdma:
                coordList.append([float(fileContents[j][latInd]), float(fileContents[j][lonInd])])
        except:
            pass

    # Check if coordList empty.
    if len(coordList) == 0:
        print("No matching CDMA entries found. Exiting.")
        exit()

    # If coordList not empty, write contents to file.
    outputPath = str(cdma) + ".txt"
    with open(outputPath, "w") as output:
        writer = csv.writer(output, lineterminator='\n', delimiter='\t')
        for k in range(len(coordList)):
            writer.writerow(coordList[k])

    print("File " + outputPath + " successfully written.")
