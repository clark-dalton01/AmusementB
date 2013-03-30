""" Venue sample""" 
from SimPy.Simulation import * 
from random import expovariate, seed, random, gauss

## @package AmusementPark
# This package partially satisfies the objectives of Amusement
# Park Project

## Patron
# Patron instances get into line at a venue and then passivate
# themselves. The venue reactivates the patron after the patron
# has been served. IN this implementation, patrons just passivate
# themselves again rather than visiting another venue.
class Patron(Process):
   """ """
   ## gotoVenue
   #
   #  This method implements Req. ???? It does not add the
   # the patron to the venue's line if the line is already full.
   # Once the patron adds itself to a venue's line, the patron
   # passivates itself. The venue is responsible for reactivating
   # the patron.
   def gotoVenue(self, venue):
      #print "Patron.start()"
      
      if(venue.lineLevel.amount < venue.lineLevel.capacity):
         # Put self in line for the venue and  passivate
         # self. The venue reactivates each patrons when the
         # venue is done serving them.
         # Req. ????
         #print "Putting patron in line"
         newPatronInfo = PatronInfo(now(), self);
         venue.waitQueue.append(newPatronInfo)
         yield put, self, venue.lineLevel, 1
      else:
         #print "Line was full so a patron walked away"
         venue.discouragedPatronsMonitor.observe(now())
         
      yield passivate, self
      #print "Awake again"
      yield passivate, self



## PatronInfo
# Instances of this class store information used to by venues to
# control interactions with patrons
class PatronInfo:
   """ """
   ## __init__
   #
   #  This method initializes PatronInfo instances
   def __init__(self, lineArrivalTime, patron):
      #print "PatronInfo.start()"
      self.lineArrivalTime = lineArrivalTime
      self.lineDepartureTime = 0 # Invalid value
      self.patron = patron

   def setlineDepartureTime(aTime):
      self.lineDepartureTime = aTime


## VenueSevice
#
#  Each instance of VenueSevice waits a specified amount of time
#  and then reactivates a patron. Each VenueSevice instance is
#  "one-shot" meaning the VenueSevice passivates itself after
#  "completing service" i.e. reactivating a single patron.
class VenueSevice(Process):

   ## start Process Execution Method (PEM)
   #  Start processing messages and run until simulation exit.
   def reactivatePatronAfterDelay(self, patron, delay):
      """ """
      #print "VenueSevice.start()"
            
      yield hold, self, delay
      #print "reactivate(patron)"
      reactivate(patron)
      yield passivate, self
      
   
## Venue
#
#  Each instance of Venue encapsulates a mechanism for serving
# patrons. 
class Venue(Process):
   
   ## start 
   #  This Process Execution Method (PEM) executes until the
   #  the simulation ends. The venue will serve up to the
   #  specified maximum number of patrons per hour.
   def start(self, maxLineLength, setTimeToServe,
      numPatronsPerHour):
      """ """
      
      ###
      # This list contains all patrons served within the last hour.
      # This list is used to meet Req. ???? by enforcing the limit
      # on the number of patrons served per hour. The venue will not
      # serve another patron as long as the number of patrons served
      # within the last hour is greater than or equal to the limit.
      self.lastHourWorthOfPatrons = [ ]
      
      self.maxNumPatronsPerHour = numPatronsPerHour
      self.maxLineLength = maxLineLength
      self.setTimeToServe = setTimeToServe
      self.waitQueue = [ ] # Stores patrons currently in line
      
      self.lineLevel = Level(name='numInLine', unitName='patrons',
            capacity=maxLineLength, initialBuffered=0,
            putQType=FIFO, getQType=FIFO,
            monitored=True, monitorType=Monitor)
      self.lineDelayMonitor = Monitor(name = 'lineDelay')
      self.discouragedPatronsMonitor = Monitor(
            name = 'discouragedPatrons')
      
      print "Venue.start()"
            
      while True:
         # Remove references to any patrons served more than an hour
         # ago to make room for any new patrons.
         newList = [ ]
         for patronInfo in self.lastHourWorthOfPatrons:
            if(patronInfo.lineDepartureTime > (now() - 60)):
               newList.append(patronInfo)
      
         self.lastHourWorthOfPatrons = newList
         
         # Only accept another patron if venue has not served
         # maxNumPatronsPerHour
         if (self.maxNumPatronsPerHour >
               len(self.lastHourWorthOfPatrons)):
               
            # get the next available patron to serve
            yield get, self, self.lineLevel, 1
            currentPatronInfo = self.waitQueue.pop()
            currentPatronInfo.lineDepartureTime = now()
            self.lastHourWorthOfPatrons.append(currentPatronInfo)

            # Observe time patron spent in line for this venue
            self.lineDelayMonitor.observe(
               currentPatronInfo.lineDepartureTime -
               currentPatronInfo.lineArrivalTime)
         
            # Schedule reactivation of the patron after a
            # delay representing time spent serving the patron.
            # The separate VenueService process is used so that
            # the venue can potentially start serving the next
            # patron in line before the service for the current
            # patron completes
            delay = self.setTimeToServe
            service = VenueSevice()
            activate(service, service.reactivatePatronAfterDelay(
               currentPatronInfo.patron, delay))
         else:
            yield hold, self, 0.01   # Yield a small amount of time
                                     # to avoid spinning fast and
                                     # wasting CPU when the venue has
                                     # already served as many patrons
                                     # as possible within the last hour
   

## PatronGenerator
# This process generates new Patron instances at a periodic rate
# and sends each patron to a venue.
class PatronGenerator(Process):
   """ """
   ## start
   #
   def start(self, venue):
      print "PatronGenerator.start()"
      i = 0
      while True:
         delay = expovariate(1.0/2.5) # Req. ????
         yield hold, self, delay

         newPatron = Patron(name = "Patron%02d"%(i,))
         activate(newPatron, newPatron.gotoVenue(venue))
         i = i + 1

## Simulation
#  The Simulation starts, runs for a predetermined period of
# simulated time, displays cumulative statistics, and then exist.
# Req. ????
theseeds = [1, ] # random number generator seeds for each trial

## Experiment/Result printer
#
for currentSeed in theseeds:
   seed(currentSeed)

   initialize()
   venue = Venue()
   activate(venue, venue.start(maxLineLength=10,
      setTimeToServe = 6, numPatronsPerHour = 21))
   generator = PatronGenerator(name = "PatronGenerator")
   activate(generator, generator.start(venue))
   simulate(until = 12 * 60) # Req. ????

   print "%8d: Venue's line capacity"%(
      venue.lineLevel.capacity)
   print "%8d: Total number of patrons served"%(
      venue.lineDelayMonitor.count())
   print "%8.4f: Average minutes spent in venue's line"%(
      venue.lineDelayMonitor.mean())
   print "%8d: Number of patrons who walked away because line was full"%(
      venue.discouragedPatronsMonitor.count())
   print "%8.4f: Time Average number of patrons in line"%(
      venue.lineLevel.bufferMon.timeAverage())
   
   # Calculate total elapsed time when line was full or empty
   lastSampleEmpty = False
   lastSampleFull = False
   cumulativeTimeWithEmptyLine = 0.0
   cumulativeTimeWithFullLine = 0.0
   for sample in venue.lineLevel.bufferMon:
      currentTime = sample[0]
      
      if lastSampleEmpty:
         cumulativeTimeWithEmptyLine = (cumulativeTimeWithEmptyLine +
            (currentTime - lastTime))
      elif lastSampleFull:
         cumulativeTimeWithFullLine = (cumulativeTimeWithFullLine +
            (currentTime - lastTime))
   
      if sample[1] == 0:
         lastSampleEmpty = True
         lastSampleFull = False
      elif sample[1] >= venue.lineLevel.capacity:
         lastSampleFull = True
         lastSampleEmpty = False
      else:
         lastSampleFull = False
         lastSampleEmpty = False
      
      lastTime = currentTime
   
   print "%8.4f: Total elapsed minutes when line was empty"%(
      cumulativeTimeWithEmptyLine)
   print "%8.4f: Total elapsed minutes when line was full"%(
      cumulativeTimeWithFullLine)

