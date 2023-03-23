from PIL import Image
import random
import time
import requests
from io import BytesIO

from inky import InkyWHAT

#modifiable values
HOST_URL = "http://IP_ADRESS:5000"
DURATION = 20

def request_database_size():
    response = requests.get(HOST_URL + "/databasesize401")
    return int(response.content)

DATABASE_SIZE = request_database_size() 

IMAGE_PATH = "/static/images/"

inky_display = InkyWHAT("black")
inky_display.set_border(inky_display.BLACK)

#if the database is empty
if DATABASE_SIZE < 1:
    raise ValueError("ERROR: database is empty")

while True:
    random_number = random.randint(1, DATABASE_SIZE)

    url = HOST_URL + IMAGE_PATH + str(random_number) + ".png"

    #load image into memory
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    
    inky_display.set_img(img)
    inky_display.show()

    img.close()

    time.sleep(DURATION)
