#!/usr/bin/env python


__version__='$Id:  $'


import lisaxml
import sys
import re, math
import numpy

import synthlisa
from math import pi, sin, cos, sqrt

import numpy.oldnumeric as Numeric
import numpy.fft as FFT


## overlap maximized over the phase
## first argument is a signal second is zero phase template
def MaxInnerProd(ser1, ser2, PSD):
  size = Numeric.shape(ser1)[0]
  pdlen = size/2
  nyquistf = 0.5/15.0   #   !!! hardcoded !!!!
  freqs = Numeric.arange(0,pdlen+1,dtype='d') * (nyquistf / pdlen)
  if(Numeric.shape(ser2)[0] != size):
     print "size of time series must be the same"
     sys.exit(1)
  if(Numeric.shape(PSD)[0] != pdlen):
     print "wrong size of psd: ", pdlen, Numeric.shape(PSD)
     sys.exit(1)
  fourier1 = FFT.fft(ser1)
  fourier2 = FFT.fft(ser2)
  prod1 = Numeric.zeros(pdlen+1, dtype='d')
  prod2 = Numeric.zeros(pdlen+1, dtype='d')
  prod1[0] = 0.0
  prod1[1:pdlen] = numpy.multiply(fourier1[1:pdlen],numpy.conjugate(fourier2[1:pdlen])) + numpy.multiply(fourier1[-1:pdlen:-1],numpy.conjugate(fourier2[-1:pdlen:-1]))
  prod1[pdlen] = fourier1[pdlen]*fourier2[pdlen]
  prod2[0] = 0.0
  prod2[1:pdlen] = numpy.multiply(fourier1[1:pdlen],numpy.conjugate(fourier2[1:pdlen]*1.j)) + numpy.multiply((fourier1[-1:pdlen:-1]),numpy.conjugate(fourier2[-1:pdlen:-1]*(-1.j)))
  prod2[pdlen] = fourier1[pdlen]*fourier2[pdlen]
  Numeric.divide(prod1[1:], PSD, prod1[1:]) 
  Numeric.divide(prod2[1:], PSD, prod2[1:]) 
  olap0 = 0.0
  olappiby2 = 0.0
  for i in xrange(pdlen):
      if (freqs[i] > 1.e-5 and freqs[i]<0.01):
           olap0 += prod1[i]
	   olappiby2 += prod2[i]
  olap0 = 2.0*olap0/float(size)
  olappiby2 = 2.0*olappiby2/float(size)
#  olap0 =  2.0*(numpy.sum(prod1[1:]))/float(size) #it must be scaled by dt
#  olappiby2 =  2.0*(numpy.sum(prod2[1:]))/float(size) #it must be scaled by dt
  print "angle of maxim. = ", math.atan(olappiby2/olap0)
  return sqrt(olap0**2 + olappiby2**2) 


def InnerProd(ser1, ser2, PSD):
  size = Numeric.shape(ser1)[0]
  pdlen = size/2
  nyquistf = 0.5/15.0   #   !!! hardcoded !!!!
  freqs = Numeric.arange(0,pdlen+1,dtype='d') * (nyquistf / pdlen)
  if(Numeric.shape(ser2)[0] != size):
     print "size of time series must be the same"
     sys.exit(1)
  if(Numeric.shape(PSD)[0] != pdlen):
     print "wrong size of psd: ", pdlen, Numeric.shape(PSD)
     sys.exit(1)
  fourier1 = FFT.fft(ser1)
  fourier2 = FFT.fft(ser2)
  prod = Numeric.zeros(pdlen+1, dtype='d')
  prod[0] = 0.0
  prod[1:pdlen] = numpy.multiply(fourier1[1:pdlen],numpy.conjugate(fourier2[1:pdlen])) + numpy.multiply(fourier1[-1:pdlen:-1],numpy.conjugate(fourier2[-1:pdlen:-1]))
  prod[pdlen] = fourier1[pdlen]*fourier2[pdlen]
  Numeric.divide(prod[1:], PSD, prod[1:]) 
  olap0 = 0.0
  for i in xrange(pdlen):
      if (freqs[i] > 1.e-5 and freqs[i]<0.01):
           olap0 += prod[i]
  olap0 = 2.0*olap0/float(size)
 # olap0 =  2.0*(numpy.sum(prod[1:]))/float(size) #it must be scaled by dt
  return  olap0

def ComputeNorm(ser, sampling, PSD):
     size = Numeric.shape(ser)[0]
     if(Numeric.shape(PSD)[0] != size/2):
         print "wrong size of psd: ", pdlen, Numeric.shape(PSD)
         sys.exit(1)
     ser2 = synthlisa.spect(ser, sampling,0)
     norm = 0.0
     indx = 0
    # fout = open("dChiTest.dat", 'w')
     for i in xrange(size/2-1):
        if (ser2[i][0] > 1.e-5 and ser2[i][0]<0.009):
	    norm += ser2[i][1]/PSD[i]
#	    record = str(ser2[i][0]) + "    " + str(2.0*norm) + "\n"
#	    fout.write(record)
	    indx = indx + 1
     norm = sqrt(2.0*norm)
 #    fout.close()     
     #print "indx = ", indx
     #norm = sqrt(2.0 *numpy.sum(ser2[1:,1]/PSD))
     return norm



# set ourselves up to parse command-line options

from optparse import OptionParser

# note that correct management of the Id string requires issuing the command
# svn propset svn:keywords Id FILENAME

parser = OptionParser(usage="usage: %prog [options] BlindData.xml ChallengeNTDI_Key.xml Result1TDI.xml Result2TDI.xml ...",
                      version="$Id:  $")


parser.add_option("-p", "--maxPhase",
                  action="store_true", dest="phasemax", default=False,
                  help="maximizes over the phase on a single channel [off by default]")


(options, args) = parser.parse_args()

#!!!! currently we support only a single source parameter file  !!!

if len(args) < 3:
    parser.error("You must specify at least the output file and one input file!")

Datafile = args[0]
Injfile = args[1]
Detfiles = args[2:]

# To do: Need to read quadrutures as well...

if options.phasemax :
   if ( re.search('Challenge1.2', Injfile) == None and \
        re.search('Challenge1B.2', Injfile) == None ):
	print "phase maximization can be done only for 1.2 and 1B.2 challenges"
	sys.exit(1)


# Reading the data 

Datatdifile = lisaxml.readXML(Datafile)
tdiData = Datatdifile.getTDIObservables()[0]
Xdata = tdiData.Xf
Adata = (2.0*tdiData.Xf -tdiData.Yf - tdiData.Zf)/3.0
Edata = (tdiData.Zf - tdiData.Yf)/math.sqrt(3.0) 

samples = Numeric.shape(Xdata)[0]

# computing useful number of points
pdlen3 = samples/2
nyquistf = 0.5/15.0   #   !!! hardcoded !!!!
freqs = Numeric.arange(0,pdlen3+1,dtype='d') * (nyquistf / pdlen3)
ind = 0
for i in xrange(pdlen3):
    if (freqs[i] > 1.e-5 and freqs[i]<0.009):
        ind += 1    

ind = ind*2
print "data size = ", samples
print "number of used points ", ind 

if (re.search('Challenge1.2', Injfile) != None):
    Dfr = 9.
elif (re.search('Challenge1B.2', Injfile) != None):
    Dfr = 9.

print "It is BBH,", Dfr, " degree of freedom" 

# Dealing with key files (injected sources)

Injtdifile = lisaxml.readXML(Injfile)
#lisa = Injtdifile.getLISAgeometry()
Injsources = Injtdifile.getLISASources()
tdi = Injtdifile.getTDIObservables()[0]
Injtdifile.close()

X = tdi.Xf
A = (2.0*tdi.Xf -tdi.Yf - tdi.Zf)/3.0
E = (tdi.Zf - tdi.Yf)/math.sqrt(3.0) 

sampling = tdi.TimeSeries.Cadence

spr = "     "
"""fout1 = open("DataX.dat", 'w')
for i in xrange(samples):
   record = str(float(i)*sampling) + spr + str(Xdata[i]) + "\n"
   fout1.write(record)
fout1.close()
fout1 = open("KeyX.dat", 'w')
for i in xrange(samples):
   record = str(float(i)*sampling) + spr + str(X[i]) + "\n"
   fout1.write(record)
fout1.close()
"""

###  Computing quadratures if needed (we do not need pi/2)
if options.phasemax:
#   injfile =  Injfile[:-18]+'_piby2-tdi-frequency.xml'
#   Injtdifile = lisaxml.readXML(injfile)
#   tdipiby2 = Injtdifile.getTDIObservables()[0]
#   Xpiby2 = tdipiby2.Xf
#   Injtdifile.close()
   injfile =  Injfile[:-18]+'_0-tdi-frequency.xml'
   Injtdifile = lisaxml.readXML(injfile)
   tdi0 = Injtdifile.getTDIObservables()[0]
   X0 = tdi0.Xf

XX = synthlisa.spect(X, sampling, 0)
fr = XX[1:,0]

# Compute noise spectral density

om = 2.0 * pi * fr
L  = 16.6782

# instrument noise

Spm = 2.5e-48 * (1.0 + (fr/1.0e-4)**-2) * fr**(-2)
Sop = 1.8e-37 * fr**2

# Spm = 2.54e-48 * (1.0 + (fr/1.0e-4)**-2) * fr**(-2)
# Sop = 1.76e-37 * fr**2

Sx = 16.0 * numpy.sin(om*L)**2 * (2.0 * (1.0 + numpy.cos(om*L)**2) * Spm + Sop)
Sxy = -4.0 * numpy.sin(2.0*om*L)*numpy.sin(om*L) * ( Sop + 4.*Spm )
Sa = 2.0 * (Sx - Sxy)/3.0
Se = Sa

normX = ComputeNorm(X,sampling, Sx)
normA = ComputeNorm(A,sampling, Sa)
normE = ComputeNorm(E,sampling, Se)


#############################################
## Computing chi^2 and SNR with the key file
##############################################

diffAkAd = synthlisa.spect(Adata - A,sampling,0) 
diffEkEd = synthlisa.spect(Edata - E,sampling,0) 

# Computing combined SNR of a difference:
SnA =  2.0 * numpy.sum(diffAkAd[1:,1] / Sa) # square SNR_Adiff
SnE =  2.0 * numpy.sum(diffEkEd[1:,1] / Se)
SnA = ComputeNorm(Adata-A, sampling, Sa)**2
SnE = ComputeNorm(Edata-E, sampling, Se)**2
SnDiff = sqrt( SnA**2 + SnE**2 )

xi2 = SnDiff/(samples - Dfr)
chi2 = 0.5*(SnA + SnE)/(ind - Dfr)
#Computing combined SNR

SnA = sampling*InnerProd(Adata, A, Sa)/normA
SnE = sampling*InnerProd(Edata, E, Se)/normE
print "SnA = ", SnA, "  SnE = ", SnE
#print "normA = ", normA, "  normE = ", normE
#print "innerProda = ",  sampling*InnerProd(Adata, A, Sa), "innerProde = ",  sampling*InnerProd(Edata, E, Se)
Sn = sqrt(SnA**2 + SnE**2)
print 80*'='
print "using key file we get"
#print "xi = ", xi2
print "chi^2 = ", chi2
print "combined SNR = ", Sn
print 80*'='



###########################################
##   Dealing with result files
###########################################


#print Detfiles[0]
sz = len(Detfiles)
if (sz > 0):
   Detfiles[0] = Detfiles[0][1:-1]
   for i in xrange(sz):
      if i !=0:
         Detfiles[i] = Detfiles[i][:-1]


for userfile in Detfiles:
   # print userfile
    if ( re.search('key', userfile) == None and re.search('Key', userfile) == None):
       print 80*'*'
       print 4*" ", "Dealing with %s file..." % userfile 
       print 80*'*'
       Dettdifile = lisaxml.readXML(userfile)
       #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
       # Here I am dealing with only 1 source!!!!!
       # Nedd to expand it deal with multiple surces...
       #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
       Dettdi =  Dettdifile.getTDIObservables()[0]

       Xs = Dettdi.Xf
       As = (2.0*Dettdi.Xf - Dettdi.Yf - Dettdi.Zf)/3.0
       Es = (Dettdi.Zf - Dettdi.Yf)/math.sqrt(3.0) 

       name = userfile[:-4]+"X.dat"
#       print "recording file:", name
#       fout1 = open(name, 'w')
#       for i in xrange(samples):
#          record = str(float(i)*sampling) + spr + str(Xs[i]) + "\n"
#          fout1.write(record)
#       fout1.close()
       normXs = ComputeNorm(Xs, sampling, Sx)
       normAs = ComputeNorm(As, sampling, Sa)
       normEs = ComputeNorm(Es, sampling, Se)
      
       ### computing chi^2

       diffAsAd = synthlisa.spect(Adata - As,sampling,0) 
       diffEsEd = synthlisa.spect(Edata - Es,sampling,0) 

       # Computing combined SNR of a difference:
       SnA =  2.0 * numpy.sum(diffAsAd[1:,1] / Sa) # square SNR_Adiff
       SnE =  2.0 * numpy.sum(diffEsEd[1:,1] / Se)
       SnA = ComputeNorm(Adata-As, sampling, Sa)**2
       SnE = ComputeNorm(Edata-Es, sampling, Se)**2
       SnDiff = sqrt( SnA**2 + SnE**2 )

       chi2 = 0.5*(SnA + SnE)/(ind - Dfr)
       SnAdif = ComputeNorm(A-As, sampling, Sa)**2
       SnEdif = ComputeNorm(E-Es, sampling, Se)**2
 
       d_chi2 = 0.5*(SnAdif + SnEdif)/Dfr
        
       print "chi^2 = ", chi2
       print "d_chi^2 = ", d_chi2, SnAdif/Dfr, SnEdif/Dfr
       #Computing combined SNR

       SnAs = sampling*InnerProd(Adata, As, Sa)/normAs
       SnEs = sampling*InnerProd(Edata, Es, Se)/normEs

       Sns = sqrt(SnAs**2 + SnEs**2)

       print "combined SNR  = ", Sns
        
       # Computing overlaps
       
       olapA = sampling*InnerProd(A,As,Sa)/(normA*normAs)
       olapE = sampling*InnerProd(E,Es,Se)/(normE*normEs)
    
       print "overlap between A tdis  = ", olapA
       print "overlap between E tdis  = ", olapE


       if options.phasemax:
#           XXpiby2 =  synthlisa.spect(Xpiby2,sampling,0) # = XX0
           normX0 = ComputeNorm(X0, sampling, Sx)

#	   olapTest = sampling*MaxInnerProd(Xpiby2, X0, Sx)/normXX0
#	   print "max olap between quadratures: ", olapTest, normXX0
#	   olap1 = sampling*InnerProd(X0, X0, Sx)/normXX0
#	   olap2 = sampling*InnerProd(X0, Xpiby2, Sx)/normXX0
#           print "test ;", olap1, olap2

	   quadr = sampling*MaxInnerProd(Xs, X0,  Sx)
	   SnXdifMin = (normXs**2 + normX0**2 - 2.0*quadr)/(normX0 * normXs)
	   
	   SnXdiff = (normXs**2 + normX**2 - 2.0*sampling*InnerProd(Xs, X, Sx))/(normX * normXs)
	   
	   print "Non-minimized SNR of dX = ", SnXdiff
	   print "Minimized over the phase SNR of dX = ", SnXdifMin
	   print "Maximized overlap = ", quadr/(normX0 * normXs)
#	   print "check : ", normX, normX0
           #print "diffXX0 = %s , diffXXpiby2  = %s " % (2.0 * numpy.sum(diffXX0[1:,1] / Sx), 2.0 * numpy.sum(diffXXpiby2[1:,1] / Sx))
          # print "quadr 0 = %s,  quadr pi/2 = %s,  SNR = %s" % (quad0, quadpiby2, sqrt(quad0**2 + quadpiby2**2))
#	   print "quadr = ", quadr
#           print "norm X0 = %s,  norm Xd = %s" % (normXX0, normXXd)
        


