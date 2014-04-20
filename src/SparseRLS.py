
import sys

from numpy import *
import numpy.linalg as la
import numpy.random as mlab


class SparseRLS(object):
	
	
	def __init__(self, Kr_, Y, includedindices):
		
		self.floattype = float64
		
		self.includedindices = includedindices
		
		self.Kr_ = Kr_
		self.Krr = take(Kr_, includedindices, 1)
		
		#Labels.
		#Can be either a vector (single output)
		#or a matrix (multiple output).
		self.Y = Y
		self.size = Y.shape[0]
		self.ysize = Y.shape[1]
		
		assert Kr_.shape == (len(includedindices), Y.shape[0])
		
		Z = la.cholesky(self.Krr)
		self.Zinv = la.inv(Z)
		#zvals, zvecs = la.eigh(self.Krr)
		#zvals, zvecs = mat(sqrt(zvals)), mat(zvecs)
		#Z = multiply(zvecs, zvals)
		#self.Zinv = multiply(1. / zvals.T, zvecs.T)
		#print zvecs * multiply(zvals.T, zvecs.T) - self.Krr
		#print Z*Z.T - self.Krr
		
		self.revals, self.revecs = la.eigh(self.Zinv * self.Kr_ * self.Kr_.T * self.Zinv.T)
		self.revals, self.revecs = mat(self.revals), mat(self.revecs)
		
		#print self.revecs * multiply(self.revals.T, self.revecs.T) - self.Zinv * self.Kr_ * self.Kr_.T * self.Zinv.T
		#print Z * self.revecs * multiply(self.revals.T, self.revecs.T) * Z.T - Z * self.Zinv * self.Kr_ * self.Kr_.T * self.Zinv.T * Z.T
		#sys.exit()
		
		self.M = self.Zinv.T * self.revecs
		self.Kr_TM = self.Kr_.T * self.M
		self.Kr_Y = self.Kr_ * self.Y
		self.MTKr_Y = self.M.T * self.Kr_Y
	
	def solve(self, lamb):
		self.lamb = lamb
		self.newreigvals = 1. / (self.revals + lamb)
		#self.alpha = self.Zinv.T * (self.revecs * (multiply(self.newreigvals.T, self.MTKr_Y)))
		self.alpha = self.M * multiply(self.newreigvals.T, self.MTKr_Y)
		
		#I = mat(eye(len(self.includedindices)))
		#print self.alpha - self.Zinv.T * la.inv(self.Zinv * self.Kr_ * self.Kr_.T * self.Zinv.T \
		#	+ lamb * mat(eye(len(self.includedindices)))) * self.Zinv * self.Kr_Y
		#print self.alpha - la.inv(self.Kr_ * self.Kr_.T + lamb * self.Krr) * self.Kr_Y
		#sys.exit()
	
	def rectangularCV(self, hoindices, hocompl):
		incnotho = []
		incinho = []
		for newind in range(len(self.includedindices)):
			oldind = self.includedindices[newind]
			if not oldind in hoindices:
				incnotho.append(newind)
			else:
				incinho.append(newind)
		incnotho = array(incnotho, dtype=int32)
                incinho = array(incinho, dtype=int32)
		Klh = self.Kr_[ix_(incnotho, hoindices)]
		M = self.M
		B = self.Kr_TM[hoindices] - self.Kr_.T[ix_(hoindices, incinho)] * M[incinho]
		
		Me = M[incinho]
		
		Ml = M[incnotho]
		
		#D = Ml.T * (self.Kr_[ix_(incnotho, hocompl)] * take(self.Y, hocompl))
		D = 	self.MTKr_Y \
			- Me.T * self.Kr_Y[incinho] \
			- self.Kr_TM[hoindices].T * self.Y[hoindices] \
			+ Me.T * self.Kr_[ix_(incinho, hoindices)] * self.Y[hoindices]
		
		BL = multiply(B, self.newreigvals)
		
		if len(incinho) == 0:
			C = BL * B.T
			N = BL * D
		else:
			BLMeT = BL * Me.T
			invPee = multiply(Me, self.newreigvals) * Me.T
			invinvPee = la.inv(invPee)
			C = BL * B.T - BLMeT * invinvPee * BLMeT.T
			MeLD = Me * multiply(self.newreigvals.T, D)
			N = BL * D - BLMeT * invinvPee * MeLD
		
		Ihh = mat(eye(len(hoindices), dtype = self.floattype))
		
		result = -la.inv(C - Ihh) * N
		
		return result
	
	
	def predict(self, testkm):
		a = self.alpha
		YY = testkm.T * a
		return YY

        def getHyperplane(self, fspace_dim, bvectors, datavector):
            tset_size = len(bvectors)
            alpha = self.alpha
            W = mat(zeros((fspace_dim, 1), dtype = float64))
            for i in range(tset_size):
                feaset = datavector[bvectors[i]]
                keys = feaset.keys()
                a = alpha[i]
                for key in keys:
                    value = feaset[key]
                    W[key,0]+= a*value
            return W
	


