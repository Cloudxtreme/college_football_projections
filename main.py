#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2, jinja2
import os, cgi, string, random, logging
from operator import itemgetter
from google.appengine.ext import db
from google.appengine.api import users, memcache
from datetime import datetime, timedelta
from schedule import scheduleDict
from top25_list import top25_list #for the html template
from top25 import top25Dict #for lookup within the app
from colorsDict import colorsDict
from conferences import conferences
from confDict import confDict
from capwordsTeams import capwordsTeams
from nicknamesDict import nicknamesDict
from scheduleNames import scheduleNameDict
from scheduleNames2 import scheduleNamesDictReverse
from d2teams import d2teamsDict
from winsDict import winsDict
from lossDict import lossDict

#if team name is ever sent to database in the future, need to use cgi.escape:
#team = cgi.escape(self.request.get("teamInput")).upper()
#if using cgi.escape, need the following code:
        #if team == "TEXAS A&AMP;M":
        #    team = "TEXAS A&M"
        #if team == "FLORIDA A&AMP;M":
        #    team = "FLORIDA A&M"
        #if team == "ALABAMA A&AMP;M":
        #    team = "ALABAMA A&M"
        #if team == "WILLIAM &AMP; MARY":
        #    team = "WILLIAM & MARY"

jinja_environment = jinja2.Environment(
		loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'])

class MainHandler(webapp2.RequestHandler):

    #this is called by the post() method
    def prepScheduleAndConfInfo(self, currentDate, team):
            
            capwordsTeam = capwordsTeams[team]
#the nicknamesDict dictionary has every team's nickname
            nickname = nicknamesDict.get(team)
#for a given team name, this is to prepare the correct filename for the team logo:
            imageName = self.prepImageName(team)
#this returns the hex code for the team's primary color:
            schoolColor = colorsDict.get(team)
#this returns the team's conference:
            conference = conferences[team].upper()

            confOpponentInfo = []
            self.prepConfOpponentInfo(team, conference, confOpponentInfo)

            scheduleName = scheduleNameDict[team]
            #this returns a list of tuples: 
            schedule = scheduleDict[scheduleName]#each tuple: 
    #(opponent, date, "@" symbol for away and "" for home and "N" for neutral, prediction, (score, if past game))
            futureScheduleInfo = []
            pastScheduleInfo = []

#this will be important if a team has any games played at a neutral location:
            footnote = []

            self.prepScheduleInfo(currentDate, schedule, futureScheduleInfo, pastScheduleInfo, footnote)
            
            neutralFootnote = ''
            if footnote:
                neutralFootnote = footnote[0]
            template_values = {"pastschedule":pastScheduleInfo, "futureschedule":futureScheduleInfo, "team":team, "capwords": capwordsTeam,"nickname": nickname, "imageName":imageName, "schoolColor":schoolColor,  "conference":conference, "confOpponentInfo":confOpponentInfo, "footnote" : neutralFootnote}
            template = jinja_environment.get_template('index.html')
            self.response.write(template.render(template_values))

    #this is called by the prepScheduleAndConfInfo() method
    def prepScheduleInfo(self, currentDate, schedule, futureScheduleInfo, pastScheduleInfo, footnote):

        for game in schedule:

            prediction = game[3]
            if prediction != "NA":
                prediction = prediction * 100
                prediction = "{:10.1f}".format(prediction) + "%"

            neutral = "" #if game is played at neutral site, this variable will be used to add an asterisk to schedule
            site = game[2]
            if site == "N":
                neutral = "*"
                site = ""
                footnote.append("* game played at neutral location")#if the team has 1 or more games at neutral sites, this footnote appears

            opponent = game[0]
#check to see if the opponent is a ranked team, so their ranking can be added to the schedule:
            opponentAbbrev = scheduleNamesDictReverse.get(opponent)
            ranking = top25Dict.get(opponentAbbrev)
            if not ranking:
                ranking = ""
            else:
                ranking = " #" + str(ranking)

            date = game[1] #this will be displayed in the team's schedule
            dateForComparison = int("2014" + date) #this is for determining if the game has already taken place
            month = date[0:2]
            day = date[2:]
            if month[0] == "0":
                month = month[1:]
            date = month + "-" + day

#check if an opponent is FBS or not. This info will be stored in an HTML data attribute for each team. For non-FBS teams, 
#when user clicks on team name to see their schedule, they see a note saying that schedules are only available for FBS teams:  
            longOpponentName = scheduleNamesDictReverse.get(opponent)
            if longOpponentName: #if the opponent is a FBS/1A team
                opponent = longOpponentName
                fbs = 1
            else: #if the opponent is a 1AA team
                fbs = 0
                longOpponentName = d2teamsDict.get(opponent)
                if longOpponentName:
                    opponent = longOpponentName
                          
            if dateForComparison >= int(currentDate): #if the game is happening in the future
                futureScheduleInfo.append({"opponent":opponent,"date":date, 'neutral' : neutral, 'site':site, "odds" : prediction, "ranking": ranking, "fbs":fbs})
            else: #if the game has already happened
                if len(game) > 4: #meaning there's a game[4]
                    score = game[4]
                else:
                    score = "NA"
                pastScheduleInfo.append({"opponent":opponent,"date":date, 'neutral' : neutral, 'site':site, "odds" : prediction, "ranking": ranking, "fbs":fbs, "score":score})
    
    #this is called by the prepScheduleAndConfInfo() method
    def prepConfOpponentInfo(self, team, conference, confOpponentInfo):
#this variable shows whether a certain team in the conference standings table is the selected team or another team
#the default is that it's another team:
        selectedTeam = "otherTeam"
        if conference != "INDEPENDENT":
#this is for building the conference standings table:
              confOpponents = confDict[conference] #returns a list with all teams in the conference
              for confOpponent in confOpponents:
                if confOpponent == team:
#this is in order to give the selected team a different background color in the conference standings table:
                    selectedTeam = "selectedTeam"
                confOpponentAbbrev = scheduleNameDict.get(confOpponent)
                teamWins = winsDict.get(confOpponentAbbrev)
                if teamWins is None:
                    teamWins = 0
                teamLosses = lossDict.get(confOpponentAbbrev)
                if teamLosses is None:
                    teamLosses = 0
                if teamWins == 0 and teamLosses == 0:
                    winPercentage = 0    
                else:
                    winPercentage = teamWins / (teamWins + teamLosses)
                record = str(teamWins) + "-" + str(teamLosses)
                confOpponentInfo.append({"team": confOpponent, "selectedTeam": selectedTeam, "record": record, "winpercentage": winPercentage})
                confOpponentInfo.sort(key = itemgetter("winpercentage"), reverse = True)

#the next line is important for the teams that appear after the selected team in the conference standings table,
#so they don't get the special background color: 
                selectedTeam = "otherTeam"
        else: #for Notre Dame and other independents:
              confOpponents = None

    #this is called by the prepScheduleAndConfInfo() method
    def prepImageName(self, team):
        
        imageName = string.replace(team," ","_")
        imageName = string.replace(imageName,"&","A")
        imageName = string.replace(imageName,"(","P")
        imageName = string.replace(imageName,")","P")
        imageName = string.replace(imageName,".","P")
        return imageName

    def getDate(self):
        
        TZoffset = timedelta(hours = -4)
        currentDate = format(datetime.now() + TZoffset, '%Y%m%d')
        return currentDate

    def get(self):

        template_values = {"top25": top25_list}
        template = jinja_environment.get_template('index.html')
        self.response.write(template.render(template_values))
        
    def post(self): #the following code runs when user requests a team's schedule

        currentDate = self.getDate()
        
        team = self.request.get("teamInput").upper()
#The capwordsTeams dict has the name for each school that looks good in writing.        
#For STANFORD, the name will be Stanford. For LSU, the name will be LSU (not Lsu).
#If the user uses autocomplete, the team name is guaranteed to be found in capwordsTeams
        if team in capwordsTeams:
           
            self.prepScheduleAndConfInfo(currentDate, team)

        else:
        	self.response.write("<h1>error - try typing in the team name again. <a href='/'>Return to homepage</a></h1>")

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)

