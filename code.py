import wifi
import ipaddress
import socketpool
import time
from adafruit_httpserver import Server, Request, Response, POST, GET
import adafruit_ili9341
import board, busio, displayio, os, fourwire


# Board pins for Display
board_type = os.uname().machine
print(f"Board: {board_type}")

if 'Pico' in board_type:
    cs_pin, reset_pin, dc_pin, mosi_pin, clk_pin = board.GP13, board.GP14, board.GP15, board.GP11, board.GP10

# Display Setup
displayio.release_displays()

# SPI bus for display
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)

# Display Bus
display_bus = fourwire.FourWire(
    spi,
    command=dc_pin,
    chip_select=cs_pin,
    reset=reset_pin
)

display = adafruit_ili9341.ILI9341(
    display_bus,
    width=240,
    height=320,
    rotation=270, # Portrait mode
    backlight_pin=None # Board has a backlight

)

print("ILI9341 Initialized")



print("Connecting to WiFI")

#  set static IP address
ipv4 = ipaddress.IPv4Address("192.168.0.74")
netmask = ipaddress.IPv4Address("255.255.255.0")
gateway = ipaddress.IPv4Address("192.168.0.1")
wifi.radio.set_ipv4_address(ipv4=ipv4, netmask=netmask, gateway=gateway)

# Wi-Fi credentials
ssid = "Girls_Gone_Wifi"
password = "jalapeno"

# Connect to WLAN
wifi.radio.connect(ssid, password)
print("Connected to WiFI")

# Web Server
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)


# HTML template for the webpage
def webpage(state):
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pico Web Server</title>
            <meta http-equiv="Content-type" content="text/html;charset=utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Pico Mobile Web Server</h1>
            <br>
            <form accept-charset="utf-8" method="POST">
                <h3>User Message Prompt</h3>
                <label for="msg">Message: </label>
                <input type="text" name="usermsg"><br><br>
                <input type="submit" value="Send" />
            </form>
            <br>
            <h3>State</h3>
            <p>{state}</p>
        </body>
        </html>
        """
    return str(html)


# --- Handler for GET requests ---
@server.route("/", GET)
def base(request: Request):
    #print("Returning Web")
    #  serve the HTML f strins
    #  with content type text/html
    return Response(request, f"{webpage("")}", content_type="text/html")

# Variables when Client sends a POST request
usermsg = ""

# --- Handler for Post requests ---
@server.route("/", POST)
def base(request: Request):
    state = ""
    usermsg = request.form_data.get("usermsg")
    if usermsg is not None:
        state = "Sending User Message: " + usermsg
        print(state)

        # Set the display color to red
        if usermsg is "Red":
            displayio.Bitmap.fill((255, 0, 0))
        # Set the display color to blue
        elif usermsg is "Blue":
            displayio.terminal.display.fill((0, 0, 255))

    #  serve the HTML f string
    #  with content type text/html
    return Response(request, f"{webpage(state)}", content_type="text/html")


clock = time.monotonic()  #  time.monotonic() holder for server ping
ping_address = ipaddress.ip_address("8.8.4.4")

# startup the server
try:
    print("starting server..")
    server.start(str(wifi.radio.ipv4_address), port=80)
    print("Listening on http://%s:80" % wifi.radio.ipv4_address)
#  if the server fails to begin, restart the pico w
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()


while True:
    try:
        if (clock + 30) < time.monotonic():
            if wifi.radio.ping(ping_address) is None:
                print("lost connection")
            else:
                print("connected")
            clock = time.monotonic()

        #  poll the server for incoming/outgoing requests
        server.poll()
    except Exception as e:
        print(e)
        continue
