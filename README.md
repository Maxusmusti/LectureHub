# LectureHub: Backend
[Try out our webapp here](https://raghavmecheri.wixsite.com/lecturehub)

## How to run this project

Note that this Flask app is designed to work with MySql servers.

1. Clone this project and install dependencies. 
2. Edit the MySql settings at the top of main.py to connect to your MySql server
2. Open and navigate a terminal window to the directory of the project
3. Set FLASK_EXPORT to 'main.py'.
2. Execute 'flask run' in the same terminal window. 

### API Endpoints

Communicate with the backend by posting through the routes implemented in main.py. All routes accept a JSON object and return a JSON object with field "status" which is True when the request executes successfully and "False" when the request fails.
