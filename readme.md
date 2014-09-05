College Football Projections is a website (college-fb.appspot.com) for looking up the schedules of college football teams and finding their probability of winning future games, as calculated by Jared Cross. 

The app uses the webapp2/Python framework, and is hosted on Google App Engine.

All data for the site is stored in Python dictionaries (and one Python list), in files. I've written Python scripts for parsing the CSV files Jared provides me with and producing a Python dictionary containing all necessary information about each team's schedule. There are also Python dictionaries containing information about each team's conference, main color, nickname. etc. 

When the user requests a certain team’s schedule, data is gathered from the various files and used to produce a dictionary (template_values) that contains all relevant data and is sent to the Jinja2 template. 

Contact me at nkarimeddiny at gmail.com with any questions.