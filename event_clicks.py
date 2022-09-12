'''Remove/insert shadow texts for tab1 and tab2'''

from tkinter import *

#tab2 entry boxes
def tab2_remove_shadow_text_left(tab2_topic_input):
    if tab2_topic_input.get() == 'Enter a topic...':
        tab2_topic_input.delete(0, END) #delete text in entry
        tab2_topic_input.insert(0, '')  #blank user input
        tab2_topic_input.config(fg='black') #change text to black

def tab2_remove_shadow_text_right(tab2_msg_input):
    if tab2_msg_input.get() == 'Enter a message...':
        tab2_msg_input.delete(0,END)    #delete text in entry
        tab2_msg_input.insert(0, '')    #blank user input
        tab2_msg_input.config(fg='black')   #change text to black

def tab2_insert_shadow_text_left(tab2_topic_input):
    if tab2_topic_input.get() == '':
        tab2_topic_input.insert(0, 'Enter a topic...')
        tab2_topic_input.config(fg='grey')
    
def tab2_insert_shadow_text_right(tab2_msg_input):    
    if tab2_msg_input.get() == '':
        tab2_msg_input.insert(0, 'Enter a message...')
        tab2_msg_input.config(fg='grey')

#tab1 entry box
def tab1_remove_shadow_text(tab1_sub_to_topic):
    if tab1_sub_to_topic.get() == 'Enter a topic...':
        tab1_sub_to_topic.delete(0, END) 
        tab1_sub_to_topic.insert(0, '') 
        tab1_sub_to_topic.config(fg='black')

def tab1_insert_shadow_text(tab1_sub_to_topic):
    if tab1_sub_to_topic.get() == '':
        tab1_sub_to_topic.insert(0, 'Enter a topic...')
        tab1_sub_to_topic.config(fg='grey')
