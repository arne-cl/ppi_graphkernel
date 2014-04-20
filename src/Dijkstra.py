#An implementation of Dijkstra's algorithm for solving the shortest
#path problem in a graph
#Author: A. Airola
#Date: 22.5.2007

class Dijkstra(object):

    INFINITY = 1000000000

    def __init__(self, nodes,edges):
        self.nodes = nodes
        self.edges = edges

    def initializeGraph(self):
        """Initializes the graph with parent and distance information"""
        for node in self.nodes:
            node.parent = []
            node.parent_edge = []
            #This is enough for the parse graph problems,
            #not necessarily for some other problems
            node.distance = Dijkstra.INFINITY
        #This assumes that edges have no prior weights
        for edge in self.edges:
            edge.weight = 1

    def uninitializeGraph(self):
        """Removes the data that was added to the nodes.
        Note that for successive uses of dijkstrate one
        does not need to call this, as initialization
        will already replace old information"""
        for node in self.nodes:
            del(node.parent)
            del(node.distance)
        for edge in self.edges:
            del(edge.weight)

    def dijkstrate(self, start_node, directed=True):
        assert start_node in self.nodes
        self.initializeGraph()
        start_node.distance = 0
        computed_nodes = []
        while len(self.nodes)>0:
            u = self.extractMin()
            computed_nodes.append(u)
            for edge in u.outgoing:
                v = edge.to
                self.relax(u,v,edge)
            #If edges are considered undirected, then also
            #incoming edges are taken to consideration.
            if not directed:
                for edge in u.incoming:
                    v = edge.fro
                    self.relax(u,v,edge)
        self.nodes = computed_nodes
                

    def extractMin(self):
        """Extracts the next node to be considered"""
        #Could probably be implemented faster than a linear search if 
        #optimizations are needed
        minimum = Dijkstra.INFINITY
        index = None
        for i, node in enumerate(self.nodes):
            if node.distance <= minimum:
                minimum = node.distance
                index = i
        return self.nodes.pop(index)

    def relax(self, u, v, edge):
        """Compares the shortest path"""
        if v.distance > u.distance+edge.weight:
            v.distance = u.distance+edge.weight
            #perhaps redundant to store both of these
            v.parent = [u]
            v.parent_edge = [edge]
        elif v.distance == u.distance+edge.weight:
            v.parent.append(u)
            v.parent_edge.append(edge)

    def isPath(self, destination):
        #Dijkstration must have been done before this is called
        return destination.distance <Dijkstra.INFINITY

    def getPath(self, destination):
        #Dijkstration must have been done before this is called
        assert destination in self.nodes
        path = []
        node = destination
        while node.parent:
            path.append(node)
            node = node.parent[0]
        if path:
            path.append(node)
        path.reverse()
        return path

    def getAllPaths(self, destination):
        assert destination in self.nodes
        if not destination.parent:
            return []
        else:
            paths = self.recursivePaths(destination)
            for path in paths:
                path.reverse()
        return paths
        

    def recursivePaths(self, node):
        paths = []
        if not node.parent:
            paths.append([node])
        else:
            for n in node.parent:
                rpaths = self.recursivePaths(n)
                for path in rpaths:
                    p = [node]
                    p.extend(path)
                    paths.append(p)
        return paths
    
        
        
