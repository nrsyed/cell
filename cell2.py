# Locate cell tower from hand-off coordinates using the method of triangles/perimeters.
# Script is currently incomplete--determines the x number of triangles from the list of
# points with the largest perimeters and prints them to the console.
debug = False

import math
import numpy as np
import csv
import argparse
import matplotlib.pyplot as plt
from operator import itemgetter
import time

PI = math.pi

# Define square function; improves code readability
def sqr(val):
    return val * val

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str)
args = vars(parser.parse_args())
fileName = args["filename"]
verbose = True

# Import tab-delimited text file of lat and long coords into an M x 2 array of coordinates,
# where [m,0] corresponds to the latitude of a particular point m and [m,1] corresponds
# to the longitude of a particular point m, and there are M total points.

# coordList will be the array containing M rows, where column 0 corresponds to the
# latitude of a point and column 1 corresponds to the longitude of a point.
# Since these are imported from a text file, the values are strings. They will be
# copied into the array coordArray as floats.
if verbose: print("Importing file... ")
with open(fileName) as logFile:
    gpsReader = csv.reader(logFile, delimiter='\t')
    coordList = list(gpsReader)
if verbose: print("File imported!\nRemoving duplicate points... ")

# Remove duplicate points.
coordListUnique = list()        # list to hold all unique points
isDuplicate = False
for i in range(len(coordList)):
    # Get the current latitude and longitude from coordList.
    # Loop through coordListUnique to check if the point (currentLat, currentLon) already exists.
    isDuplicate = False
    currentLat = float(coordList[i][0])
    currentLon = float(coordList[i][1])
    for j in range(len(coordListUnique)):
        if (coordListUnique[j][0] == currentLat) and (coordListUnique[j][1] == currentLon):
            isDuplicate = True
            break
    
    if isDuplicate:
        continue
    else:
        coordListUnique.append([currentLat, currentLon])

# Put the coordinates from coordListUnique into the numpy array coordArray
coordArray = np.zeros((len(coordListUnique), 2))
for i in range(len(coordListUnique)):
    coordArray[i,0] = coordListUnique[i][0]
    coordArray[i,1] = coordListUnique[i][1]
if verbose: print("Duplicate points removed!\n")

if debug:
    print(coordArray)

# Find the numTriangles sets of three points that form the triangles with the largest perimeters.
# These sets and their perimeters will be stored in the list triList.
numTriangles = 10       # The number of sets of points.
triList = list()
currentPerim = 0        # Variable to store perimeter during each loop iteration

# Define function perimeter() to compute perimeter of the triangle formed by 3 points. Accepts
# three numpy 1x2 arrays and outputs a single scalar value.
def perimeter(point1, point2, point3):
    side1 = np.linalg.norm(point2 - point1)
    side2 = np.linalg.norm(point3 - point1)
    side3 = np.linalg.norm(point3 - point2)
    return side1 + side2 + side3

numPoints = len(coordArray[:,0])
numCombinations = math.factorial(numPoints) / (math.factorial(numPoints - 3) * math.factorial(3))
if verbose:
    print("Preparing to compute triangle perimeters. There are {:d} points".format(numPoints) +
        " and {:d} possible combinations.\n".format(numCombinations))
    
iteration = 0       # var to track iterations
initialTime = time.time() 
currentTime = initialTime
for i in range(len(coordArray[:,0]) - 2):
    for j in range(i+1, len(coordArray[:,0]) - 1):
        for k in range(j+1, len(coordArray[:,0])):
            iteration += 1
            if verbose==True and iteration % 500000 == 0:
                lastTime = currentTime
                currentTime = time.time()
                timeSinceLast = currentTime - lastTime
                rate = 500000 / timeSinceLast
                timeLeft = (numCombinations - iteration) / rate
                print("{:d} / {:d} combinations completed".format(iteration, numCombinations)
                    + " in {:.3f} seconds. ".format(currentTime - initialTime)
                    + "Estimated {:.3f} seconds remaining.\n".format(timeLeft))

            currentPerim = perimeter(coordArray[i,:], coordArray[j,:], coordArray[k,:])
            
            # Check length of triList. If it doesn't already have numTriangles values in
            # it, simply append currentPerim and the current set of points to the list,
            # then sort the list. Otherwise, check if currentPerim is greater than any
            # of the perimeters currently in the list; if it is, remove the appropriate
            # value, then insert currentPerim in its spot.
            if len(triList) < numTriangles:
                triList.append([currentPerim, coordArray[i,:], coordArray[j,:], coordArray[k,:]])
                # Sort by first index of the entries in triList; ascending order
                triList.sort(key=itemgetter(0))
            else:
                for index, entry in enumerate(triList):
                    if currentPerim > entry[0]:
                        triList.pop(index)
                        triList.insert(index, [currentPerim,coordArray[i,:],coordArray[j,:], coordArray[k,:]])
                        break

for entry in triList:
    print(entry)
