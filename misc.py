#This document contains classes not intended to be part of venue.py
# but can be moved to other appropriate lib/whatever.py files.


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