#!/usr/bin/python
"""
A quick and not always optimal python implementation of project 5 for cs31.
"""

def popall(index, *lists):
  for l in lists:
    l.pop(index)

def standardizeRules(distances, word1, word2, nRules):
  valid = []
  
  for i in xrange(nRules):
    if distances[i] <= 0:
      continue
    if not word1[i].isalpha() or not word2[i].isalpha():
      continue
    
    word1[i], word2[i] = word1[i].lower(), word2[i].lower()

    # Check for previous
    if word1[i] in word1[:i] and word2[i] in word2[:i]:
      index = word1.index(word1[i])
      index2 = word2.index(word2[i])
      if index == index2:
        # Swap if greater
        if distances[i] > distances[index]:
          valid[valid.index(index)] = i
        continue
    elif word2[i] in word1[:i] and word1[i] in word2[:i]:
      index = word1.index(word2[i])
      index2 = word2.index(word1[i])
      if index == index2:
        # Swap if greater
        if distances[i] > distances[index]:
          valid[valid.index(index)] = i
        continue
      
    valid.append(i)

  # Refill word1, word2
  print valid
  for t in enumerate(valid):
    distances[t[0]] = distances[t[1]]
    word1[t[0]] = word1[t[1]]
    word2[t[0]] = word2[t[1]]

  return len(valid)

def determineQuality(dists, word1, word2, nRules, document):
  # Remove nonalphabet characters
  doc = list(document)
  doc = "".join([ c.lower() for c in doc if c.isalpha() or c == " "])
  words = doc.split()

  # Compute quality now
  quality = 0
  for t in zip(word1, word2, dists):
    if not t[0] in words or not t[1] in words:
      continue
    
    # Build lists of indices
    n1 = [w[0] for w in enumerate(words) if w[1] == t[0]]
    n2 = [w[0] for w in enumerate(words) if w[1] == t[1]]

    for i in n1:              # Suboptimal, but works
      for j in n2:
        if abs(i - j) <= t[2]:
          quality += 1
          break
      else:
        continue
      break                   # This is why you have gotos :)

  print words
  return quality
    
def testspec():
  dists = [2, 4, 1, 3, 2, 1, 13]
  word1 = ["mad", "deranged", "NEFARIOUS", "half-witted", "robot",
           "plot", "have"]
  word2 = ["scientist", "robot", "PLOT", "assistant", "deranged",
           "Nefarious", "mad"]
  nRules = 7;
  
  n = standardizeRules(dists, word1, word2, nRules)

  print "\n---RESULTS---\n"
  print dists[:n]
  print word1[:n]
  print word2[:n]

def test1():
  dists = [5, 2, 3, 9, 15, 1]
  word1 = ["cheese", "boARd", "black", "mo$ney", "potato", "umbrella"]
  word2 = ["cake", "games", "potato", "blah", "black", "rain"]
  nRules = 6;
  
  n = standardizeRules(dists, word1, word2, nRules)

  print "\n---RESULTS---\n"
  print dists[:n]
  print word1[:n]
  print word2[:n]

def qualspec():
  dists = [2, 4, 1, 13]
  word1 = ["mad", "deranged", "nefarious", "have"]
  word2 = ["scientist", "robot", "plot", "mad"]
  nRules = 4

  cases = ["The mad UCLA mad scientist unleaS&$Hed a deranged evil giant r535oBot.",
           "The mad UCLA scientist unleashed    a deranged robot.",
           "**** 2014 ****",
           "  That plot: NEFARIOUS!",
           "deranged deranged robot deranged robot robot",
           "Two mad scientists suffer from deranged-robot fever.",
           "",
           "#$(#$153  ()41[",
           "#$(#$m1ad53  ()scien41tist[",
           "The mad UCLA scientist nefarious unleaS&$Hed plot nefarious a deranged a evil giant r535oBot."]

  for s in cases:
    n = determineQuality(dists, word1, word2, nRules, s)
    print n
    print ""

def main():
  #testspec()
  #test1()
  qualspec()

if __name__ == "__main__":
  main()
