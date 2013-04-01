""" Venue sample"""
from SimPy.Simulation import *
from random import expovariate, seed, random, gauss

## @package AmusementPark
# This package partially satisfies the objectives of Amusement
# Park Project


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

      # Holds value to satisfy Req. 0015 - max num patrons per hour
      self.maxNumPatronsPerHour = numPatronsPerHour

      # Holds value to satisfy Req. 0016 - patrons served by x minutes
      # depending on venue type
      self.setTimeToServe = setTimeToServe

      # Satisfies Req. 0014 - venue must have queue for patrons
      self.waitQueue = [ ] # Stores patrons currently in line
      self.lineLevel = Level(name='numInLine', unitName='patrons',
            capacity=maxLineLength, initialBuffered=0,
            putQType=FIFO, getQType=FIFO,
            monitored=True, monitorType=Monitor)

      # Satisfies Req. 0017 - venue must have max queue length
      self.maxLineLength = maxLineLength


      self.lineDelayMonitor = Monitor(name = 'lineDelay')
      self.lineEmptyMonitor = Monitor(name = 'lineEmpty')
      self.lineFullMonitory = Monitor(name = 'lineFull')
      self.discouragedPatronsMonitor = Monitor(
            name = 'discouragedPatrons')

      print "Venue.start()"

      while True:
         lineEmpty = False

         if len(self.waitQueue) == 0 && self.lineEmpty == False:
            self.tempLineEmptyTimeStart = now()
            lineEmpty = True

         # This should be relocated to where Patron inserts self into queue
         elif len(self.waitQueue) == self.maxLineLength && \
            self.lineFull == False:
            tempLineFullTimeStart = now()
            self.lineFull = True

         # get the next available patron to serve
         yield get, self, self.lineLevel, 1


         currentPatronInfo = self.waitQueue.pop()

         currentPatronInfo.lineDepartureTime = now()

         # Monitors time that line is empty
         # This must be re-checked because even if a patron enters and
         # is removed from the line, the line might have instantly put
         # the patron on the ride.
         if len(self.waitQueue) == 0:
            self.lineEmpty = True
            self.tempLineEmptyTimeStart = now()
         # Records data for Req. 0009 - monitor empty line time
         # This should be relocated to where Patron inserts self into queue
         elif tempLineEmptyTimeStart != False:
            self.tempLineEmptyTimeEnd = now()
            # Observe time line has been empty to this point
            self.lineEmptyMonitor.observe(self.tempLineEmptyTimeStart -
               self.tempLineEmptyTimeEnd)
         # Records data for Req. 0010 - monitor (vendor 0) line full time
         elif self.lineFull == True:
            tempLineFullTimeEnd = now()

            self.lineFullMonitor.observe(tempLineFullTimeStart -
               tempLineFullTimeEnd)
            self.lineFull == False

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

         # Satisfies Req. 0015 - not serving more than maxNumPatronsPerHour
         # maxNumPatronsPerHour can only be served if queue is never
         # empty.
         yield hold, self, 1 / self.maxNumPatronsPerHour

         while len(self.waitQueue) == 0
            yield hold, self, 0.001   # Yield a small amount of time
                                     # to avoid spinning fast and
                                     # wasting CPU when the venue has
                                     # already served as many patrons
                                     # as possible within the last hour




