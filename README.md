## Usage
### Installation
You will need to:
- Install latest version of [Google Chrome](https://www.google.com/chrome/).
- Install [Python 3](https://www.python.org/downloads/)
- Have a Facebook account without 2FA enabled

Download the repository and open the cmd inside it

```bash
# Set up a virtual env

"python3 -m venv venv" oppure "python -m venv venv" oppure "py -m venv venv"
call venv/scripts/activate.bat

# Install Python requirements

pip install -r requirements.txt 
```

The code is multi-platform and is tested on both Windows and Linux.
Chrome driver is automatically downloaded using the chromedriver_manager package.

For local testing a mysql server instance is required on port 3306, the access info must be specified in the constants.py file.

### How to Run
- Fill your Facebook credentials into [`res/credentials/credentials.yaml`](res/credentials/credentials.yaml)
- Edit the [`res/input/input.txt`](res/input/input.txt) file and add profile, groups and individual group posts links as you want in the following format with each link on a new line:
Make sure the link only contains the username or id number at the end and not any other stuff. Make sure its in the format mentioned above.

Run the command !

```python
python main.py
```
