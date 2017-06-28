# Locate cell tower from hand-off coordinates using the method of triangles/perimeters.
# Script determines perimeters of the largest triangles formed by 10 sets of 3 points,
# computes the coordinates of the center of the circle formed by each triangle, then
# uses the average circle center location as its estimate for the true center.
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
    
    if not isDuplicate:
        coordListUnique.append([currentLat, currentLon])

# Put the coordinates from coordListUnique into the numpy array coordArray
coordArray = np.zeros((len(coordListUnique), 2))
for i in range(len(coordListUnique)):
    coordArray[i,0] = coordListUnique[i][0]
    coordArray[i,1] = coordListUnique[i][1]
if verbose: print("Duplicate points removed!\n")

if debug: print(coordArray)

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
                print("{:d} / {:d} combinations ({:.1f}%) completed".format(
                    iteration, numCombinations, 100. * iteration / numCombinations)
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
                triList.sort(key=itemgetter(0), reverse=True)
            else:
                for index, entry in enumerate(triList):
                    if currentPerim > entry[0]:
                        triList.pop(index)
                        triList.insert(index, [currentPerim,coordArray[i,:],coordArray[j,:], coordArray[k,:]])
                        break

# Use the function getCircle(...) to compute the coordinates of the center of the circle
# generated by three arbitrary points, as well as the radius of the circle.
#   The center coordinates are computed as follows. First, use the three points
#   (x1, y1), (x2, y2), and (x3, y3) to write three equations for the circle:
#   (x1 - h)^2 + (y1 - k)^2 = r^2   (1)
#   (x2 - h)^2 + (y2 - k)^2 = r^2   (2)
#   (x3 - h)^2 + (y3 - k)^2 = r^2   (3)
#
#       where (h, k) are the coordinates of the center of the circle and r is its radius.
#
#   Subtract equation 2 from equation 1 to get an equation that eliminates r. Then subtract
#   equation 3 from equation 1 to get a second equation that eliminates r. The choices of
#   equations to subtract from one another are arbitrary; the goal is to obtain a system
#   of 2 equations containing the terms x1, x2, x3, y1, y2, y3, x, and h, eliminating r.
#
#   Then the system of equations can be written in the form Mx=b, where M is a 2x2 coefficient
#   matrix consisting of terms of x1, x2, x3, y1, y2, and y3; x is the solution vector [h, k];
#   and b is the ordinate vector consisting of terms of x1, x2, x3, y1, y2, and y3. In long form:
#
#   [A  B]  [h] =   [C]    
#   [D  E]  [k]     [F]
#
#   This system can be solved for h and k. After h and k have been determined, any one of the
#   equations 1, 2, or 3 can be used to determine r.
#
# Function getCircle(...) accepts three 1x2 numpy arrays: three pairs of (x,y) coordinates.
# Outputs a 3-tuple containing (h, k, r).
def getCircle(p1, p2, p3):
    lat1 = p1[0]
    lon1 = p1[1]
    lat2 = p2[0]
    lon2 = p2[1]
    lat3 = p3[0]
    lon3 = p3[1]

    # TODO: CHECK FOR COLLINEARITY

    A = lat2 - lat1
    B = lon2 - lon1
    C = -0.5 * (sqr(lat1) - sqr(lat2) + sqr(lon1) - sqr(lon2))
    D = lat3 - lat1
    E = lon3 - lon1
    F = -0.5 * (sqr(lat1) - sqr(lat3) + sqr(lon1) - sqr(lon3))
    
    circleOrigin = np.linalg.lstsq(np.array([[A, B], [D, E]]), np.array([[C], [F]]))
    h = circleOrigin[0][0]
    k = circleOrigin[0][1]

    r = math.sqrt(sqr(lat1 - h) + sqr(lon1 - k))
    return (h, k, r)

# Compute the center and radius of the points formed by each of the above triangles.
# Array column 0 = latitude (h), 1 = longitude (k), 2 = radius (r)
triCircles = np.zeros((numTriangles, 3))
for i in range(numTriangles):
    circleCoords = getCircle(triList[i][1], triList[i][2], triList[i][3])
    triCircles[i,0] = circleCoords[0]
    triCircles[i,1] = circleCoords[1]
    triCircles[i,2] = circleCoords[2]

# Plot points as blue dots.
fig, ax = plt.subplots()
ax.plot(coordArray[:,1], coordArray[:,0], 'bo')

# Plot triangles and circles formed by triangles in red.
# Simultaneously compute average circle center coords and average radius.
circleResolution = 100  # number of points used to construct (the circumference) of circles
theta = np.linspace(0, 2*PI, circleResolution)
circleCircumferencePoints = np.zeros((circleResolution, 2))

sumLats = 0
sumLons = 0
sumRadii = 0
numToAverage = 0
for i in range(numTriangles):
    # Plot triangle
    ax.plot([triList[i][1][1], triList[i][2][1], triList[i][3][1]],
        [triList[i][1][0], triList[i][2][0], triList[i][3][0]], 'r-')

    # Plot circle center
    h = triCircles[i,0]
    k = triCircles[i,1]
    r = triCircles[i,2]
    ax.plot(k, h, 'r+')

    # Plot circle
    for j in range(circleResolution):
        circleCircumferencePoints[j,0] = k + r * math.sin(theta[j])
        circleCircumferencePoints[j,1] = h + r * math.cos(theta[j])

    ax.plot(circleCircumferencePoints[:,0], circleCircumferencePoints[:,1], 'r-')

    # Remove outliers/unrealistically large circles from average.
    if r <= 0.25:
        numToAverage += 1
        sumLats += h
        sumLons += k
        sumRadii += r

# Compute average center and radius.
avgLat = sumLats / numToAverage
avgLon = sumLons / numToAverage
avgRad = sumRadii / numToAverage

# Plot average circle center and radius in black.
ax.plot(avgLon, avgLat, 'kx', lw=2)
for j in range(circleResolution):
    circleCircumferencePoints[j,0] = avgLon + avgRad * math.sin(theta[j])
    circleCircumferencePoints[j,1] = avgLat + avgRad * math.cos(theta[j])
ax.plot(circleCircumferencePoints[:,0], circleCircumferencePoints[:,1], 'k-', lw=2)

print("Center: ({:f}, {:f}). Radius: {:f}\n".format(avgLat, avgLon, avgRad))
#ax.invert_yaxis()
#ax.invert_xaxis()
plt.show()
