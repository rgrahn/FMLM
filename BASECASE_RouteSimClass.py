from BASECASE_RouteRiderVanClass import *
import networkx as nx
import datetime as dt
import time
import numpy as np

class Sim(object):
    def __init__(self, startTime, vehicles, riders, graph, timeDict, waitCoeff, driveCoeff):
        self.time = startTime # Start time is at 6:00am
        self.vehiclesDict = vehicles
        self.vehicles = [ ]
        self.remainingRiders = riders
        self.dailyRiders = riders
        self.graph = graph
        self.systemQueue = [ ]
        self.timeDict = timeDict
        self.waitCoeff = waitCoeff    # For wait times at Ikea
        self.driveCoeff = driveCoeff  # For in-vehicle times

    # Define time step (assume 1 seconds)  
    def step(self):
        self.time += 5
        
    # Convert time to a timeperiod (e.g., 15min time intervals)
    def getTimePeriod(self, timeString):
        timeInterval = 15
        timePeriod = dt.datetime.strptime(timeString, '%H:%M:%S').time()
        timePeriod = str(timePeriod.replace(minute = timeInterval*(timePeriod.minute//timeInterval), second = 0))
        return timePeriod

    # Converts seconds to time string
    def convertSecondsToTimeString(self, seconds):
        hours = str(int(seconds//3600))
        minutes = str(int((seconds%3600)//60))
        if len(hours) < 2:
            hours = '0' + hours
        if len(minutes) < 2:
            minutes = '0' + minutes
        secs = '00'
        return ':'.join([hours, minutes, secs])

    # Activate vans based on their start times
    def activateVans(self):
        for veh, startTime in self.vehiclesDict.items():
            if (startTime <= self.time) and ((startTime + 5) > self.time):
                # Initiate van(vehicle_id, initiate vehicle at Ikea, current_time)
                self.vehicles.append(van(veh, 3, self.time))


    def assignRiderToVan(self):
        # For look ahead time-window
        timeWindow2 = 0*60
        for rider in self.remainingRiders:
            # Assume 5 min look ahead for arriving buses
            if (type(rider.rideID) == str) and ('virtual' in rider.rideID):
                timeWindow2 = 5*60
            # Checks if any requests are made
            if (rider.origTime <= self.time + timeWindow2):
                timePeriod = self.getTimePeriod(self.convertSecondsToTimeString(self.time))
                
                # This is to calculate user costs for Uber assignment
                directTravTime = nx.shortest_path_length(self.graph[timePeriod], source = rider.orig, \
                                                          target = rider.dest, weight = 'median_x')
                # The case when only one vehicle is working (6am - 7am)
                if (len(self.vehicles) == 1):
                    marginalCost, newRoute, riderPickup = self.vehicles[0].findBestRoute(self.graph[timePeriod], rider, \
                                                                                         self.timeDict, self.waitCoeff, \
                                                                                         self.driveCoeff)

                    self.vehicles[0].riderQueue.append(rider)
                    rider.van = self.vehicles[0].vehID
                    self.vehicles[0].route = newRoute
                    self.remainingRiders.remove(rider)  
                #Case where both shuttles are active
                #Find minimum marginal cost
                else:
                   self.findMinCost(timePeriod, rider)

    # Finds vehicle with minimum marginal cost
    def findMinCost(self, timePeriod, rider):
        marginalCosts = []
        routes = []
        pickupTimes = []
        # For each vehicle, compute marginal costs and select van-rider match based on minimum marginal cost
        for veh in self.vehicles:
            marginalCost, newRoute, riderPickup = veh.findBestRoute(self.graph[timePeriod], rider, \
                                                                    self.timeDict, self.waitCoeff, \
                                                                    self.driveCoeff)
            marginalCosts.append(marginalCost)
            routes.append(newRoute)
            pickupTimes.append(riderPickup)
        bestIndex = marginalCosts.index(min(marginalCosts))
        riderPickup = pickupTimes[bestIndex]
        self.vehicles[bestIndex].riderQueue.append(rider)
        rider.van = self.vehicles[bestIndex].vehID
        self.vehicles[bestIndex].route = routes[bestIndex]
        self.remainingRiders.remove(rider) 

    # Makes the next trip for the van based on the vehicles pre-determined route
    def nextTrip(self):
        timePeriod = self.getTimePeriod(self.convertSecondsToTimeString(self.time))
        for veh in self.vehicles:
            if (veh.inTransit == False) and ((veh.departureTime == None) or (veh.departureTime <= self.time)):
                travTime = veh.getLinkTravTime(self.graph[timePeriod])
                veh.arrivalTime = self.time + travTime 
                veh.inTransit = True

    # Moved the van between locations within the van's route
    def moveVans(self):
        for veh in self.vehicles:
            if (veh.arrivalTime <= self.time) and (veh.inTransit == True):
                veh.currentLocation = veh.route[0][1]
                veh.inTransit = False
                # Takes max of arrival time and the request time   
                if (len(veh.route) >= 2):     
                    # No dwell if current location == next location
                    dwellTime = 60 if (veh.route[0][1] != veh.route[1][1]) else 0 
                if (len(veh.route[0]) == 3) and (veh.route[0][2] == 'pickup'):
                    # Case when current location is a pickup --> can't depart before request pickup time
                    veh.departureTime = max(veh.arrivalTime, self.timeDict[veh.route[0][0]]) + dwellTime
                elif (len(veh.route[0]) == 3) and (veh.route[0][2] == 'dropoff'):
                    # Case when next location is a dropoff --> add dwellTime
                    veh.departureTime = veh.arrivalTime + dwellTime
                else:
                    veh.departureTime = veh.arrivalTime
                veh.route.pop(0)
                veh.dropoffRiders()
                veh.pickupRiders()
