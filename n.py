import sys
import fileinput


def updateNgrok(filename):
    with open(filename, "r+") as fp:
        print(fp.readlines())
        for line in fp.readlines():
            print(line)
    # for line in fileinput.FileInput(filename, inplace=1):
    #     print(line)
    #     # if 'ngrok.io' in line:
    #     #     print(line)


updateNgrok('app/app.py')