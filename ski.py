#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""A simple client to create a CLA model for the ski game."""

import sys
import random
import logging
import copy
import os.path

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter

#import model_params
import description


games = 0
yards = 0
longest = 0
slopesize = 80
slopewidth = 21
slopewidthmin = 23
slopewidthmax = 35
variablewidth = False

# uncomment for repeatable testing data
random.seed("NuPIC")

# number of records to train on
_NUM_RECORDS = 100

# set the checkpoint save file name
CWD = os.path.dirname(os.path.realpath(__file__))
SAVE = 'ski.model'
#savefile = os.path.join(CWD, SAVE)
savefile = "/Volumes/RAM Disk/ski.model"

#-----------------------------------------------------------------------------
# skier functions
#-----------------------------------------------------------------------------
def generate_random(choicelist):
    random_choice = random.choice(choicelist)
    return random_choice

def calc_skier_position(skierposition,predicted):
    if predicted > skierposition:
        skierposition = skierposition + 1
    if predicted < skierposition:
        skierposition = skierposition - 1
    return skierposition

def print_slopeline(padding,tree,skier,slopewidth,skierposition):
    """
    This function prints a line of the slope to the screen (stdout).
    The line includes two trees, and a skier.  Occasionally the
    trees are not printed due to a jump.  The width of the slope is
    static for now, and the random number is used to determine how
    far from the left side of the screen the slope begins.
    0--------------t--------S----------t-------------
    """
    global yards
    global slopesize
    leftspace = skierposition - padding
    rightspace = slopewidth - leftspace
    paddingr = padding + slopewidth
    paddingright = slopesize - paddingr
    print padding*" " + tree + leftspace*" " + skier + rightspace*" " + tree + paddingright*" ", yards
    return {'treeleft': padding, 'pos': skierposition, 'treeright': paddingr}

def print_slopeline_perfect(padding,tree,skier,slopewidth):
    skierposition = padding + slopewidth/2
    return print_slopeline(padding,tree,skier,slopewidth,skierposition)

def print_slopeline_crash(padding,tree,skier,slopewidth,skierposition):
    """
    This function prints a line of the slope to the screen (stdout)
    that indicates the skier crashed.
    """
    tree = "*"
    return print_slopeline(padding,tree,skier,slopewidth,skierposition)

def print_stats():
    """
    This function prints the final stats after a skier has crashed.
    """
    global games
    global yards
    global longest
    global savefile
    if yards > longest:
      longest = yards
    print
    print "You skied a total of", yards, "yards!"
    print
    print "In", games, "games, the best run is", longest, "yards!"
    print

    f = open('ski.log', 'a')
    f.write(str(games)+"\t"+str(yards)+"\n")
    f.close()

    return 0


#-----------------------------------------------------------------------------
# nupic functions
#-----------------------------------------------------------------------------
def createModel():
  return ModelFactory.create(description.config)



def runGame():
  global games
  global yards
  global slopesize
  global slopewidth
  global slopewidthmin
  global slopewidthmax
  global variablewidth
  global savefile
  tree = "|"
  skier = "H"
  minpadding = 0
  maxpadding = slopesize - slopewidth
  #choicelist_drift = [-2,-1,0,1,2]
  #choicelist_width = [-2,0,2]
  choicelist_drift = [-1,0,1]
  choicelist_width = [-1,0,1]

  games = games + 1
  change = 0
  padding = 14
  skierposition = (padding + (slopewidth/2))

  # See if we have a saved model to load
  if os.path.exists(savefile):
    print "Loading game history from " + savefile
    model = ModelFactory.loadFromCheckpoint(savefile)
  else:
    print "Creating new game model"
    model = createModel()

  model.enableInference({'predictionSteps': [1], 'predictedField': 'pos', 'numRecords': 4000})
  inf_shift = InferenceShifter();

  # - Train on a perfect run
  print
  print "================================= Start Training ================================="
  print
  for i in xrange(slopesize - slopewidth):
    record = print_slopeline_perfect(i,tree,skier,slopewidth)
    result = inf_shift.shift(model.run(record))

  while i > 0:
    record = print_slopeline_perfect(i,tree,skier,slopewidth)
    result = inf_shift.shift(model.run(record))
    i = i - 1

  while i < padding:
    record = print_slopeline_perfect(i,tree,skier,slopewidth)
    result = inf_shift.shift(model.run(record))
    i = i + 1

  for i in xrange(_NUM_RECORDS):
    yards = yards + 1
    if (variablewidth):
        change = generate_random(choicelist_width)
        slopewidth = slopewidth + change
        if slopewidth > slopewidthmax:
            slopewidth = slopewidthmax
        if slopewidth < slopewidthmin:
            slopewidth = slopewidthmin

    drift = generate_random(choicelist_drift)
    padding = padding + drift
    if padding > maxpadding:
        padding = maxpadding
    if padding < minpadding:
        padding = minpadding

    padding = padding - (change/2)
    if padding < 0:
        padding = 0
    if padding + slopewidth > slopesize:
        padding = slopesize - slopewidth

    record = print_slopeline_perfect(padding,tree,skier,slopewidth)

    result = inf_shift.shift(model.run(record))

  # - Then set it free to run on it's own
#  model.disableLearning()
  print
  print "=================================== Begin Game ==================================="
  print
  yards = 0
  padding = 14
  skierposition = (padding + (slopewidth/2))
  while True:
    yards = yards + 1
    if (variablewidth):
        change = generate_random(choicelist_width)
        slopewidth = slopewidth + change
        if slopewidth > slopewidthmax:
            slopewidth = slopewidthmax
        if slopewidth < slopewidthmin:
            slopewidth = slopewidthmin

    drift = generate_random(choicelist_drift)
    padding = padding + drift
    if padding > maxpadding:
        padding = maxpadding
    if padding < minpadding:
        padding = minpadding

    padding = padding - (change/2)
    if padding < 0:
        padding = 0
    if padding + slopewidth > slopesize:
        padding = slopesize - slopewidth

    record = print_slopeline(padding,tree,skier,slopewidth,skierposition)
    if ((skierposition - padding) < 1) or ((skierposition - padding) > slopewidth):
        break

    model.save(savefile)

    result = inf_shift.shift(model.run(record))
    #inferred = result.inferences['multiStepPredictions'][1]
    #predicted = sorted(inferred.items(), key=lambda x: x[1])[-1][0]
    predicted = 0.0
    total_probability = 0.0
    for key, value in result.inferences['multiStepPredictions'][1].iteritems():
        predicted += float(key) * float(value)
        total_probability += float(value)
    predicted = predicted / total_probability

    skierposition = calc_skier_position(skierposition, predicted)

    # reload if we made a bad prediction
    perfect = padding + slopewidth/2
    if abs(perfect - skierposition) > 2:
      model = ModelFactory.loadFromCheckpoint(savefile)


if __name__ == "__main__":
  while True:
    runGame()
    print_stats()
