from SimPy.Simulation import * 
import random
#from Park import Park

# constants for length of time a venue takes to serve a patron
VENDOR_SERVICE_TIME = 3
RIDE_SERVICE_TIME = 6
ATTRACTION_SERVICE_TIME = 10

# constants for areas
AREA_0 = "0"
AREA_A = "A"
AREA_B = "B"
AREA_C = "C"

# constants for the times when patrons begin to arrive and stop arriving
START_ARRIVAL_TIME = 0.0 * 60 # hour 0 (minute 0)
FINAL_ARRIVAL_TIME = 2.0 * 60 # hour 2 (minute 120)

class Park(Process):
  def __init__(self, numPatrons):
		Process.__init__(self)
		self.numPatrons = numPatrons
		self.patrons = []
		self.venues = []
		# level for tracking stats on number of patrons in park
		self.patronsInParkLevel = Level(name='Patrons in Park', unitName='Patrons',
										capacity=self.numPatrons, initialBuffered=0,
										putQType=FIFO, getQType=FIFO,
										monitored=True, monitorType=Monitor)
	def start(self):
		self.addVenues()
		self.generatePatrons()
		
		# venues need to be activated first, since patrons will request service from them upon activation
		activate(self.vendor0, self.vendor0.open())
		for venue in self.venues:
			activate(venue, venue.open())

		arrivalTimeRange = FINAL_ARRIVAL_TIME - START_ARRIVAL_TIME
		for patron in self.patrons:
			yield put, self, self.patronsInParkLevel, 1
			# generate a random arrival time
			arrivalTime = random.random() * arrivalTimeRange + START_ARRIVAL_TIME
			# active the patron at its arrival time
			activate(patron, patron.arrive(), at=arrivalTime)
		
	def addVenues(self):
		self.venues.append(Venue(name="Vendor A0", area=AREA_A, queueCapacity=20, queueInterval=0.5, serviceTime=VENDOR_SERVICE_TIME, popularity=0.05))
		self.venues.append(Venue(name="Attraction A1", area=AREA_A, queueCapacity=20, queueInterval=0.5, serviceTime=ATTRACTION_SERVICE_TIME, popularity=0.05))
		self.venues.append(Venue(name="Ride B0", area=AREA_B, queueCapacity=20, queueInterval=0.5, serviceTime=RIDE_SERVICE_TIME, popularity=0.2))
		self.venues.append(Venue(name="Vendor B1", area=AREA_B, queueCapacity=20, queueInterval=0.5, serviceTime=VENDOR_SERVICE_TIME, popularity=0.2))
		self.venues.append(Venue(name="Attraction C0", area=AREA_C, queueCapacity=20, queueInterval=0.5, serviceTime=ATTRACTION_SERVICE_TIME, popularity=0.25))
		self.venues.append(Venue(name="Ride C1", area=AREA_C, queueCapacity=20, queueInterval=0.5, serviceTime=RIDE_SERVICE_TIME, popularity=0.25))
		
		# give vendor 0 a virtually unlimited capacity of numPatrons        
		self.vendor0 = Venue(name="Vendor 0", area=AREA_0, queueCapacity=20, queueInterval=0.5, serviceTime=VENDOR_SERVICE_TIME, popularity=1.0)

	def generatePatrons(self):
		for i in range(self.numPatrons):
		   self.patrons.append(Patron(name=str(i), park=self))

# Represents a patron being served by a venue. When activated, it holds for the venue's service time, then reawakens the patron.
# This has to be done by a separate process to allow for multiple patrons to be serviced by a single venue at a time.
class VenueService(Process):
	def __init__(self, venue, patron):
		Process.__init__(self)
		self.venue = venue
		self.patron = patron

	# holds for the venue's service time, then reactivates the patron
	def servePatron(self):
		self.printEvent('started serving')
		yield hold, self, self.venue.serviceTime
		self.printEvent('finished serving')
		reactivate(self.patron)

	# helper function to print an event, for debugging
	def printEvent(self, event):
		print '(' + str(now()) + '): ' + 'Venue ' + self.venue.name + ' ' + event + ' Patron ' + self.patron.name + '.'

class Venue(Process):
	# name: descriptive name for the Venue
	# lineCapacity: the maximum number of patrons that can be in the Venue's queue
	# queueInterval: The number of minutes between serving patrons
	# serviceTime: The number of minutes that the Venue serves a patron
	# service time is in minutes
	def __init__(self, name, area, queueCapacity, queueInterval, serviceTime, popularity):
		Process.__init__(self, name=name)
		self.area = area
		self.queueInterval = queueInterval
		self.serviceTime = serviceTime
		self.popularity = popularity
		self.queue = []
		self.patronsInLineLevel = Level(name='Patrons in Line', unitName='Patrons',
										capacity=queueCapacity, initialBuffered=0,
										putQType=FIFO, getQType=FIFO,
										monitored=True, monitorType=Monitor)

	def open(self):
		self.printEvent('opened')
		while True:
			# if there is at least one person in line, let the venue serve them
			if len(self.queue) > 0:
				# get first patron from the line
				yield get, self, self.patronsInLineLevel, 1
				firstInLine = self.queue.pop(0)
				
				# start serving the patron
				venueService = VenueService(self, firstInLine)
				activate(venueService, venueService.servePatron())

				# wait a number of minutes before the next patron is served
				yield hold, self, self.queueInterval
			else:
				# it is necessary to hold for at least a small time interval here - otherwise, the program may get stuck in an infinite loop
				yield hold, self, 0.01

	# helper function to print an event, for debugging
	def printEvent(self, event):
		print '(' + str(now()) + '): ' + 'Venue ' + self.name + ' ' + event + '.'

	# waits for the line to become available, then adds the patron to the line
	# it is the patron's responsibility to check if the line is full by calling isLineFull before
	# calling this function. Otherwise, the patron will have to wait to join the line
	def joinQueue(self, patron):
		# add the patron to the venue's line - the yield is done first in case the line is full when the patron decides to join
		patron.printEvent('joined line for Venue ' + self.name)
		self.queue.append(patron)

	# returns True if this venue's line is full, False otherwise. This check should be made before a patron
	# joins the line for this venue
	def isLineFull(self):
		return self.patronsInLineLevel.amount == self.patronsInLineLevel.capacity

WALK_TIME_SAME_VENUE = 0
WALK_TIME_SAME_AREA = 2
WALK_TIME_DIFFERENT_AREA = 5

class Patron(Process):
	def __init__(self, name, park):
		Process.__init__(self, name=name)
		self.park = park

	def arrive(self):
		self.printEvent('arrived')

		# all patrons must visit vendor 0 first
		yield put, self, self.park.vendor0.patronsInLineLevel, 1
		self.park.vendor0.joinQueue(self)
		yield passivate, self
		self.lastVenue = self.park.vendor0

		# choose venues until the end of the simulation
		while True:
			# choose a venue
			self.chooseNextVenue()
			self.printEvent('chose Venue ' + self.nextVenue.name)

			# walk to the chosen venue
			yield hold, self, self.walkTimeToNextVenue()
			# reset the lastVenue so that the next calculated walk time is correct
			self.lastVenue = self.nextVenue
			self.printEvent('arrived at Venue ' + self.nextVenue.name)
			if not(self.nextVenue.isLineFull()):
				# in the small chance that the chosen venue actually has a full queue due to concurrent operations,
				# the patron is added to the Level first to ensure that they cannot join a full queue
				yield put, self, self.nextVenue.patronsInLineLevel, 1
				self.nextVenue.joinQueue(self);
				# passivate the patron to let the Venue take control
				yield passivate, self
			else:
				self.printEvent('discovered Venue ' + self.nextVenue.name + ' has a full line')

	# chooses the next venue for the patron, based on the venue popularities and the patron's riding history
	def chooseNextVenue(self):
		self.nextVenue = random.choice(self.park.venues)
		chooseAgainRandVal = random.random()
		rideRandVal = random.random()
		
		# there is a 95% chance that the next chosen venue will not be the same venue
		if chooseAgainRandVal < 0.95:
			venues = list(self.park.venues)
			popSum = 0.0
			i = 0
			# remove the last ride chosen from the list of choices
			while i < len(venues):
				if venues[i].name == self.nextVenue.name:
					del venues[i]
				else:
					popSum = popSum + venues[i].popularity
					i = i + 1
			# rescale the random value to the range of the reduced list - this ensures that all venues retain their same relative popularity
			rideRandVal = rideRandVal * popSum
		else:
			venues = self.park.venues
			# generate a new random value to decide the actual ride

		# randomly choose a venue based on their popularites - successfully tested on a 12 hour simulation with 1000 patrons
		popSum = 0
		for venue in venues:
			popSum = popSum + venue.popularity
			if rideRandVal <= popSum:
				self.nextVenue = venue
				return
		# in the rare case that no venue is chosen due to numerical imprecisions, simply pick the last venue in the list
		self.nextVenue = venue

	# holds for the amount of time required to walk from one venue to another
	def walkTimeToNextVenue(self):
		#calculate the walk time based on the relative locations of the previous and next venues
		if self.nextVenue == self.lastVenue:
			return WALK_TIME_SAME_VENUE # same venue, no time to walk
		elif self.nextVenue.area == self.lastVenue.area:
 			return WALK_TIME_SAME_AREA
		else:
			return WALK_TIME_DIFFERENT_AREA

	# helper function to print an event, for debugging
	def printEvent(self, event):
		print '(' + str(now()) + '): ' + 'Patron ' + self.name + ' ' + event + '.'

random.seed()
initialize()

park = Park(numPatrons=10)
activate(park, park.start())


simulate(until = 12.0 * 60.0) # simulate 12 hours, with each simulation unit representing 1 minute

print '(' + str(now()) + '): ' + 'Simulation Complete.'
