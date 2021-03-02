import re
import sys
import time
import fileinput
import webbrowser


def r(filename, open=False):
    if len(sys.argv) > 1:
        ngrok = sys.argv[1].replace('/', '').replace('.', '')
        for line in fileinput.input(filename, inplace=True):
            if '.ngrok.io' in line.strip():
                regex = re.search(r'\'(.*?).ngrok.io', line).group(1)
                line = re.sub(regex, ngrok, line)
            sys.stdout.write(line)

        if open:
            time.sleep(.5)
            open_browser(ngrok)


def open_browser(url):
    url = 'https://' + url + '.ngrok.io/login'

    # Windows
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

    webbrowser.get(chrome_path).open(url)


r('app/app.py')
r('instance/settings.py', True)