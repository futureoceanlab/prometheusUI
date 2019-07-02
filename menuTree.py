
class MenuTree():
	# A tree is a list of nodes 
	# Nodes have a name and a list of child nodes
	# The purpose of the tree is to make it easy to get
	# the previous and next level of the menu

	def __init__(self, treeStructure):
		#treeStructure is a dictionary, like the MENU_TREE above

		self.root = 'root'
		self.tree = self.makeTree(treeStructure)
		self.currentLevel = self.tree

	def makeTree(self, treeStructure):
		#recursively make each TreeNode be a name a list of child TreeNodes

		if type(treeStructure) is not dict:
			return treeStructure
		treeFromHere = []
		for key in treeStructure:
			treeFromHere.append(TreeNode(key, self.makeTree(treeStructure[key])) )
			
		return treeFromHere

	def getSelectionLevel(self, selection):
		return selection.getImmediateChildren()

	def traverseDownToSelectionLevel(self, selection):
		#when the user clicks on the selection, this gets the children of that selection
		self.currentLevel = self.getSelectionLevel(selection)

	def goUpLevel(self, currentListOfNodes):
		self.currentLevel = self.findPreviousLevel()

	def printCurrentLevel(self):
		for i in self.currentLevel:
			print("  Node: ", i.name)

	def printGivenLevel(self, given):
		for n in given:
			print(n.name)

	def isAtRoot(self):
		return self.tree[0].getImmediateChildren() == self.currentLevel

	def isAtTempRoot(self):
		#TEMP
		return True

	def findPreviousLevel(self):
		exploreList = [self.tree[:]]
		if self.currentLevel == self.tree:
			return self.tree
		while True:
			tempExploreList = []
			for nodeList in exploreList:
				for node in nodeList:
					nodeChildren = node.getImmediateChildren()
					if set(self.currentLevel) == set(nodeChildren):
						return exploreList[0]
					tempExploreList.append(nodeChildren)
				exploreList = tempExploreList[:]


class TreeNode():
	def __init__(self, name, childrenOrValue):
		self.name = name

		if type(childrenOrValue)==list:
			#a node has children
			self.children = sorted(childrenOrValue, key=lambda x: x.name)
			self.value = None
		else:
			#or it is a leaf
			self.value = childrenOrValue
			self.children = None

	def getImmediateChildren(self):
		return self.children

	def sortLevel(self,children):        
		for i in range(len(children)):
			minimum = i
			
			for j in range(i + 1, len(children)):
				# Select the smallest value
				if children[j].name < children[minimum].name:
					minimum = j

			# Place it at the front of the 
			# sorted end of the array
			children[minimum], children[i] = children[i], children[minimum]
				
		return children

	def isLeaf(self):
		return self.children == None

	def getValue(self):
		return self.value

	def changeValue(self, newVal):
		if self.value:
			self.value = newVal

	def printChildren(self):
		s = ''
		for c in self.getImmediateChildren():
			s += c.name+' '
		print(s)