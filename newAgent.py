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
	       first = 'DefensiveAgent', second = 'DefensiveAgent'):
  return [eval(first)(firstIndex), eval(second)(secondIndex)]


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
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    teamNums = self.getTeam(gameState)
    features['Distancefromstart'] = self.getMazeDistance(gameState.getInitialAgentPosition(teamNums[0]), gameState.getInitialAgentPosition(teamNums[1]))
    features['stayApart'] = self.getMazeDistance(gameState.getAgentPosition(teamNums[0]), gameState.getAgentPosition(teamNums[1]))
    if(len(invaders) != 0):
      features['stayApart'] = 0
    return features

  def getWeights(self,gameState, action):
    return {'Distancefromstart': 5, 'numInvaders': -2000, 'onDefense': 400, 'stayApart': 4, 'invaderDistance':-800, 'stop':-10,'reverse':-2}
