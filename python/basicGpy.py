#WARNING: This script does not currently run on Hydra

import numpy  #as np
import matplotlib #import pyplot as plt
import GPy

#matplotlib.rcParams['figure.figsize'] = (8,6)


X = numpy.random.uniform(-3.,3.,(20,1))
Y = numpy.sin(X) + numpy.random.randn(20,1)*0.05

print "X"
print X

print "Y"
print Y

print "kernel = GPy.kern.RBF(input_dim=1, variance=1., lengthscale=1.)"
kernel = GPy.kern.RBF(input_dim=1, variance=1., lengthscale=1.)

print "m = GPy.models.GPRegression(X,Y,kernel)"git add
m = GPy.models.GPRegression(X,Y,kernel)


print "m"
print m

plot = m.plot()
matplotlib.pylab.show(block=True) 

m.optimize(messages=True)

print "optimized m"
print m

plot = m.plot()
matplotlib.pylab.show(block=True) 

