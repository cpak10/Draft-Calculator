# Draft Calculator

In League of Legends, an integral part of the competitive scene is what is known as draft stage. This is where the two teams decide which champions, out of the 160 that exist, that they would like to play. Below are scripts that utilize public data on matches in solo/duo queue (the mode which most League of Legends gamers play) to predict how certain champion combinations are expected to play out. All data is pulled from a public site linked below.

Essentially, the scripts below will take a look at when each champion is most likely to win in a game and considers those points as its strengths. Then the algorithms will combine all the data for the 10 champions at play and output when exactly each team is expected to do well.

Champion.gg link: https://champion.gg/

Draft Analyzer - draft.py
- This outputs a graph that vizualizes when a team will hit its point of strength.

Draft Database Builder - draft_api.py
- This calls Riot Games API to build the databases used to feed this analyzer.

Draft Highlights - draft_highlights.py
- This is used to show win rates for certain drafts.

Draft Model - draft_ml.py
- This is an experimental script that uses TensorFlow neural nets to predict draft outcomes.
