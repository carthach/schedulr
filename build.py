import os

try:
    os.system("docker-compose up --build")
except KeyboardInterrupt:
    pass
