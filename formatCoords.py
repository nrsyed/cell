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
# Created: 2017-06-18
#
############################################################################################################

import argparse
import csv
import types

# IN THE COMMAND LINE, RUN THIS SCRIPT WITH THE OPTION -h TO PRINT HELP MESSAGE. EXAMPLE:
# >> python formatCoords.py -h


# Configure the command line argument parser
parser = argparse.ArgumentParser()

parser.add_argument("input-file", help="File name of the desired file (required)")
parser.add_argument("-d", "--delim", type=str, help="Delimiter. For the following special characters:\n" +
    "sp (space)\ttab (tab)\tcr (carriage return)\tnl (newline). Default character is tab.")
parser.add_argument("-c", "--cdma-index", default="2", help="The column index that contains the tower CDMA (first column index = 0); default 2")
parser.add_argument("-a", "--latitude-index", default=3, help="The column index that contains the latitude (first column index = 0); default 3")
parser.add_argument("-o", "--longitude-index", default=4, help="The column index that contains the longitude (first column index = 0); default 4")
parser.add_argument("-f", "--first-line", default=0, help="The row index where actual data begins (first row index = 0); default 0")
parser.add_argument("-n", "--cdma-number", default=385, help="The CDMA of the desired cell tower; default 385")

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
outputPath = str(cdma) + "_coords.txt"
with open(outputPath, "w") as output:
    writer = csv.writer(output, lineterminator='\n', delimiter='\t')
    for k in range(len(coordList)):
        writer.writerow(coordList[k])

print("File " + outputPath + " successfully written.")
