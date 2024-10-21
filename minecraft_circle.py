import math

# input variables
points = 8
min_length = 3
max_length = 10
tolerance = 0.1


# process variables
degree_step = 360 / points
accepted_points = []
for i in range(points):
    accepted_points.append([])


# checking for acceptable points

