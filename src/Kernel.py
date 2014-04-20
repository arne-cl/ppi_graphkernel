

class Kernel(object):
	
	def __init__(self):
		''
	
	def kernel(self, x, y):
		return dot_dict(x, y)
	
	def __str__(self):
		return "Kernel"
	
	def __repr__(self):
		return "Kernel"

def dot(x, y):
	sum = 0
	xlen = len(x)
	ylen = len(y)
	i = 0
	j = 0
	while i < xlen and j < ylen:
		if x[i].index == y[j].index:
			sum += x[i].value * y[j].value
			i+=1
			j+=1
		else:
			if x[i].index > y[j].index:
				j+=1
			else:
				i+=1
	return sum


def dot_dict(x,y):
	sum=0.0
	for key in x.keys():
		if y.has_key(key):
			sum+=x[key]*y[key]
	#print sum
	return sum



def dist(x,y):
	sum=0.0
	for key in x.keys():
		if y.has_key(key):
			sum+=abs(x[key]-y[key])
		else:
			sum+=abs(x[key])
	for key in y.keys():
		if x.has_key(key):
			continue
		else:
			sum+=abs(y[key])
	return sum


