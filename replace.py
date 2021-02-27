import re
import sys
import fileinput


def r(filename):
    if len(sys.argv) > 1:
        ngrok = sys.argv[1]
        for line in fileinput.input(filename, inplace=True):
            if '.ngrok.io' in line.strip():
                regex = re.search(r'\'(.*?).ngrok.io', line).group(1)
                line = re.sub(regex, ngrok, line)
            sys.stdout.write(line)


r('app/app.py')
r('instance/settings.py')