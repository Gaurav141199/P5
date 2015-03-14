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
from game import Directions, Actions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
			   first = 'OffensiveAgent', second = 'DefensiveAgent'):
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

class DefensiveAgent(CaptureAgent):
  def __init__(self, index):
        self.index = index
        self.observationHistory = []

  def getSuccessor(self,gameState,action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != util.nearestPoint(pos):
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self,gameState,action):
    features = self.getFeatures(gameState,action)
    weights = self.getWeights(gameState,action)
    return features*weights

  def chooseAction(self,gameState):
    actions = gameState.getLegalActions(self.index)
    values = [self.evaluate(gameState,a) for a in actions]
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions,values) if v == maxValue]
    return random.choice(bestActions)

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    #if(scared ...)features['numInvaders'] = 0
    
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    teamNums = self.getTeam(gameState)
    initPos = gameState.getInitialAgentPosition(teamNums[0])
    # use the minimum noisy distance between our agent and their agent
    features['DistancefromStart'] = myPos[0] - initPos[0]
    if(features['DistancefromStart'] < 0): features['DistancefromStart'] *= -1
    if(features['DistancefromStart'] >= 10):features['DistancefromStart'] = 10
    features['DistancefromStart'] *= features['DistancefromStart']
    if(features['DistancefromStart'] <= 4):features['DistancefromStart'] += 1
    if(features['DistancefromStart'] == 1):features['DistancefromStart'] == -9999
    
    features['stayApart'] = self.getMazeDistance(gameState.getAgentPosition(teamNums[0]), gameState.getAgentPosition(teamNums[1]))
    features['onDefense'] = 1
    features['offenseFood'] = 0
    if myState.isPacman: features['onDefense'] = 0
    if(len(invaders) == 0 and successor.getScore() <= 0):
      features['onDefense'] =-1
      features['offenseFood'] = min([self.getMazeDistance(myPos,food) for food in self.getFood(successor).asList()])
      features['foodCount'] = len(self.getFood(successor).asList())
    if(len(invaders) != 0):
      features['stayApart'] = 0
      features['DistancefromStart'] = 0
    return features

  def getWeights(self,gameState, action):
    return {'foodCount': -20,'offenseFood': -1, 'DistancefromStart': 4, 'numInvaders': -8000, 'onDefense': 10, 'stayApart': 10, 'invaderDistance':-1100, 'stop':-20,'reverse':-5}
