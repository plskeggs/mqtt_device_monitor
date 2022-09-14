'''
Login screen verifies if API key is valid and proceeds to connect
to MQTT broker with client certificate and private key.
A .ini file is created to save the valid API keys and certificates.

'''
import argparse
import json
from tkinter import ttk
import paho.mqtt.client as mqtt

import configparser
import os
from tkinter import *
from tkinter import filedialog as fd
from tkinter.font import BOLD
from tkinter.ttk import Combobox, Notebook
from tktooltip import ToolTip

import http_requests
import generate_certs
import themes
import event_clicks
import plots
import topics

#universal font and background
myFont = 'Arial'
myBg = '#333F48'

#these are used to log in
account_type = '' 
api_key = ''
client_cert = ''
priv_key = ''

data_to_list_api = ['']
data_to_list_client = ['']
data_to_list_key = ['']
subscribed_topics_list = []

client_id = ''
mqtt_topic_prefix = ''
mqtt_endpoint = ''
topic = None 

http_create = None
http_get = None
certs_flag = None
client_flag = None
first_start_flag = 0
first_start_flag2 = 0
auto_sub_flag = 0
j = 0

ACC_URL = 'https://api.nrfcloud.com/v1/account'
DEV_URL = 'https://api.nrfcloud.com/v1/devices'
AUTH_BEARER_PREFIX = 'Bearer '
PORT = 8883
KEEP_ALIVE = 30

myGrey = '#D9D9D9'  #even lighter grey
lighter_grey = '#D3D3D3'    #this is darker than myGrey
light_grey = '#ECEFF1'
middle_grey = '768692'
dark_grey = '#333F48'
nordic_blue = '#00A9CE'
nordic_blueslate = '#0033A0'
nordic_lake = '#0077C8'

'''
def parse_args():
    parser = argparse.ArgumentParser(description="Device Credentials Installer",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--apikey", type=str,
                        help="nRF Cloud account API key",
                        default=None)
    parser.add_argument("-v", "--verbose",
                        help="bool: Make output verbose",
                        action='store_true', default=False)
    parser.add_argument("-d", "--deviceid", type=str,
                        help="Device ID",
                        default=None)
    return parser.parse_args()

args = parse_args()
api_key = args.apikey
target_device = args.deviceid
'''

config = configparser.ConfigParser()    #instantiate config parser for login info
topic_config = configparser.ConfigParser(allow_no_value=True)   #config parser for topics

'''Tkinter Shadow Functions'''
#whenever input boxes are modified, go to event_clicks to do work
def tab2_on_entry_click_left(event):
    event_clicks.tab2_remove_shadow_text_left(tab2_topic_input)

def tab2_entry_focus_out_left(event):
    event_clicks.tab2_insert_shadow_text_left(tab2_topic_input)

def tab2_on_entry_click_right(event):
    event_clicks.tab2_remove_shadow_text_right(tab2_msg_input)

def tab2_entry_focus_out_right(event):
    event_clicks.tab2_insert_shadow_text_right(tab2_msg_input)

def tab1_on_entry_click(event):
    event_clicks.tab1_remove_shadow_text(tab1_sub_to_topic)

def tab1_entry_focus_out(event):
    event_clicks.tab1_insert_shadow_text(tab1_sub_to_topic)

#interactive events customizations
def button_config(button):
    button.bind("<Enter>", button_hover)
    button.bind("<Leave>", button_hover_leave)

def button_hover_leave(event):  #go back to original color
    button = event.widget
    button['bg'] = orig_color

def button_hover(event):    #change color of button when hovered over with mouse
    global orig_color

    button = event.widget
    orig_color = button.cget("background")  #grab button's original color
    button['bg'] = "grey"

def enter_login_press(event):   #for login screen
    enter_login() #pass onto function as if the 'Enter' button was clicked

def terminal_enter_event(e):
    terminal_enter()

def terminal_clear():   #clear terminal output and entry box
    terminal_list['state'] = NORMAL 
    terminal_input.delete(0, END)
    terminal_list.delete(1.0, END)
    terminal_list['state'] = DISABLED

def terminal_enter():    
    user_input = terminal_input.get()
    if user_input == '':    #nothing typed in, do nothing
        return 
    else:
        terminal_list['state'] = NORMAL
        terminal_print(user_input)  #output user input on terminal 
        terminal_list['state'] = DISABLED

    terminal_list['state'] = NORMAL 
    if user_input == '/help':
        help_output()
    elif user_input == '-v':
        terminal_list.insert(END, 'Python Version 3.10.6\n')
        terminal_list.insert(END, 'Developed SUMMER 2022\n')
    elif user_input == '-acc':
        #terminal_list.insert(END, ) 
        pass

    terminal_input.delete(0, END) #clear entry box
    terminal_list['state'] = DISABLED

def terminal_print(text):   #terminal output
    terminal_list['state'] = NORMAL
    text_format = ' >> ' + text 
    terminal_list.insert(END, text_format + '\n') #insert at the bottom 
    terminal_list.yview(END)    #move scrollbar along with text
    terminal_list['state'] = DISABLED

def help_output():
    help_list = ['\n----------------------------------------',
                 '  -v              program version',
                 '  -acc        account information',
                 '  -dev        device information',
                 '  -add more stuff later',
                 '----------------------------------------'
                ]
    for i in help_list:
        terminal_list.insert(END, i + '\n')
        terminal_list.yview(END)

'''MQTT Callbacks'''
def on_log(client, userdata, level, buf):
    terminal_print(buf)
    
def on_publish(client, userdata, mid):
    '''MQTT published message callback'''
    terminal_print(str(mid))

def on_message(client, userdata, msg):
    '''MQTT message receive callback'''
    global curr_msg_topic

    #neatly organize the messages and place them in the messages tab and retain them
    curr_msg_topic = msg.topic
    check_message(msg.payload.decode('utf-8'), curr_msg_topic)

def on_unsubscribe(client, userdata, mid):
    '''MQTT topic unsubscribe callback'''
    pass 
    #print('\nUnsubscribed.', mid)

def on_subscribe(client, userdata, mid, granted_qos): 
    '''MQTT topic subscribe callback'''
    insert_treeview_topic()

    if auto_sub_flag == 1:  #callback is for topics that were automatically subscribed in the beginning
        return 

    tab1_sub_to_topic.delete(0,END) #clear entry box
    tab1_subscribed_list.insert(END, topic) #add topic to listbox for subscribed topics

def on_connect(client, userdata, flags, rc):
    '''MQTT broker connect callback.'''
    global subscribed_topics_list

    if rc == mqtt.CONNACK_ACCEPTED:
        client.connected_flag = True 
    
        '''If the program reconnects by itself, we need to unsubscribe from all topics and re-subscribe to them
        after. This means we need to clear our list array that holds the subscribed topics but keep the 
        config parser file to remember what to subscribe back to.'''
        if subscribed_topics_list:  #if not empty
            for topic in subscribed_topics_list:
                client.unsubscribe(topic)    #unsubcribe from all subscribed topics
            subscribed_topics_list.clear() #clear subscription list
        
        #check if we have a file saved for list of subscribed topics from previous session if applicable
        check_subscribed_topics()

    else:
        print("Bad connection. Returned code = ", rc)

'''My MQTT Actions'''
def auto_subscribe(value):
    global auto_sub_flag
    global address

    address = str(value)
    auto_sub_flag = 1
    terminal_print("Auto-subscribing to: " + value)
    client.subscribe(value, qos=0)
    auto_sub_flag = 0

    tab1_subscribed_list.insert(END, value) #and add to listbox

def do_publish():
    if client_flag == 0:
        terminal_print('Please select a target device.')
        return  
    topic = tab2_topic_input.get() #grab what was in topic entry textbox
    address = topics.compare_pubs(topic, mqtt_topic_prefix, target_device)   #obtain address of topic
    user_msg = tab2_msg_input.get()    #grab what was in the msg entry textbox
    msg_to_pub = pub_message_check(user_msg)

    client.publish(topic=address, payload=json.dumps(msg_to_pub), qos=0, retain=True) #publish message to topic 
    tab2_topic_input.delete(0,END)  #clear entry box
    tab2_msg_input.delete(0,END) #clear entry box

def do_unsubscribe():
    global address

    if client_flag == 0:
        terminal_print(text='Please select a target device.')
        return

    topic = tab1_sub_to_topic.get() #grab user input from entry box
    address = topics.compare_subs(topic, mqtt_topic_prefix, target_device)
    client.unsubscribe(address)   #unsubscribe to topic
    tab1_sub_to_topic.delete(0,END) #clear entry box
    tab1_subscribed_list.delete(ANCHOR)

    #check if it's in our list of subscribed topics
    if address in subscribed_topics_list:
        subscribed_topics_list.remove(address)  #delete from our subscribed topics list
        
        with open('saved_topics.ini', 'r') as topic_configfile:
            topic_config.read_file(topic_configfile)

        for key in topic_config[account_type]:    #and delete from file
            if key == address:
                topic_config.remove_option(account_type, key)
        with open('saved_topics.ini', 'w') as topic_configfile:
            topic_config.write(topic_configfile)

def do_subscribe(): #client.subscribe() work in here
    global topic
    global tab1_subscribed_list
    global address

    if client_flag == 0:
        terminal_print('Please select a target device.')
        return 
    topic = tab1_sub_to_topic.get() #grab what was typed in the sub_to_topic entry box
    address = topics.compare_subs(topic, mqtt_topic_prefix, target_device) #function to compare topics to get their actual address if selected from listbox
    terminal_print("Address: " + address)

    #check if it's in our list of subscribed topics
    if address not in subscribed_topics_list:   #make sure there's no duplicates
        subscribed_topics_list.append(address)  #add to our subscribed topics list

        client.subscribe(address, qos=0)


        topic_config[account_type][address] = ''   #and add to file
        #topic_config[account_type][target_device] = {address}  #use this for  
        with open('saved_topics.ini', 'w') as topic_configfile:
            topic_config.write(topic_configfile)
    else:
        terminal_print('Already subscribed to topic.')
    
        
def check_subscribed_topics():
    file_exists = os.path.exists('saved_topics.ini')
    if file_exists is not True:  #create file and add section for subscribed topics
        topic_config['Prod'] = {}
        topic_config['Beta'] = {}
        topic_config['Dev'] = {}
        topic_config['Feat'] = {}

        with open('saved_topics.ini', 'w') as topic_configfile:
            topic_config.write(topic_configfile)

    else:   #parse existing file
        topic_config.read('saved_topics.ini')
        subscribed_topics = topic_config[account_type]

        if subscribed_topics == '': #nothing to subscribe to, move on
            return
        else:
            for value in topic_config[account_type]:  #for loop to send each topic to subscribe function
                subscribed_topics_list.append(value)  #also store the topic in a list 
                auto_subscribe(value)
                print('subscribed list:', subscribed_topics_list)

def pub_message_check(msg): #user custom message
    if msg == '' or msg == '{None}':
        msg = None
    else:
        msg = msg
    return msg

def check_message(message, curr_msg_topic):  #function to handle exceptions
    #print("Raw data: ", message)
    #print(type(message))
    try:
        unpacked_json = json.loads(message)
    except Exception as e:
        print("Couldn't parse raw data: %s" % message, e)
    else:
        print("JSON:", unpacked_json)
        sort_message(unpacked_json, curr_msg_topic)

def sort_message(unpacked_json, curr_msg_topic):       
    message_array = []
    
    '''
    The for-loop below used to work without issues, but now it's giving an error depending on
    which message we receive. 
    Error msg: "Caught exception in on_message: 'list' object has no attribute 'items'"
    '''

    for key, value in unpacked_json.items():    #iterate for single key-value pair
        if isinstance(value, dict):
            for key2, value2 in value.items():  #iterate for a value with value
                value2 = str(value2)
                value2 = value2.strip('{}')     #this gets rid of brackets for "networkInfo"
                
                #Unable to pick "lte" apart
                if isinstance(value2, dict):
                    for key3, value3 in value2.items():  #iterate for a value with a value with value
                        print('third iteration: ', key3, ':', value3)
                        value3 = str(value3)
                        value3 = value3.strip('{}')
                        curr_line = key3 + ':' + str(value3)
                        message_array.append(curr_line)
                else:
                    print("is instance 2: {0} : {1}".format(key2, value2))
                    curr_line = key2 + ':' + str(value2)
                    message_array.append(curr_line)    
        else:
            curr_line = key + ': ' + str(value)
            message_array.append(curr_line)
    print('\n')

    message_array = [x for x in message_array if not x.startswith('lte')]   #just going to completely ignore 'lte' and everything after it for now
    print('message array:', message_array)
    output_messages(message_array, curr_msg_topic)  #pass to function to put into message tab

    
    #plot for "activity"? Everytime we go through here, put a point on the plot vs. time
    #Also read message array here to pull out whatever data we need to plot on the graph vs time
    #i.e. if "voltage" exists in the array, find the key "data" and grab that value out to plot (send to plots.py)
    #for key "appId" = RSRP value, get value of key "data"
    #or              = VOLTAGE, get value of key "data" 


def insert_treeview_topic():
    global curr_msg_topic

    tab3_topic = [] #list for topics in Treeview in Tab3
    curr_msg_topic = address
    if topic not in tab3_topic:
        if topic == None:  #for initial subscriptions in the beginning of program
            short_topic = '...' + address[-10:]  #only show the last 10 characters of a topic
            
            tab3_tree.insert("", END, iid=curr_msg_topic, text=short_topic)
            tab3_topic.append(address)
            
            print('1:', tab3_topic)
            print('address:', address)
        else:

            short_topic = '...' + address[-10:]
            tab3_tree.insert("", END, iid=curr_msg_topic, text=short_topic, tags='topic')     #parent
            tab3_topic.append(topic)
            
            print('2:', tab3_topic)
            print('topic:', topic)

def output_messages(message_array, curr_msg_topic):
    count_msg = 1   #start at 1 to account for the blank line
    curr_msg_topic = str(curr_msg_topic)
    children = tab3_tree.get_children(curr_msg_topic)
    message_count = len(children)

    print('children: ', children)
    print('message count1:', message_count)

    if message_count > 20:  #limit 20 messages per topic
        for record in reversed(children): #reverse, delete oldest record (starting from [0]) and increase all other records by 1
            oldest_item = tab3_tree.index(record)
            if record == oldest_item:
                tab3_tree.delete(record)

            tab3_tree.move(record, tab3_tree.parent(record), tab3_tree.index(record)+1) #move everything else down
    
    #insert messages in Treeview in its appropriate topic section
    for i in message_array:
        tab3_tree.insert(parent=curr_msg_topic, index=0, values=i, tags='dark')    #child, insert from top
        count_msg = count_msg + 1
    print(count_msg)

    tab3_tree.insert(parent=curr_msg_topic, index=0, values='', tags='light') #blank line in between chunk of messages
    

'''Tab 2 Stuff'''
def tab2_update_msgBox(data):   #add list of messages into box
    tab2_messages_list.delete(0,END)
    for item in data:
        tab2_messages_list.insert(END, item)

def tab2_update_listBox(data):   #update the listbox
    tab2_listBox.delete(0,END)    #clear the listbox
    for item in data:   #add topics to listbox
        tab2_listBox.insert(END, item)

def do_clear2():
    tab2_topic_input.delete(0,END)  #clear entry box
    tab2_msg_input.delete(0,END) #clear entry box
    event_clicks.tab2_insert_shadow_text_left(tab2_topic_input)   #put shadow texts back in
    event_clicks.tab2_insert_shadow_text_right(tab2_msg_input)
    
def tab2_fillout_msg(e):
    tab2_msg_input.delete(0,END)
    tab2_msg_input.insert(0, tab2_messages_list.get(ANCHOR))
    tab2_msg_input.config(fg='black')

def tab2_fillOut(e):
    tab2_topic_input.delete(0,END)    #delete whatever is in entry box
    tab2_topic_input.insert(0, tab2_listBox.get(ANCHOR))  #add clicked list item to listbox
    tab2_topic_input.config(fg='black')

'''Tab 1 Stuff'''
def do_clear():
    tab1_sub_to_topic.delete(0,END)
    event_clicks.tab1_insert_shadow_text(tab1_sub_to_topic) #insert shadow text

def tab1_fillOut_sub(e):
    global subscribed_list
    subscribed_list = []
    
    tab1_sub_to_topic.delete(0,END) #clear bottom box
    tab1_sub_to_topic.insert(0, tab1_subscribed_list.get(ANCHOR))   
    tab1_sub_to_topic.config(fg='black')
    subscribed_list.append(tab1_subscribed_list.get(ANCHOR))

def tab1_fillOut(e):
    tab1_sub_to_topic
    tab1_sub_to_topic.delete(0,END)    #clear bottom entry box
    tab1_sub_to_topic.insert(0, tab1_listBox.get(ANCHOR))  #add clicked list item to listbox
    tab1_sub_to_topic.config(fg='black')

def tab1_update_listBox(data):   #update the listbox
    tab1_listBox.delete(0,END)    #clear the listbox
    for item in data:   #add topics to listbox
        tab1_listBox.insert(END, item)

def tab1_checkKeyPress(e):
    typed = tab1_searchBar.get() #grab what was typed in the search bar
    if typed == '':     #nothing was typed
        data = sub_topic_list
    else:
        data = []
        for item in sub_topic_list:
            if typed.lower() in item.lower(): #convert everything to lowercase
                data.append(item)
    tab1_update_listBox(data)    #update listbox with selected topics

def change_device(*args):
    global target_device
    global device_specifics 
    global device_info
    global client_flag
    global first_start_flag2

    device_specifics = []
    target_device = device_list.get()   #get user selection from dropdown menu

    if client_flag == 0:    #not connected to MQTT broker
        if target_device == 'Select Device...':
            device_info['state'] = NORMAL 
            device_info.delete(1.0, END)
            device_info.insert(END, select_message, "align")
            device_info['state'] = DISABLED 
            return    #device not selected, do nothing
        elif target_device != 'Select Device...':
            pass    #selected a device, continue with bottom code to grab device info 
    if client_flag == 1:    #connected to MQTT broker
        if target_device == 'Select Device...': #no device selected
            target_device = None    #disconnect target device and from MQTT broker
            client_flag = 0         
            client.disconnect()
            client.loop_stop()
            if first_start_flag2 == 0:
                first_start_flag2 = first_start_flag2 + 1
                return 

            device_info['state'] = NORMAL 
            device_info.delete(1.0, END)
            device_info.insert(END, select_message, "align")
            device_info['state'] = DISABLED 
            return 

        elif target_device != 'Select Device...':   #switching from one device to another
            client.disconnect() #disconnect from the current device before switching
            client.loop_stop()  #then continue with bottom code
    #change device details depending on the device selected
    for device in http_get['items']:
        if device['id'] == target_device:
            separate = 'T'  #delete T and everything after it, only want the date
            createdDate = device['$meta']['createdAt']
            createdDate = createdDate.split(separate, 1)[0]
            device_specifics = ['Dev ID: ' + device['id'],                           
                                #'Dev Name: ' + device['name'],
                                'Type: ' + device['type'],
                                'Subtype: ' + device['subType'],
                                'Created On: ' + createdDate,
                                'Version: ' + device['$meta']['version']
                                ]
    devText = '\n'.join(device_specifics)

    device_info['state'] = NORMAL 
    device_info.delete(1.0, END)
    device_info.insert(END, devText)
    device_info['state'] = DISABLED 
    
    connectMQTT()   #connect to MQTT broker

def tab3_layout(tab3):
    global tab3_tree

    #tab3 layout: left column for treeview and right for plots
    tab3.columnconfigure(0, weight=2)
    tab3.columnconfigure(1, weight=1)
    tab3.rowconfigure(0, weight=1)
    
    #frame for left column
    tab3_layout_left = Frame(tab3, highlightthickness=0, borderwidth=0)
    tab3_layout_left.grid(column=0, row=0, padx=5, pady=10, sticky=W+E+N+S)

    #use Treeview widget on Messages tab to display hierarchical collection of items
    tab3_tree = ttk.Treeview(tab3_layout_left, columns=(1,2), show='tree headings')
    tab3_tree_scroll = Scrollbar(tab3_layout_left, orient=VERTICAL, command=tab3_tree.yview)    
    tab3_tree.config(yscrollcommand=tab3_tree_scroll.set)
    tab3_tree_scroll.pack(side=RIGHT, fill=Y)
    tab3_tree.pack(padx=5, pady=5, fill=BOTH, expand=TRUE)

    #set up columns with titles
    tab3_tree.heading("#0", text='Topics')
    tab3_tree.heading(1, text='Messages')
    tab3_tree.heading(2, text='Data')

    tab3_tree.column('#0', width=95, anchor=W)
    tab3_tree.column(1, anchor=W)
    tab3_tree.column(2, anchor=W)

    style2 = ttk.Style()
    style2.configure("Treeview.Heading", font=(myFont, 10, 'bold'), background=lighter_grey, foreground=nordic_blueslate)
    style2.configure("Treeview", font=(myFont, 10), background='white')

    tab3_tree.tag_configure('topic', font=(myFont, 10, 'bold'), background=lighter_grey, foreground=nordic_blueslate)
    tab3_tree.tag_configure('light', background='#E8E8E8')
    tab3_tree.tag_configure('dark', background='#DFDFDF')

    
    #frame for right column (plots)
    tab3_layout_right = Frame(tab3)
    tab3_layout_right.grid(padx=5, pady=10, column=1, row=0, sticky=W+E+N+S)

    tab3_layout_right.columnconfigure(0, weight=1, uniform=1)
    tab3_layout_right.rowconfigure(0, weight=1, uniform=1)
    tab3_layout_right.rowconfigure(1, weight=1, uniform=1)

    #function for plot1
    plots.graph1(tab3_layout_right)
    #function for plot2
    plots.graph2(tab3_layout_right)
    

    '''   DETAILS
    Treeview widget on left side of frame
    -Depending on which topic is expanded:
    # (1) parent: topic 
    # (1) first child: most recent message
        # and the details
        # color code each one 
    # (1) second child: attach a "link" that opens up a pop-up listing all messages with scrollbar 
    # save messages to a .txt file or something, cap at (50)msgs 
    
    # if another topic is subbed to, create another parent tree for that topic:
    # (2) parent: topic
    # (2) first child: most recent message
    # etc.

    # we just need one function to create parents and its children - just iterate when
    # subscribing to topic/remove when unsubscribing

    The right side will include graphs/visuals?
    For the plot:
    # retrieve message
    # grab the specific data value
    # update data with line.set_data()
    # update canvas with canvas.draw()

    # remember subscribed topics so when we select a device, we automatically subscribe to them again
    # save to .txt file 
    # write a new function that will read from that file every time we select a device
    # to check if there are any topics we were watching previously
    
    '''

def tab2_layout(tab2):
    global tab2_listBox
    global tab2_msg_input
    global tab2_topic_input
    global tab2_messages_list

    #tab2 layout
    tab2.columnconfigure(tuple(range(7)), weight=1) #eight columns
    tab2.rowconfigure(tuple(range(3)), weight=1)    #three rows

    tab2_select_label = Label(tab2, text='Select a topic to send a message to: ')
    tab2_select_label.config(font=(myFont, 13), background=myGrey)
    tab2_select_label.grid(column=0, row=0, columnspan=4, padx=(0,5), pady=(15,0), ipady=5, sticky=N+S)

    tab2_listbox_border = Frame(tab2, background='white')
    tab2_listbox_border.grid(column=0, row=1, columnspan=4, rowspan=2, padx=(40,5), pady=(5,15),
                        sticky=W+E+N+S)

    tab2_listBox = Listbox(tab2_listbox_border, borderwidth=0, highlightthickness=0, background='white')
    tab2_scroll = Scrollbar(tab2_listbox_border, orient=VERTICAL, command=tab1_listBox.yview)
    tab2_listBox.config(font=(myFont, 12), yscrollcommand=tab2_scroll.set, relief=RAISED, 
                        selectbackground='#737c7d')
    
    tab2_scroll.pack(side=RIGHT, fill=Y)
    tab2_listBox.pack(padx=20, pady=20, fill=BOTH, expand=TRUE)

    #create list of "Publish" topics to insert into Listbox
    pub_topic_list = [
        '{device_id}/shadow/get/accepted',
        '$aws/things/{device_id}/shadow/get/rejected',
        '$aws/things/{device_id}/shadow/update/delta',
        'mqtt_topic_prefix/m/d/{device_id}/c2d',
        'mqtt_topic_prefix/{device_id}/jobs/rcv',
        'm/#',
        'a/connections'
    ]
    tab2_update_listBox(pub_topic_list)  #add topics to our list
    tab2_listBox.bind("<<ListboxSelect>>", tab2_fillOut)  #create a binding on the listbox onclick

    tab2_help = Label(tab2, text="[ Help ]", background='#80AABA', foreground='white')
    tab2_help.config(font=(myFont, 12), borderwidth=1, relief='raised', anchor=CENTER, justify=LEFT)
    tab2_help.grid(column=0, row=3, padx=(40,0), pady=(5,15), ipadx=2, sticky=N+S)
    ToolTip(tab2_help, msg='Click on a topic and a message\nabove to auto-fill or manually\ntype into the textbox.',
            background='#AEDAEB', font=(myFont, 12), follow=True)

    tab2_topic_input = Entry(tab2)  #this is for the topic
    tab2_topic_input.config(font=(myFont, 12))
    tab2_topic_input.insert(0, 'Enter a topic...')  #insert shadow text
    tab2_topic_input.grid(column=1, row=3, columnspan=3, padx=5, pady=(5,15), sticky=W+E)

    #remove/show shadow text when in or out of focus
    tab2_topic_input.bind('<FocusIn>', tab2_on_entry_click_left)
    tab2_topic_input.bind('<FocusOut>', tab2_entry_focus_out_left)
    tab2_topic_input.config(fg='grey')

    tab2_msg_input = Entry(tab2)    #this is for the message
    tab2_msg_input.config(font=(myFont, 12))
    tab2_msg_input.insert(0, 'Enter a message...')  #insert shadow text
    tab2_msg_input.grid(column=4, row=3, columnspan=2, pady=(5,15), sticky=W+E)

    #remove/show shadow text when in or out of focus
    tab2_msg_input.bind('<FocusIn>', tab2_on_entry_click_right)
    tab2_msg_input.bind('<FocusOut>', tab2_entry_focus_out_right)
    tab2_msg_input.config(fg='grey')

    #clear button to clear entry
    tab2_clear_button = Button(tab2, text='Clear', command=do_clear2,
                            activeforeground='white', activebackground='#9ed3e8')
    tab2_clear_button.grid(column=6, row=3, padx=5, pady=(0,15), sticky=W+E+N+S)
    #make publish button go to publish function and clear entries
    tab2_publish_button = Button(tab2, text="Publish", command=do_publish, background=nordic_blue,
                               foreground='white', activeforeground='white', activebackground='#9ed3e8')
    tab2_publish_button.grid(column=7, row=3, padx=(0,40), pady=(0,15), ipadx=20, sticky=W+E+N+S)

    button_config(tab2_clear_button)
    button_config(tab2_publish_button)

    #common messages label
    tab2_msgs_label = Label(tab2, text='Common Messages')
    tab2_msgs_label.config(font=(myFont, 12), background=myGrey, anchor=CENTER, relief=GROOVE)
    tab2_msgs_label.grid(column=4, row=0, columnspan=4, padx=(0,40), pady=(15,0), ipadx=100, ipady=1, sticky=N+S)

    #list of messages
    tab2_messages_border = Frame(tab2, background='white')
    tab2_messages_border.grid(column=4, row=1, columnspan=4, rowspan=2, padx=(10,40), pady=(5,15),
                        sticky=W+E+N+S)

    tab2_messages_list = Listbox(tab2_messages_border, borderwidth=0, highlightthickness=0, background='white')
    tab2_msgsList_scroll = Scrollbar(tab2_messages_border, orient=VERTICAL, command=tab1_listBox.yview)
    tab2_messages_list.config(font=(myFont, 12), yscrollcommand=tab2_msgsList_scroll.set, relief=RAISED, 
                        selectbackground='#737c7d')
    tab2_msgsList_scroll.pack(side=RIGHT, fill=Y)
    tab2_messages_list.pack(padx=20, pady=20, fill=BOTH, expand=TRUE)
    tab2_messages_list.bind("<<ListboxSelect>>", tab2_fillout_msg)  #create a binding on the listbox onclick

    #insert list of possible messages to publish
    message_options = [
        '{appId:Type}',
        '{None}'
    ]
    tab2_update_msgBox(message_options)  #add topics to our list
    tab2_messages_list.bind("<<ListboxSelect>>", tab2_fillout_msg)  #create binding

def tab1_layout(tab1):
    global tab1_listBox
    global tab1_searchBar
    global tab1_sub_to_topic
    global sub_topic_list
    global tab1_subscribed_list

    #tab1 layout
    tab1.columnconfigure(tuple(range(7)), weight=1) #eight columns
    tab1.rowconfigure(tuple(range(3)), weight=1)    #three rows

    tab1_search = Label(tab1, text='Search: ')
    tab1_search.config(font=(myFont, 13), background=myGrey)
    tab1_search.grid(column=0, row=0, padx=(0,5), pady=(18,0), sticky=E+N+S)

    tab1_searchBar = Entry(tab1)
    tab1_searchBar.config(font=(myFont, 12))
    tab1_searchBar.grid(column=1, row=0, columnspan=3, padx=(0,5), pady=(20,0), sticky=W+E)

    tab1_listbox_border = Frame(tab1, background='white')
    tab1_listbox_border.grid(column=0, row=1, columnspan=4, rowspan=2, padx=(40,5), pady=(5,15),
                        sticky=W+E+N+S)

    tab1_listBox = Listbox(tab1_listbox_border, borderwidth=0, highlightthickness=0, background='white')
    tab1_scroll = Scrollbar(tab1_listbox_border, orient=VERTICAL, command=tab1_listBox.yview)
    tab1_listBox.config(font=(myFont, 12), yscrollcommand=tab1_scroll.set, relief=RAISED, 
                        selectbackground='#737c7d')
    
    tab1_scroll.pack(side=RIGHT, fill=Y)
    tab1_listBox.pack(padx=(20,5), pady=20, fill=BOTH, expand=TRUE)

    #create list of topics to insert into Listbox
    sub_topic_list = [
        '$aws/things/{device_id}/shadow/get',
        '$aws/things/{device_id}/shadow/update',
        'mqtt_topic_prefix/m/d/{device_id}/d2c',
        'mqtt_topic_prefix/m/d/{device_id}/d2c/bulk',
        'mqtt_topic_prefix/{device_id}/jobs/req',
        'mqtt_topic_prefix/{device_id}/jobs/update',
        'mqtt_topic_prefix/m/#'
        ]
    tab1_update_listBox(sub_topic_list)  #add topics to our list
    tab1_listBox.bind("<<ListboxSelect>>", tab1_fillOut)  #create a binding on the listbox onclick

    tab1_searchBar.bind("<KeyRelease>", tab1_checkKeyPress) #create binding for keys pressed while active on search bar

    tab1_sub_to_topic = Entry(tab1)
    tab1_sub_to_topic.config(font=(myFont, 12))
    tab1_sub_to_topic.insert(0, 'Enter a topic...')
    tab1_sub_to_topic.grid(column=0, row=3, columnspan=5, padx=(40,1), pady=(5,15), sticky=W+E)
    
    #remove/show shadow text when in or out of focus
    tab1_sub_to_topic.bind('<FocusIn>', tab1_on_entry_click)
    tab1_sub_to_topic.bind('<FocusOut>', tab1_entry_focus_out)
    tab1_sub_to_topic.config(fg='grey')

    #clear button to clear entry
    tab1_clear_button = Button(tab1, text='Clear', command=do_clear,
                               activeforeground='white', activebackground='#9ed3e8')
    tab1_clear_button.grid(column=5, row=3, padx=(5,0), pady=(0,15), sticky=W+E+N+S)
    #make subscribe button go to subscribe function and clear sub_to_topic Entry
    tab1_sub_button = Button(tab1, text="Subscribe", command=do_subscribe, background=nordic_blue,
                               foreground='white', activeforeground='white', activebackground='#9ed3e8')
    tab1_sub_button.grid(column=6, row=3, padx=5, pady=(0,15), sticky=W+E+N+S)
    #make unsubscribe button go to unsubscribe function and clear sub_to_topic Entry
    tab1_unsub_button = Button(tab1, text="Unsubscribe", command=do_unsubscribe, background=nordic_lake,
                                foreground='white', activeforeground='white', activebackground='#9ed3e8')
    tab1_unsub_button.grid(column=7, row=3, padx=(0,40), pady=(0,15), sticky=W+E+N+S)
    
    button_config(tab1_clear_button)
    button_config(tab1_sub_button)
    button_config(tab1_unsub_button)

    #subscribed topics label
    tab1_subbed_topics_label = Label(tab1, text='Subscribed Topics ')
    tab1_subbed_topics_label.config(font=(myFont, 12), background=myGrey, anchor=CENTER, relief=GROOVE)
    tab1_subbed_topics_label.grid(column=4, row=0, columnspan=4, padx=(0,40), pady=(15,0), ipadx=100, ipady=4)

    #list of subscriptions box
    tab1_subscribedList_border = Frame(tab1, background='white')
    tab1_subscribedList_border.grid(column=4, row=1, columnspan=4, rowspan=2, padx=(10,40), pady=(5,15),
                        sticky=W+E+N+S)

    tab1_subscribed_list = Listbox(tab1_subscribedList_border, borderwidth=0, highlightthickness=0, background='white')
    tab1_second_scroll = Scrollbar(tab1_subscribedList_border, orient=VERTICAL, command=tab1_subscribed_list.yview)
    tab1_third_scroll = Scrollbar(tab1_subscribedList_border, orient=HORIZONTAL, command=tab1_subscribed_list.xview)
    tab1_subscribed_list.config(font=(myFont, 12), yscrollcommand=tab1_second_scroll.set, relief=RAISED, 
                        xscrollcommand=tab1_third_scroll.set, selectbackground='#737c7d')
    tab1_second_scroll.pack(side=RIGHT, fill=Y)
    tab1_third_scroll.pack(side=BOTTOM, fill=X)
    tab1_subscribed_list.pack(padx=20, pady=20, fill=BOTH, expand=TRUE)
    
    tab1_subscribed_list.bind("<<ListboxSelect>>", tab1_fillOut_sub)  #create a binding on the listbox onclick

def create_right_frame(container):
    global terminal_list
    global terminal_input
    global first_start_flag

    frame = Frame(container, background=light_grey)
    frame.columnconfigure(0, weight=1)      #one column
    frame.rowconfigure(tuple(range(3)), weight=1)    #four rows

    if first_start_flag==0: #only run through this function once
        first_start_flag = 1
        themes.tab_theme() #set custom theme for tabs

    #create sub/pub/msgs tabs
    tabs = Notebook(frame)
    tabs.grid(column=0, row=0, rowspan=2, padx=10, pady=10, sticky=W+E+N+S)

    tab1 = Frame(tabs) 
    tab2 = Frame(tabs)
    tab3 = Frame(tabs)
    
    tab1.config(background=myGrey)
    tab2.config(background=myGrey)
    tab3.config(background=myGrey)

    tab1.pack(expand=True, fill=BOTH)
    tab2.pack(expand=True, fill=BOTH)
    tab3.pack(expand=True, fill=BOTH)

    tabs.add(tab1, text='Subscribe')    #add frames to notebook
    tabs.add(tab2, text='Publish')
    tabs.add(tab3, text='Messages')
    
    tab1_layout(tab1)    #put stuff in each tab
    tab2_layout(tab2)
    tab3_layout(tab3)

    #user terminal - redirect -UBACKS to this frame; connects, subscribes, publishes, messages
    terminal_border = Frame(frame, background=dark_grey)
    terminal_border.grid(column=0, row=2, padx=10, pady=(10,0), 
                        ipadx=20, ipady=20, sticky=W+E+N+S)
    
    terminal_list = Text(terminal_border, height=15, borderwidth=0, highlightthickness=0, wrap=CHAR)
    terminal_scroll = Scrollbar(terminal_border, orient=VERTICAL, command=terminal_list.yview)
    terminal_list.config(font=(myFont, 11), background=dark_grey, foreground='white', 
                        yscrollcommand=terminal_scroll.set)
    terminal_scroll.pack(side=RIGHT, fill=Y)
    terminal_list.pack(padx=10, pady=(10,0), fill=BOTH, expand=TRUE)

    terminal_print("Welcome! Select a device to get started.")  #first line in terminal
    terminal_print("Type /help for more information.")
    terminal_list['state'] = DISABLED

    #textbox for user terminal
    terminal_input_frame = Frame(frame, background=light_grey)
    terminal_input_frame.grid(column=0, row=3, padx=10, ipadx=2, ipady=1, sticky=W+E+N+S)

    terminal_input = Entry(terminal_input_frame)
    terminal_input.config(font=(myFont, 14), background='#d9d9d9')
    terminal_input.pack(padx=(0,5), pady=(0,8), fill=BOTH, expand=TRUE, side=LEFT)

    #enter terminal button
    terminal_enter_button = Button(terminal_input_frame, text='Enter', command=terminal_enter) 
    terminal_enter_button.config(background=nordic_blue, activebackground='#345',
                                 foreground='white', activeforeground='white')
    terminal_enter_button.pack(padx=(0,5), pady=(0,8), ipadx=15, fill=None, expand=FALSE, side=LEFT)
    button_config(terminal_enter_button)

    #clear terminal button
    terminal_clear_button = Button(terminal_input_frame, text='Clear', command=terminal_clear) 
    terminal_clear_button.config(activebackground='#345', activeforeground='white')
    terminal_clear_button.pack(padx=(0,5), pady=(0,8), ipadx=15, fill=None, expand=FALSE, side=LEFT)
    button_config(terminal_clear_button)

    #bind "Enter" key event with terminal_input
    terminal_input.bind('<Return>', terminal_enter_event)  #bind enter key with event function

    '''
    For the user terminal textbox,
    If the user types in something that is saved/valid for our 
    program, we will print something out on the terminal.
    (i.e. /help will output all possible commands for our interface
          /listdevices will output all devices in that account
          /accountinfo will output mqtt account info
          etc.)
    
    If the user types in something we don't know, just do nothing.
    Everytime the user hits "enter", print out what was typed and clear the entry box
    '''

    for widget in frame.winfo_children():
        widget.grid(padx=5, pady=3)
    return frame

def create_left_frame(container):
    global device_list
    global device_info
    global select_message

    frame = Frame(container)
    frame.columnconfigure(0, weight=1)      #one column
    for i in range(7):      
        frame.rowconfigure(i, weight=1)    #eight rows
    
    frame.option_add("*Background", 'white')
    frame.option_add("*Foreground", 'black')

    '''
    #nRF Cloud logo *****INCOMPLETE, try to make transparent
    nrfLogo = ImageTk.PhotoImage(Image.open("nrfcloud_logo.png"))
    logo = Label(frame, image=nrfLogo)
    logo.config(background='#748587')
    logo.grid(row=0, column=0, padx=(5), pady=(5), sticky=W+E+N+S)
    '''

    #(0,0) select device drop down menu at top left
    device_options = []
    device_list = StringVar()
    device_list.trace('w', change_device)
    device_list.set("Select Device...")
   
    device_options.append('Select Device...')
    for device in http_get['items']:
        if device['id'].startswith('nrf-'): #only include devices and not account device
            device_options.append(device['id'])    #put device IDs in device_list array

    select_device_frame = Frame(frame, borderwidth=2, relief="ridge")
    select_device_frame.grid(column=0, row=0, padx=10, pady=(10,0), sticky=W+E+N+S)

    select_device = OptionMenu(select_device_frame, device_list, *device_options)  #dropdown menu
    select_device.config(font=(myFont, 12), background=nordic_blue, foreground='white')
    select_device['menu'].configure(bg='#d6d6d6', bd=0, font=(myFont, 12))
    select_device.pack(fill=BOTH, expand=TRUE)

    #(0,1) below that, account and device information
    device_info_frame = Frame(frame, background='#0f5d73', borderwidth=2, relief=RAISED)
    device_info_frame.grid(column=0, row=1, rowspan=2, padx=(30,20), pady=(0,10))

    device_info = Text(device_info_frame, background='#0f5d73', foreground='white', width=25, height=7, wrap=WORD)
    device_info.config(highlightthickness=0, borderwidth=0, font=(myFont, 10), spacing1=5, spacing2=2, spacing3=2)
    device_info.pack(padx=15, pady=(7,3), fill=BOTH, expand=TRUE)
    device_info.tag_configure("align", justify='center')
    device_info.tag_configure("bold", font=(None, 10, BOLD))

    select_message = "\n\nSelect device above\n for more information."
    device_info.insert(END, select_message, "align")
    device_info['state'] = DISABLED

    #(0,3) mqtt user information
    mqtt_info_frame = Frame(frame, borderwidth=2, relief=RAISED, background='#186e99')
    mqtt_info_frame.grid(column=0, row=3, rowspan=3, padx=(30,20))
    
    mqtt_info = Text(mqtt_info_frame, background='#186e99', foreground='white', width=25, height=10, wrap=CHAR)
    mqtt_info.config(highlightthickness=0, borderwidth=0, font=(myFont, 10), spacing1=5, spacing2=2, spacing3=2)
    mqtt_info.pack(padx=15, pady=(10,10), fill=BOTH, expand=TRUE)
    mqtt_info.tag_configure("align", justify='center')      #configure tags
    mqtt_info.tag_configure("bold", font=(None, 10, BOLD))
    mqtt_info.tag_configure("spacing", font=(None, 3,))

    mqtt_endpoint_text = 'MQTT Endpoint:'
    mqtt_topic_prefix_text = 'MQTT Topic Prefix:'
    mqtt_client_id_text = 'MQTT Client ID:'

    mqtt_info.insert(END, mqtt_endpoint_text + '\n', "bold")
    mqtt_info.insert(END, mqtt_endpoint + '\n')
    mqtt_info.insert(END, '\n', "spacing")
    mqtt_info.insert(END, mqtt_topic_prefix_text + '\n', "bold")
    mqtt_info.insert(END, mqtt_topic_prefix + '\n')
    mqtt_info.insert(END, '\n', "spacing")
    mqtt_info.insert(END, mqtt_client_id_text + '\n', "bold")
    mqtt_info.insert(END, client_id)
    
    mqtt_info.tag_add("align", 1.0, END)
    mqtt_info['state'] = DISABLED

    #(0,4) show account type
    account_type_frame = Frame(frame, borderwidth=2, relief=RAISED, background='#298b9e')
    account_type_frame.grid(column=0, row=6, padx=(30,20))

    account_type_text = Text(account_type_frame, background='#298b9e', foreground='white', width=25, height=2, wrap=CHAR)
    account_type_text.config(highlightthickness=0, borderwidth=0, font=(myFont, 10), spacing1=5, spacing2=2, spacing3=2)
    account_type_text.pack(padx=15, pady=7, fill=BOTH, expand=TRUE)
    account_type_text.tag_configure("align", justify='center')  #configure tags
    account_type_text.tag_configure("bold", font=(None, 10, BOLD))

    account_type_label = 'Account Type:'

    account_type_text.insert(END, account_type_label + '\n', "bold")
    account_type_text.insert(END, account_type)
    account_type_text.tag_add("align", 1.0, END)    #center all
    account_type_text['state'] = DISABLED 

    #(0,7) bottom left, log off button
    log_off_frame = Frame(frame, background=light_grey)
    log_off_frame.grid(column=0, row=7, padx=10, pady=15, sticky=W+E+S)

    log_off = Button(log_off_frame, text="Log Off", command=restartPopup)
    log_off.config(activebackground='#9ed3e8', activeforeground='white', background='#505f63', foreground='white')
    log_off.pack(pady=(0,10), fill=BOTH, expand=TRUE)
    button_config(log_off)

    for widget in frame.winfo_children():
        widget.grid(padx=5, pady=1)
    return frame

def main_screen():
    '''Main Screen Configuration'''  
    root.deiconify()    #show main page
    if first_start_flag == 0:   #only build once
        #build two frames for main window
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=6)
        root.rowconfigure(0, weight=1)

        left_frame = create_left_frame(root)
        left_frame.config(background=light_grey)
        left_frame.grid(column=0, row=0, sticky=W+E+N+S)

        right_frame = create_right_frame(root)
        right_frame.config(background=light_grey)
        right_frame.grid(column=1, row=0, sticky=W+E+N+S)

def edit_config_file(flag, data): #store new values into file
    if flag == 1:   #store into API
        config[account_type]['api'] = api_key
    elif flag == 2: #store into clientCert
        config[account_type]['clientcert'] = client_cert
    elif flag == 3: #store into privKey
        config[account_type]['privkey'] = priv_key
    else:
        pass    #do nothing if no input
    
    with open('saved_login.ini', 'w') as configfile:
            config.write(configfile)    #write changes to file

def complete_login():   #save the rest of the login info before moving on to main screen
    global radiobutton_var
    
    #store valid certificates on configparser file
    if client_cert not in data_to_list_client: #check if client certificate has been saved before
        flag = 2    #store new valid client_cert into configparser file
        edit_config_file(flag, client_cert)

    if priv_key not in data_to_list_key: #check if priv_key has been saved before
        flag = 3    #store new valid priv_key into configparser file
        edit_config_file(flag, priv_key)

    login.grab_release()    #remove focus
    login.withdraw()    #close login window
    main_screen()   #continue with main screen program

def reset_program():
    device_list.set("Select Device...")  #reset target_device

    device_info['state'] = NORMAL   #reset device info textbox
    device_info.delete(1.0, END)
    device_info.insert(END, select_message, "align")
    device_info['state'] = DISABLED 

    tab1_subscribed_list.delete(0, END) #empty subscribed topics listbox

    #clear messages tab
    for i in tab3_tree.get_children():
        tab3_tree.delete(i)

def popupLogin():
    reset_program()
    logOff.withdraw()   #hide prior window
    root.withdraw() #hide main window

    if client_flag ==1:
        client.disconnect()
        client.loop_stop()
    root.withdraw()  #hide main screen
    login.deiconify()   #show login screen
    login.grab_set()    #disable main screen, focus on login
    
    radiobutton_var.set(None) #reset radiobuttons
    clientCert_file_input.set('') #and reset inputs
    privKey_file_input.set('')
    apikey_input.set('')

def restartReturn():
    logOff.grab_release()
    logOff.withdraw()

def restartPopup():
    global logOff      

    logOff = Toplevel(root)
    logOff.lift() #keep above main window  
    logOff.grab_set()   #only enable this popup to be interactive
    logOff.iconbitmap('./nordicicon.ico')
    logOff.title("nRF Cloud Log Off")
    logOff['background']= myBg

    logOff.option_add("*Font", myFont)
    logOff.option_add("*Background", myBg)
    logOff.option_add("*Foreground", "white")

    #set login dimensions
    logOff_width = 300
    logOff_height = 100

    #already got screen dimensions earlier, now find center points
    logOff_x = int((screen_width/2) - (logOff_width/2))
    logOff_y = int((screen_height/2) - (logOff_height/2))
    
    logOff.geometry(f'{logOff_width}x{logOff_height}+{logOff_x}+{logOff_y}')
    logOff.resizable(False, False)  #fixed size
    logOff.overrideredirect(True)

    logOff_label = Label(logOff, text = "Are you sure you want to log off?")
    logOff_label.pack(fill=None, expand=TRUE)

    yes_button = Button(logOff, text="Yes", command=popupLogin, background=nordic_blue)
    no_button = Button(logOff, text="No", command=restartReturn)
    yes_button.pack(fill=BOTH, expand=TRUE, side=LEFT)
    no_button.pack(fill=BOTH, expand=TRUE, side=LEFT)

    button_config(yes_button)
    button_config(no_button)

def connectMQTT():
    global client 
    global mqtt_topic_prefix
    global mqtt_endpoint
    global client_id 
    global client_flag

    mqtt_endpoint = http_create['mqttEndpoint']
    mqtt_topic_prefix = http_create['mqttTopicPrefix']
    client_id = mqtt_topic_prefix[mqtt_topic_prefix.index('/')+1:]
    client_id = client_id[:client_id.index('/')]
    client_id = 'account-' + client_id 

    client = mqtt.Client(client_id, clean_session=False)
    client.on_connect = on_connect #bind functions to callback
    client.on_subscribe = on_subscribe
    client.on_publish = on_publish
    client.on_message = on_message
    client.on_log = on_log
 
    client.tls_set(ca_certs=str('./caCert.pem'), certfile=client_cert,
                    keyfile=priv_key, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                    tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    client.connect_async(mqtt_endpoint, PORT, KEEP_ALIVE)
    client.loop_start() #create nonblocking thread and return
    
    #set flag so when we switch devices or exit we also client.loop_stop and client.disconnect()
    client_flag = 1     #and also to determine if certificates were valid

def do_createAD():
    generate_certs.create_device(account_type, api_key, client_cert, priv_key)   #create acc dev and certs

    if client_cert not in data_to_list_client: #check if client certificate has been saved before
        flag = 2    #store new valid client_cert into configparser file
        edit_config_file(flag, client_cert)

    if priv_key not in data_to_list_key: #check if priv_key has been saved before
        flag = 3    #store new valid api_key into configparser file
        edit_config_file(flag, priv_key)

    createAD_to_login() #return back to login window
 
def createAD_to_login():
    createAD.grab_release() #remove focus
    createAD.withdraw() #get rid of popup window
    returnLogin()

def generateCerts_to_login():
    generateCerts.grab_release()
    generateCerts.withdraw()
    returnLogin()

def returnLogin():
    login.grab_set()   #focus on login window

def createAD_popup():
    global createAD 

    createAD = Toplevel(root, highlightbackground='white', highlightthickness=2)
    createAD.lift()     #keep window at the top
    createAD.grab_set() #only enable this window to be interactive
    createAD.iconbitmap('./nordicicon.ico')
    createAD.title("nRF Cloud Create Account Device")
    createAD['background'] = myBg 
    
    createAD.option_add("*Font", myFont)
    createAD.option_add("*Background", myBg)
    createAD.option_add("*Foreground", "white")

    createAD_width = 400
    createAD_height = 200

    #already got screen dimensions from main, now find center points
    createAD_x = int((screen_width/2) - (createAD_width/2))
    createAD_y = int((screen_height/2) - (createAD_height/2))

    createAD.geometry(f'{createAD_width}x{createAD_height}+{createAD_x}+{createAD_y}')
    createAD.resizable(False, False)  #fixed size
    createAD.overrideredirect(True)

    AD_label = Label(createAD, text="No account device found.\nWould you like to automatically\n create one?")
    AD_label.pack(fill=None, expand=TRUE)

    yes_button = Button(createAD, text="Yes", command=do_createAD, background=nordic_blue)
    no_button = Button(createAD, text="Return to login", command=createAD_to_login)
    yes_button.pack(ipadx=40, fill=BOTH, expand=TRUE, side=LEFT)
    no_button.pack(fill=BOTH, expand=TRUE, side=LEFT)
    
    button_config(yes_button)
    button_config(no_button)

def generateCerts_popup():
    global generateCerts

    generateCerts = Toplevel(root, highlightbackground='white', highlightthickness=2)
    generateCerts.lift()     #keep window at the top
    generateCerts.grab_set() #only enable this window to be interactive
    generateCerts.iconbitmap('./nordicicon.ico')
    generateCerts.title("nRF Cloud Certificates")
    generateCerts['background'] = myBg 
    
    generateCerts.option_add("*Font", myFont)
    generateCerts.option_add("*Background", myBg)
    generateCerts.option_add("*Foreground", "white")

    generateCerts_width = 400
    generateCerts_height = 200

    #already got screen dimensions from main, now find center points
    generateCerts_x = int((screen_width/2) - (generateCerts_width/2))
    generateCerts_y = int((screen_height/2) - (generateCerts_height/2))

    generateCerts.geometry(f'{generateCerts_width}x{generateCerts_height}+{generateCerts_x}+{generateCerts_y}')
    generateCerts.resizable(False, False)  #fixed size
    generateCerts.overrideredirect(True)

    generateCerts_label = Label(generateCerts, text="Would you like to generate new certificates?")
    generateCerts_label.pack(fill=None, expand=TRUE)

    yes_button = Button(generateCerts, text="Yes", command=do_createAD, background=nordic_blue)
    no_button = Button(generateCerts, text="Return to login", command=generateCerts_to_login)
    yes_button.pack(ipadx=40, fill=BOTH, expand=TRUE, side=LEFT)
    no_button.pack(fill=BOTH, expand=TRUE, side=LEFT)
    
    button_config(yes_button)
    button_config(no_button)

def get_file_paths():
    global client_cert
    global priv_key

    client_cert = clientCert_file_input.get()
    priv_key = privKey_file_input.get()
    
    if client_cert or priv_key == '':   #for some reason this works... 
        invalid_certs_alert()

def find_account_device(api_key):
    global http_get
    global client_cert
    global priv_key
    global acc_device_id

    http_get = http_requests.http_req('GET', DEV_URL, api_key)   #fetch devices info
    device_list = []
    for device in http_get['items']:   #look for account device
        device_list.append(device['id']) #put device IDs in device_list array
    found_device = [i for i in device_list if i.startswith('account-')]
    
    if found_device:    #user account has an account device, save info
        acc_device_id = str(found_device)
        acc_device_id = acc_device_id.strip("['']")

        get_file_paths()    #grab cert paths from inputs
        connectMQTT()   #attempt to connect to MQTT broker
        
        if client_flag == 1:
            complete_login()
        else:
            invalid_certs_alert()
    else:
        login.grab_release()    #allow interaction with popup window
        createAD_popup()    #ask if user wants to create an account device


def config_file(account_type):  #autofill input boxes
    global api_key
    global client_cert
    global priv_key
    global data_to_list_api
    global data_to_list_client
    global data_to_list_key

    #check if file exists
    file_exists = os.path.exists('saved_login.ini')
    if file_exists is not True:  #create file and add sections with blank values to fill in later
        #build structure
        config['Prod'] = {'API': '',
                          'clientCert': '',
                          'privKey': ''}
        config['Beta'] = {'API': '',
                          'clientCert': '',
                          'privKey': ''}
        config['Dev'] = {'API': '',
                          'clientCert': '',
                          'privKey': ''}
        config['Feat'] = {'API': '',
                          'clientCert': '',
                          'privKey': ''}
        with open('saved_login.ini', 'w') as configfile:
            config.write(configfile)

    else:   #parse existing file
        config.read('saved_login.ini')
        api_key = config[account_type]['API']   
        client_cert = config[account_type]['clientCert']
        priv_key = config[account_type]['privKey']
        
        #put values into input boxes 
        clientCert_file_input['values'] += (client_cert,) #add value to combobox list to show in drop down menu
        clientCert_file_input.set(client_cert)    #autofill input for client cert path
        
        privKey_file_input['values'] += (priv_key,)
        privKey_file_input.set(priv_key)
        
        apikey_input['values'] += (api_key,)
        apikey_input.set(api_key)

def account_chosen():
    global account_type

    selected = radiobutton_var.get()    #get the value of the radiobutton selected
    if selected == 1:   #convert to assignment by name
        account_type = 'Prod'
    elif selected == 2:
        account_type = 'Beta'
    elif selected == 3:
        account_type = 'Dev'
    elif selected == 4:
        account_type = 'Feat'
    else:
        pass

    config_file(account_type)   #send to function to get info from saved_login file

def fileExplorer_privKey():
    file_selected = fd.askopenfilename()    #open file explorer
    privKey_file_input.set(file_selected)   #show output selected on combobox

def fileExplorer_clientCert():
    file_selected = fd.askopenfilename()
    clientCert_file_input.set(file_selected)

def invalid_certs_alert():
    global invalid_login_label

    invalid_login_label.config(text='Invalid certificates!')
    invalid_login_label.pack(fill=None, expand=FALSE, side=TOP)
    invalid_login_label.after(2000, lambda: invalid_login_label.pack_forget())

def invalid_login_alert():    #shows error label for two seconds
    global invalid_login_label

    invalid_login_label.config(text='Invalid login credentials!\n Please try again.')
    invalid_login_label.pack(fill=None, expand=FALSE, side=TOP)
    invalid_login_label.after(2000, lambda: invalid_login_label.pack_forget())

def enter_login():
    '''check if API key is valid- if so, store into configparser file and continue'''
    global login 
    global http_create
    global api_key

    #get api_key from input
    api_key = apikey_input.get()    #get API key from input

    #if else statement to test if we can login, otherwise send error and stay at login screen
    http_create = http_requests.http_req('GET', ACC_URL, api_key)  #fetch acc info
    check = [i for i in http_create if isinstance(i, str) and i.startswith('mqttEndpoint')]
    check = str(check)
    check = check.strip("['']") #to be able to use for comparison in if-else statement below
    
    if check == 'mqttEndpoint': #check if api_key used is valid
        if api_key in data_to_list_api: #check if api_key has been saved before
            pass
        else:   #store new valid api_key into configparser file
            flag = 1
            edit_config_file(flag, api_key)
        find_account_device(api_key)   #look for account device
    else:
        invalid_login_alert()

def exit_login():
    root.destroy()  #close program

def login_screen():
    '''Login Frame'''
    global login 
    global invalid_login_label

    #for the entry boxes
    global clientCert_file_input
    global data_to_list_client
    global privKey_file_input
    global data_to_list_key
    global apikey_input
    global data_to_list_api
    global radiobutton_var

    login = Toplevel(root, highlightbackground="grey", highlightthickness=3)  #set up login window 
    login.lift() #keep at the top of application
    login.grab_set()    #only enable login screen to be interative for now
    login.iconbitmap('./nordicicon.ico')
    login.title("nRF Cloud Account Login")
    login['background'] = myBg

    login.option_add("*Font", myFont)
    login.option_add("*Background", myBg)
    login.option_add("*Foreground", "white")

    #set login dimensions
    login_width = 450
    login_height = 550

    #already got screen dimensions from main, now find center points
    login_x = int((screen_width/2) - (login_width/2))
    login_y = int((screen_height/2) - (login_height/2))

    login.geometry(f'{login_width}x{login_height}+{login_x}+{login_y}')
    login.resizable(False, False)  #fixed size
    #login.overrideredirect(True)

    '''Login Screen'''
    login.columnconfigure(tuple(range(4)), weight=2)    #four columns
    login.rowconfigure(tuple(range(10)), weight=2)   #10 rows
    login.rowconfigure(4, weight=1) #make one row smaller to adjust spacing

    intro1_frame = Frame(login)
    intro1_frame.grid(column=0, row=0, columnspan=4, padx=5, pady=5, sticky=W+E+N+S)
    intro1_label = Label(intro1_frame, text="Welcome to the", font=(None, 18))
    intro1_label.pack(fill=None, expand=FALSE, side=BOTTOM)

    intro2_frame = Frame(login)
    intro2_frame.grid(column=0, row=1, columnspan=4, padx=5, sticky=W+E+N+S)
    intro2_label = Label(intro2_frame, text="nRF Cloud Device Monitor Tool", font=(None, 18))
    intro2_label.pack(fill=None, expand=FALSE)

    step1_frame = Frame(login)
    step1_frame.grid(column=0, row=2, columnspan=4, padx=5, sticky=W+E+N+S)
    step1_label = Label(step1_frame, text="Please select account type: ")
    step1_label.config(font=(None, 12, BOLD))
    step1_label.pack(fill=None, expand=TRUE)

    #order: prod, beta, dev, feat
    radiobutton_var = IntVar()
    select_frame = Frame(login)
    select_frame.grid(pady=(0,15), column=0, row=3, columnspan=4)

    prod_select = Radiobutton(select_frame, text="Prod", variable=radiobutton_var, value=1, command=account_chosen)
    prod_select.config(activebackground=myBg, activeforeground='grey', cursor='hand2')
    prod_select.pack(fill=None, expand=FALSE, side=LEFT)
    prod_select.deselect()

    beta_select = Radiobutton(select_frame, text="Beta", variable=radiobutton_var, value=2, command=account_chosen)
    beta_select.config(activebackground=myBg, activeforeground='grey', cursor='hand2')
    beta_select.pack(padx=15, fill=None, expand=FALSE, side=LEFT)
    beta_select.deselect()

    dev_select = Radiobutton(select_frame, text="Dev", variable=radiobutton_var, value=3, command=account_chosen)
    dev_select.config(activebackground=myBg, activeforeground='grey', cursor='hand2')
    dev_select.pack(fill=None, expand=FALSE, side=LEFT)
    dev_select.deselect()

    feat_select = Radiobutton(select_frame, text="Feat", variable=radiobutton_var, value=4, command=account_chosen)
    feat_select.config(activebackground=myBg, activeforeground='grey', cursor='hand2')
    feat_select.pack(padx=(15,0), fill=None, expand=False, side=LEFT)
    feat_select.deselect()  

    '''
    For the Radiobuttons, when one is selected, make it go to a function that
    .gets the one that is selected, then open a file that is formatted in a dict
    and use the dict with the same key "type" has the one that is selected to output its
    corresponding cacert, private key, and API key.
    But this will only work if the account has been logged in before.
    And if the account has logged in successfully before and the user manually 
    chooses files, try to use those files to connect.
    If login success, replace those files with whatever was in caCert : "", privKey : "", etc.

    '''

    step2_frame = Frame(login)
    step2_frame.grid(column=0, row=4, columnspan=4, padx=5, pady=(0,5), sticky=W+E+N+S)
    step2_label = Label(step2_frame, text="[ ? ] Insert associated files:")
    step2_label.config(font=(None, 11, BOLD))
    step2_label.pack(fill=None, expand=FALSE, side=BOTTOM)
    ToolTip(step2_label, msg='Select client cert and private key\nfile paths from history if any,\nor browse for new ones.',
            background='#AEDAEB', foreground='black', font=(None, 10), follow=True)

    clientCert_frame = Frame(login)
    clientCert_frame.grid(column=0, row=5, columnspan=2, padx=(5,2), sticky=W+E+N+S)
    clientCert_label = Label(clientCert_frame, text='Client Cert: ')
    clientCert_label.pack(fill=None, expand=FALSE, side=RIGHT)

    clientCert_file_frame = Frame(login)
    clientCert_file_frame.grid(column=2, row=5, columnspan=2, padx=5, sticky=W+E+N+S)

    clientString = StringVar()
    clientCert_file_input = Combobox(clientCert_file_frame, values=data_to_list_client, textvariable=clientString)
    clientCert_file_input.config(font=(None, 8), width=30)
    clientCert_file_input.pack(fill=None, expand=FALSE, side=LEFT)

    clientCert_browse_button = Button(clientCert_file_frame, text="[Browse]", command=fileExplorer_clientCert)
    clientCert_browse_button.config(font=(None, 10))
    clientCert_browse_button.pack(fill=None, expand=FALSE, side=LEFT)

    privKey_frame = Frame(login)
    privKey_frame.grid(column=0, row=6, columnspan=2, padx=(5,2), sticky=W+E+N+S)
    privKey_label = Label(privKey_frame, text='Private Key: ')
    privKey_label.pack(fill=None, expand=FALSE, side=RIGHT)

    privKey_file_frame = Frame(login)
    privKey_file_frame.grid(column=2, row=6, columnspan=2, padx=5, pady=5, sticky=W+E+N+S)

    keyString = StringVar()
    privKey_file_input = Combobox(privKey_file_frame, values=data_to_list_key, textvariable=keyString)
    privKey_file_input.config(font=(None, 8), width=30)
    privKey_file_input.pack(fill=None, expand=FALSE, side=LEFT)

    privKey_browse_button = Button(privKey_file_frame, text="[Browse]", command=fileExplorer_privKey)
    privKey_browse_button.config(font=(None, 10))
    privKey_browse_button.pack(fill=None, expand=FALSE, side=LEFT)

    apikey_label_frame = Frame(login)
    apikey_label_frame.grid(column=0, row=7, columnspan=4, padx=5, pady=(5,0), sticky=W+E+N+S)
    apikey_label = Label(apikey_label_frame, text='Enter your API Key:')
    apikey_label.config(font=(None, 11, BOLD))
    apikey_label.pack(fill=None, expand=TRUE)

    apiString = StringVar()
    apikey_input_frame = Frame(login)
    apikey_input_frame.grid(column=0, row=8, columnspan=4, padx=5, sticky=W+E+N+S)
    apikey_input = Combobox(apikey_input_frame, values=data_to_list_api, textvariable=apiString, width=30)
    apikey_input.pack(fill=None, expand=FALSE)

    bottom_buttons_frame = Frame(login)
    bottom_buttons_frame.grid(column=0, row=9, columnspan=3, padx=(5,0), pady=(0,5))
    exit_login_button = Button(bottom_buttons_frame, text='Exit', command=exit_login)
    exit_login_button.pack(ipadx=5, fill=None, expand=FALSE, side=LEFT)

    new_certs_button = Button(bottom_buttons_frame, text='New Certs', command=generateCerts_popup)
    new_certs_button.config(font=(None, 11))
    new_certs_button.pack(padx=20, ipadx=1, ipady=1, fill=None, expand=FALSE, side=LEFT)

    enter_login_button = Button(bottom_buttons_frame, text='Enter', command=enter_login)
    enter_login_button.pack(ipadx=12, fill=None, expand=FALSE, side=LEFT)

    blank_corner_frame = Frame(login)
    blank_corner_frame.grid(column=3, row=9, padx=(0,5), pady=(0,5), sticky=W+E+N+S)
    #blank corner will pop up notification if invalid login
    invalid_login_label = Label(blank_corner_frame, text='')
    invalid_login_label.config(font=(None, 9), foreground='red')    #red text color

    #bind enter key with event function
    login.bind('<Return>', enter_login_press)

    button_config(clientCert_browse_button)
    button_config(privKey_browse_button)
    button_config(enter_login_button)
    button_config(exit_login_button)
    button_config(new_certs_button)

def doNothing():
    pass


'''Root Frame'''
root = Tk() #setup root window
root.iconbitmap('./nordicicon.ico')
root.title("nRF Cloud Device Monitor Tool")
root['background'] = '#748587'
root.withdraw()  #hide main screen for now

#set window dimensions
window_width = 1150
window_height = 650

#get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

#find center points
main_x = int((screen_width/2) - (window_width/2)) #center X
main_y = int((screen_height/2) - (window_height/2))   #center Y

root.geometry(f'{window_width}x{window_height}+{main_x}+{main_y}')
root.minsize(600, 300)

login_screen()

root.mainloop()