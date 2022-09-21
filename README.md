# nRF Cloud Device Monitor Tool  

### Application that monitors device activity in a user's account from nRF Cloud. Connects to nRF Cloud to access virtual device (aka account device) and uses MQTT connection to subscribe/publish to topics and receive messages. This program can also be used to create a new account device along with its certificates. Login information and topics previously subscribed to for each account type and device are stored and used upon the next login.

## Requirements

#### User API Key from nRF Cloud
#### pip install -U paho-mqtt  
#### pip install -U tkinter-tooltip  
#### pip install -U matplotlib

## main.py
#### Encapsulates almost all of the GUI design and main program functionality. Choose from four different account types (Prod, Beta, Dev, and Feat) to login to. ConfigParser is used to store the login info according to the account type that was chosen. 

### sort_message():
#### Digs through the dict to look for all key:value pairs, including values with a value. The results will be used to send specific data types to our plots.py and output the data types and values line-by-line on the Treeview. 

### connectMQTT():
#### Uses Paho MQTT library to connect to the broker with secure TLS connection to port 8883.

### change_device():
#### This function will be ran through every time a device is selected/unselected from the drop-down menu on the top left of the main screen. This is to ensure that we output the correct device information and saved topics, and when switching from one device to another, to first disconnect from the previous one before connecting to the next one. 

## topics.py
#### List of topics to subscribe to, publish to, and some possible messages to publish to a topic. The topics in the lists are reduced to {mqtt_topic_prefix} or {device_id} due to the long length of the actual address. Therefore, we also have functions to translate those to be able to use in our program to subscribe or publish.

## http_requests.py
#### REST API used to fetch account information or create new account device. If there was an error in doing so, a pop-up window will alert the user to try the same action again or return to login.

## plots.py
#### Creates two graphs to plot specific incoming data from messages received (RSRP and Button). Data is sent into plots.py when new data is received, and the graph updates every five seconds.

## generate_certs.py
#### Function to create an account device along with CA certificate, client certificate, and private key.

## event_clicks.py
#### When clicking on the input boxes in the "Subscribe" or "Publish" tabs, remove the shadow text, and put it back up when not in use.

## terminal.py
#### Terminal input/output functions for the black box on the bottom right of the main screen. 

## themes.py
#### Tkinter TTK custom theme for the tabs on the main screen. 