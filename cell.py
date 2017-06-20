# Locate cell tower from hand-off coordinates
debug = False
debugConstants = False

import math
import numpy as np
import csv
import argparse
import matplotlib.pyplot as plt

PI = math.pi

# Define square function; improves code readability
def sqr(val):
    return val * val

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str)
parser.add_argument("-p", "--percent", type=float, default=0.9, help="Percentage of points (as a decimal) that" +
    " must be encompassed by minRadius. Must be between 0 and 1.0. Default 0.9")
args = vars(parser.parse_args())
fileName = args["filename"]
minPerc = args["percent"]

# Import tab-delimited text file of lat and long coords into an M x 2 array of coordinates,
# where [m,0] corresponds to the latitude of a particular point m and [m,1] corresponds
# to the longitude of a particular point m, and there are M total points.

# coordList will be the array containing M rows, where column 0 corresponds to the
# latitude of a point and column 1 corresponds to the longitude of a point.
# Since these are imported from a text file, the values are strings. They will be
# copied into the array coordArray as floats.
with open(fileName) as logFile:
    gpsReader = csv.reader(logFile, delimiter='\t')
    coordList = list(gpsReader)
 
# Check for and remove duplicate points.
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

coordArray = np.zeros((len(coordListUnique), 2))
for i in range(len(coordListUnique)):
    coordArray[i,0] = coordListUnique[i][0]
    coordArray[i,1] = coordListUnique[i][1]

if debug:
    print(coordArray)

# Initialize variables
# Matrix coefficients A, B, C, D, E, F
A = 0
B = 0
C = 0
D = 0
E = 0
F = 0

# Latitude and longitude of point 1, point 2, point 3
lat1 = 0
lon1 = 0
lat2 = 0
lon2 = 0
lat3 = 0
lon3 = 0

# Latitude and longitude of the origin of the circle formed by any 3 points, as
# well as the radius of the circle.
circleOrigin = np.zeros((1,2))
lat0 = 0
lon0 = 0
radius = 0

# Determine "centroid" of point distribution, then compute the minimum radius of
# the circle, centered at the centroid, necessary to capture <= 90% of the points.
numPoints = len(coordArray[:,0])
sumLats = 0     # running total (sum) of the latitude values
sumLons = 0     # running total (sum) of the longitude values

if debug: print("numPoints = {:d}\n".format(numPoints))

# First, determine the "centroid" of the points (centroid of latitude, centroid of longitude).
for i in range(numPoints):
    sumLats += coordArray[i,0]
    sumLons += coordArray[i,1]

latCentroid = sumLats / numPoints
lonCentroid = sumLons / numPoints

if debug: print("Centroid = ({:f}, {:f})\n".format(latCentroid, lonCentroid))


# To avoid repeated calculation, create a list containing the distance of each point
# from the centroid. Sort list in numerical order. Determine requisite radius.
pointDistance = 0       # Initialize point distance variable
pointDistList = []      # Initialize list

# Iterate through the points to compute the distance of each point from the centroid. Add
# each distance to the list of distances.
for i in range(numPoints):
    pointDistance = math.sqrt(sqr(coordArray[i,0] - latCentroid) + sqr(coordArray[i,1] - lonCentroid))
    pointDistList.append(pointDistance)

# Sort list in numerical order, from least to greatest
pointDistList.sort()

if debug: print(pointDistList)
# Determine the distance (radius) that represents the 90th percentile of the sorted list values. I.e., the
# minRadius is the radius that contains 90% of all points, measured from the centroid.
minRadius = pointDistList[int(minPerc * numPoints - 1)]

# Set a max radius to preclude results that may be unrealistically far away.
maxRadius = 1.2 * pointDistList[-1]

if debug: print("minRadius = {:f}, maxRadius = {:f}\n".format(minRadius, maxRadius))

# Triple nested for-loop, where first loop corresponds to first point, second
# loop corresponds to second point, and third loop corresponds to third point.
# If a set of 3 points whose computed radius >= minRadius, then the boolean minRadiusAchieved is
# set to True and the triple for-loop is exited.
minRadiusAchieved = False

for i in range(len(coordArray[:,0]) - 2):
    if minRadiusAchieved == True:
        break

    lat1 = coordArray[i,0]
    lon1 = coordArray[i,1]
    for j in range(i+1, len(coordArray[:,0]) - 1):
        if minRadiusAchieved == True:
            break

        lat2 = coordArray[j,0]
        lon2 = coordArray[j,1]
        for k in range(j+1, len(coordArray[:,0])):
            if minRadiusAchieved == True:
                break

            # Check if any pair of points is identical
            if ((lat1==lat2) and (lon1==lon2)) or ((lat1==lat3) and (lon1==lon3)) or ((lat2==lat3) and (lon2==lon3)):
                continue

            
            lat3 = coordArray[k,0]
            lon3 = coordArray[k,1]
            
            if debugConstants:
                print("i={:d}, j={:d}, k={:d}".format(i, j, k))
                print("lat1={:f}, lon1={:f}\nlat2={:f}, lon2={:f}\nlat3={:f}, lon3={:f}".format(
                    lat1, lon1, lat2, lon2, lat3, lon3))

            # TODO: Check for collinearity (in the unlikely event that the three points form a line).
            # Formulate each point as a vector.
            R1 = np.array([[lat1, lon1, 0]])
            R2 = np.array([[lat2, lon2, 0]])
            R3 = np.array([[lat3, lon3, 0]])
            
            # Define matrix coefficients for this particular set of points (see equations).
            A = lat2 - lat1
            B = lon2 - lon1
            C = -0.5 * (sqr(lat1) - sqr(lat2) + sqr(lon1) - sqr(lon2))
            D = lat3 - lat1
            E = lon3 - lon1
            F = -0.5 * (sqr(lat1) - sqr(lat3) + sqr(lon1) - sqr(lon3))

            if debugConstants:
                print("A={:.3f}, B={:.3f}, C={:.3f}, D={:.3f}, E={:.3f}, F={:.3f}\n".format(A, B, C, D, E, F))

            # Solve for the coordinates of the origin of the circle formed by the 3 points.
            # NOTE: linalg.lstsq solves for {h, k}; circleOrigin[0,0] = h, and circleOrigin[1,0] = k.
            # NOTE: lat0 refers to h, and lon0 refers to k.
            circleOrigin = np.linalg.lstsq(np.array([[A, B], [D, E]]), np.array([[C], [F]]))
            lat0 = circleOrigin[0][0]
            lon0 = circleOrigin[0][1]
            
            # Compute the radius of the circle
            radius = math.sqrt(sqr(lat1 - lat0) + sqr(lon1 - lon0))
            
            # If radius >= minRadius, set minRadiusAchieved = True.
            if (radius >= minRadius) and (radius < maxRadius):
                minRadiusAchieved = True

points = plt.plot(coordArray[:,0], coordArray[:,1], 'bo')
plt.plot(latCentroid, lonCentroid, 'g+')

if minRadiusAchieved == True:
    lat0 = float(lat0)
    lon0 = float(lon0)
    theta = np.linspace(0, 2*PI, 100)
    circleCoords = np.zeros((100, 2))
    for i in range(len(theta)):
        circleCoords[i,0] = lat0 + (radius * math.cos(theta[i]))
        circleCoords[i,1] = lon0 + (radius * math.sin(theta[i]))
    
    plt.plot(lat0, lon0, 'rx')
    plt.plot(circleCoords[:,0], circleCoords[:,1], 'r-')
    print("Center located at latitude {:f}, longitude {:f}. Radius = {:f}".format(lat0, lon0, radius))
else:
    print("Center could not be located. Try reducing precision of radius.")

plt.show()
