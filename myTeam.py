# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
			   first = 'OffensiveAgent', second = 'DefensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class OffensiveAgent(CaptureAgent):
  def __init__(self, index):
	self.index = index
	self.observationHistory = []
	
#Follows from getSuccessor function of ReflexCaptureAgent
  def getSuccessor(self,gameState,action):
	successor = gameState.generateSuccessor(self.index, action)
	pos = successor.getAgentState(self.index).getPosition()
	if pos != util.nearestPoint(pos):
	  return successor.generateSuccessor(self.index, action)
	else:
	  return successor

#Follows from chooseAction function of ReflexCaptureAgent
  def chooseAction(self,gameState):
	actions = gameState.getLegalActions(self.index)
	values = [self.evaluate(gameState,a) for a in actions]
	maxValue = max(values)
	bestActions = [a for a, v in zip(actions,values) if v == maxValue]
	return random.choice(bestActions)

#Follows from evaluate function of ReflexCaptureAgent
  def evaluate(self,gameState,action):
	features = self.getFeatures(gameState,action)
	weights = self.getWeights(gameState,action)
	return features*weights

#Most of the logic will go in this function...
  def getFeatures(self,gameState,action):
  	#Start like getFeatures of OffensiveReflexAgent
	features = util.Counter()
	successor = self.getSuccessor(gameState,action)

	#Get other variables for later use
	agentState = successor.getAgentState(self.index)
	capsules = self.getCapsules(successor)
	enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
	position = successor.getAgentState(self.index).getPosition()

	#Get set of invaders and defenders
	invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
	defenders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
	
	#Set value for features
	features['successorScore'] = self.getScore(successor)
	features['distanceToFood'] = min([self.getMazeDistance(position,food) for food in self.getFood(successor).asList()])
	features['capsuleDistance'] = 0
	features['defenderDistance'] = 0 #Stays away from defensive agents from the other team
	features['invaderDistance'] = 0
	features['numInvaders'] = len(invaders)

	#Set behavior when Pacman and there are defenders
	if(agentState.isPacman and len(defenders) > 0):   
	  features['defenderDistance'] = min([self.getMazeDistance(position,a.getPosition()) for a in defenders])
	  if(len(capsules) > 0):
		capsuleDistance = min([self.getMazeDistance(position,cap) for cap in capsules])
		features['capsuleDistance'] = capsuleDistance

	#Act as DefensiveAgent if not Pacman, there are invaders, and agent is not scared
	if(agentState.isPacman == False and len(invaders) > 0 and agentState.scaredTimer == 0):
	  dists =[self.getMazeDistance(position,a.getPosition()) for a in invaders]
	  features['invaderDistance'] = min(dists)
	  features['numInvaders'] = len(invaders)

	return features

  def getWeights(self,gameState,action):
	return {'successorScore':100,'distanceToFood':-1,'capsuleDistance':-150,'defenderDistance':300,'invaderDistance':-10,'numInvaders':-1000}


class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def chooseAction(self, gameState):
	"""
	Picks among the actions with the highest Q(s,a).
	"""
	actions = gameState.getLegalActions(self.index)

	# You can profile your evaluation time by uncommenting these lines
	# start = time.time()
	values = [self.evaluate(gameState, a) for a in actions]
	# print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

	maxValue = max(values)
	bestActions = [a for a, v in zip(actions, values) if v == maxValue]

	return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
	"""
	Finds the next successor which is a grid position (location tuple).
	"""
	successor = gameState.generateSuccessor(self.index, action)
	pos = successor.getAgentState(self.index).getPosition()
	if pos != nearestPoint(pos):
	  # Only half a grid position was covered
	  return successor.generateSuccessor(self.index, action)
	else:
	  return successor

  def evaluate(self, gameState, action):
	"""
	Computes a linear combination of features and feature weights
	"""
	features = self.getFeatures(gameState, action)
	weights = self.getWeights(gameState, action)
	return features * weights

  def getFeatures(self, gameState, action):
	"""
	Returns a counter of features for the state
	"""
	features = util.Counter()
	successor = self.getSuccessor(gameState, action)
	features['successorScore'] = self.getScore(successor)
	return features

  def getWeights(self, gameState, action):
	"""
	Normally, weights do not depend on the gamestate.  They can be either
	a counter or a dictionary.
	"""
	return {'successorScore': 1.0}

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
	features = util.Counter()
	successor = self.getSuccessor(gameState, action)

	myState = successor.getAgentState(self.index)
	myPos = myState.getPosition()

	# Computes whether we're on defense (1) or offense (0)
	features['onDefense'] = 1
	if myState.isPacman: features['onDefense'] = 0

	# Computes distance to invaders we can see
	enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
	invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
	features['numInvaders'] = len(invaders)
	if len(invaders) > 0:
	  dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
	  features['invaderDistance'] = min(dists)

	if action == Directions.STOP: features['stop'] = 1
	rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
	if action == rev: features['reverse'] = 1

	return features

  def getWeights(self, gameState, action):
	return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}