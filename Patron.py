
# Ryan Scott
# Patron.py
# Code runs successfully with Python 3.3.0 and SimPy 2.3.1

from SimPy.Simulation import * 
from random import randint, seed

# Relevant Requirements 
# (Monitors might be used to get some of these outputs)
# 0002 The CSCI shall output average simulation time spent in line by one patron in a day.
# 0003 The CSCI shall output average time each patron spends in line.
# 0004 The CSCI shall output the average number of venues patrons visit per day.
# 0005 The CSCI shall output the maximum number of venue visits by a single patron per day.
# 0007 The CSCI shall output the number of instances in which a patron could not find a venue. 
# 0008 The CSCI shall output the number of times per day that any patron selects a venue that has no other patrons in line.
# 0020 The CSCI patron shall never select a venue that has a full line.
# 0021 The CSCI shall simulate a 95% chance that each patron will select a venue that is different from the venue that most recently served the patron.
# 0022 If a patron selects a venue that is different from the venue that most recently served the patron, the patron shall select the next venue with frequency proportional to the venue's popularity.
# 0023 Every CSCI patron shall simulate a visit to Vendor 0 upon entry into the park.
# 0024 All CSCI patrons arrive at the park between 10AM and 12PM, with arrival times randomly distributed in that interval.
# 0025 1% of the CSCI patrons shall depart the park between 12PM and 1PM.
# 0026 2% of the CSCI patrons shall depart the park between 1PM and 2PM.
# 0027 3% of the CSCI patrons shall depart the park between 2PM and 3PM.
# 0028 4% of the CSCI patrons shall depart the park between 3PM and 4PM.
# 0029 10% of the CSCI patrons shall depart the park between 4PM and 5PM.
# 0030 10% of the CSCI patrons shall depart the park between 5PM and 6PM.
# 0031 5% of the CSCI patrons shall depart the park between 6PM and 7PM.
# 0032 10% of the CSCI patrons shall depart the park between 7PM and 8PM.
# 0033 10% of the CSCI patrons shall depart the park between 8PM and 9PM.
# 0034 45% of the CSCI patrons shall depart the park between 9PM and 10PM.
# 0035 Each CSCI patron shall simulate a walk of 2 minutes between venues in the same area.
# 0036 Each CSCI patron shall simulate a walk of 5 minutes between venues in separate areas.

# Assumptions:
# A patron must walk to a venue before it can know whether its line is full or not (This means that for Req. 0007, a patron will have to walk to every venue and find all lines to be full)
# Patrons never return to venue Vendor0 after leaving it
# Venue Vendor0 is in its own separate area

# Still need to implement:
# Patrons arriving at the park at appropriate times, PatronGenerator class
# Patrons leaving the park at appropriate times
# What to do if venue Vendor0's line is full (probably make the line infinite?)
# Need comments

class Patron(Process):

    def __init__(self, name):
    	self.name = name
    	self.nextVenue = venueVendor0 # Req. 0023
    	self.lastVenue = venueVendor0
    	self.numberVenuesVisited = 0 # Req. 0004, Req. 0005
    	self.numberTimesNoAvailableVenue = 0 # Req. 0007
    	self.numberEmptyLines = 0 # Req. 0008
    	self.lineFull = False
    	self.avoidVenues = []
    	Process.__init__(self, name=name)
    
    # This is the PEM
    def execute(self):
    	while True:
    		if (self.enterVenue()):
    			yield put, self, self.nextVenue.lineLevel, 1
    			yield passivate, self
    		self.chooseNextVenue()

    		walkTime = self.walkToNextVenue()
    		yield hold, self, walkTime
    		print (getTime() + " Patron " + self.name + " arrives at venue " + self.nextVenue.name)

    def enterVenue(self):
    	self.lastVenue = self.nextVenue

    	if (self.nextVenue.lineLevel.amount < self.nextVenue.lineCapacity):
    		print (getTime() + " Patron " + self.name + " has entered the line for venue " + self.nextVenue.name)
    		self.nextVenue.waitQueue.append(self)
    		self.numberVenuesVisited = self.numberVenuesVisited + 1 # Req. 0004, Req. 0005

    		if (self.nextVenue.lineLevel.amount == 0): # Req. 0008
    			self.numberEmptyLines = self.numberEmptyLines + 1
    		self.avoidVenues = []
    		self.lineFull = False
    		return True
    	else:
    		print (getTime() + " Patron " + self.name + " could not enter venue " + self.nextVenue.name + " because the line was full!")
    		self.lineFull = True
    		return False

    def chooseNextVenue(self):
    	randomNumber = randint(1,100)
    	if (randomNumber >= 1 and randomNumber <= 5 and self.lineFull == False and self.lastVenue != venueVendor0): # Req. 0021
    		print (getTime() + " Patron " + self.name + " decided to return to the same venue, " + self.lastVenue.name + ", and begins walking there")	
    	else:
    		if (self.lastVenue != venueVendor0):
    			self.avoidVenues.append(self.lastVenue)
    		availableVenues = list(Venues)

    		for venue in self.avoidVenues:
    			availableVenues.remove(venue)

    		totalPopularity = 0
    		for venue in availableVenues:
    			totalPopularity = totalPopularity + venue.popularity
    		
    		randomNumber = randint(1,totalPopularity)
    		currentPopularity = 0
    		i = iter(availableVenues)
    		venueFound = False
    		
    		while venueFound == False:
    			currentVenue = next(i)
    			currentPopularity = currentPopularity + currentVenue.popularity
    			if (randomNumber <= currentPopularity):
    				self.nextVenue = currentVenue
    				venueFound = True
    				currentVenue.timesChosen = currentVenue.timesChosen + 1
    		print (getTime() + " Patron " + self.name + " has chosen " + self.nextVenue.name + " as the next venue and begins walking there")

    def walkToNextVenue(self):
    	if (self.nextVenue.number[0] == self.lastVenue.number[0]):
    		print ("        Patron " + self.name + " walks for 2 minutes to reach venue " + self.nextVenue.name)
    		return 2 # Req. 0035
    	else:
    		print ("        Patron " + self.name + " walks for 5 minutes to reach venue " + self.nextVenue.name)
    		return 5 # Req. 0036

class VenueService(Process):
    
    def __init__(self, serviceTime):
    	self.serviceTime = serviceTime
    	Process.__init__(self,name="Venue Service")

    def reactivatePatronAfterDelay(self, patron):
    	print ("        Venue " + patron.nextVenue.name + " serves patron " + patron.name + " for " + str(int(self.serviceTime)) + " minutes")
    	yield hold, self, self.serviceTime
    	reactivate(patron)
    	print (getTime() + " Patron " + patron.name + " leaves venue " + patron.nextVenue.name)

class Venue(Process):
   
    def __init__(self, type, number, capacity, numPatronsPerHour, popularity):
    	self.name = type + " " + number
    	self.type = type
    	self.number = number
    	self.lineCapacity = capacity
    	self.numPatronsPerHour = numPatronsPerHour
    	self.popularity = popularity
    	self.waitQueue = [] # Stores patrons currently in line
    	self.lineLevel = Level(name='numInLine', unitName='patrons', capacity=self.lineCapacity, initialBuffered=0, putQType=FIFO, getQType=FIFO, monitored=True, monitorType=Monitor)
    	self.serviceTime = 0
    	self.timesChosen = 0
    	if (self.type == "Vendor"):
    		self.serviceTime = 3
    	elif (self.type == "Ride"):
    		self.serviceTime = 6
    	elif (self.type == "Attraction"):
    		self.serviceTime = 10
    	Process.__init__(self, name=self.name)

    def start(self):
    	while True:
    		if (self.lineLevel.amount > 0):
    			yield get, self, self.lineLevel, 1
    			currentPatron = self.waitQueue.pop(0)
    			print (getTime() + " Venue " + self.name + " is now serving patron " + currentPatron.name)
    			service = VenueService(self.serviceTime)
    			activate(service, service.reactivatePatronAfterDelay(currentPatron))
    		else:
    			yield hold, self, 0.01

#class PatronGenerator(Process):
    
    #def __init__(self, numberPatrons):
    	#self.numberPatrons = numberPatrons
    	#Process.__init__(self, name="Patron Generator")

    #def generatePatrons(self):
    	#while True:
    		#make self.numberPatrons amount of patrons, with arrival times between 10AM and 12PM

def getTime():
    time = now()

    hour = int(time/60)
    hour = hour + 10
    period = "AM"

    if (hour >= 12):
    	period = "PM"

    if (hour > 12):
    	hour = hour - 12

    if (hour < 10): # Just for formatting purposes
    	period = period + " "

    minutes = int(time%60)

    if (minutes < 10):
    	strMinutes = "0" + str(minutes)
    else:
    	strMinutes = str(minutes)

    strTime = str(hour) + ":" + strMinutes + period
    return strTime

def createVenues():
    venueRideA0 = Venue("Ride", "A0", 20, 30, 10)
    venueRideA1 = Venue("Ride", "A1", 20, 30, 5)
    venueRideA2 = Venue("Ride", "A2", 20, 30, 5)
    venueRideA3 = Venue("Ride", "A3", 20, 30, 3)
    venueAttractionA0 = Venue("Attraction", "A0", 20, 30, 10)
    venueAttractionA1 = Venue("Attraction", "A1", 20, 30, 3)
    venueAttractionA3 = Venue("Attraction", "A3", 20, 30, 4)
    venueVendorA0 = Venue("Vendor", "A0", 20, 30, 2)
    venueVendorA2 = Venue("Vendor", "A2", 20, 30, 4)
    venueRideB0 = Venue("Ride", "B0", 20, 30, 7)
    venueRideB1 = Venue("Ride", "B1", 20, 30, 4)
    venueRideB2 = Venue("Ride", "B2", 20, 30, 6)
    venueRideB3 = Venue("Ride", "B3", 20, 30, 3)
    venueAttractionB0 = Venue("Attraction", "B0", 20, 30, 3)
    venueAttractionB1 = Venue("Attraction", "B1", 20, 30, 4)
    venueAttractionB3 = Venue("Attraction", "B3", 20, 30, 2)
    venueVendorB0 = Venue("Vendor", "B0", 20, 30, 8)
    venueVendorB2 = Venue("Vendor", "B2", 20, 30, 3)
    venueRideC1 = Venue("Ride", "C1", 20, 30, 7)
    venueAttractionC1 = Venue("Attraction", "C1", 20, 30, 4)
    venueVendorC1 = Venue("Vendor", "C1", 20, 30, 3)

    Venues.append(venueRideA0)
    Venues.append(venueRideA1)
    Venues.append(venueRideA2)
    Venues.append(venueRideA3)
    Venues.append(venueAttractionA0)
    Venues.append(venueAttractionA1)
    Venues.append(venueAttractionA3)
    Venues.append(venueVendorA0)
    Venues.append(venueVendorA2)
    Venues.append(venueRideB0)
    Venues.append(venueRideB1)
    Venues.append(venueRideB2)
    Venues.append(venueRideB3)
    Venues.append(venueAttractionB0)
    Venues.append(venueAttractionB1)
    Venues.append(venueAttractionB3)
    Venues.append(venueVendorB0)
    Venues.append(venueVendorB2)
    Venues.append(venueRideC1)
    Venues.append(venueAttractionC1)
    Venues.append(venueVendorC1)

    for item in Venues:
    	activate(item, item.start())


random.seed()
initialize()

Venues = []
Patrons = []

venueVendor0 = Venue("Vendor", "0", 50, 50, 0)
activate(venueVendor0, venueVendor0.start())

createVenues()

#generator = PatronGenerator(100)
#activate(generator, generator.start())

patron1 = Patron("P1")
patron2 = Patron("P2")
patron3 = Patron("P3")
patron4 = Patron("P4")
patron5 = Patron("P5")

Patrons.append(patron1)
Patrons.append(patron2)
Patrons.append(patron3)
Patrons.append(patron4)
Patrons.append(patron5)

for item in Patrons:
    activate(item, item.execute())

simulate(until = 12*60)

#total = 0
#for v in Venues:
    #total = total + v.timesChosen
#for v in Venues:
    #print ("Venue " + v.name + " was chosen " + str((v.timesChosen/total)*100) + "%")

# Get input from user (instructor) when program is run
# Please enter Vendor 0's maximum line capacity:
# Please enter Vendor 0's maximum number of patrons per hour:
# Please enter Ride A0's popularity:
# Please enter Ride A0's maximum line capacity:
# Please enter Ride A0's maximum number of patrons per hour:
# etc.
# Please enter the number of days to simulate:
# Please enter ther number of patrons for day 1:
# Please enter the number of patrons for day 2:
# etc.
