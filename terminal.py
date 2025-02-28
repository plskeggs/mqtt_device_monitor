from tkinter import NORMAL, DISABLED, END


class Terminal():

    def __init__(self, terminal_list, terminal_input,
                mqtt_endpoint, mqtt_topic_prefix, client_id):
        self.__terminal_list = terminal_list
        self.__terminal_input = terminal_input
        self.__mqtt_endpoint = mqtt_endpoint
        self.__mqtt_topic_prefix = mqtt_topic_prefix
        self.__client_id = client_id

    def terminal_reset(self):
        self.__terminal_list['state'] = NORMAL
        self.terminal_print("Welcome! Select a device to get started.")  #first line in terminal
        self.terminal_print("Type /help for more information.")
        self.__terminal_list['state'] = DISABLED

    def terminal_clear(self):   #clear terminal output and entry box
        self.__terminal_list['state'] = NORMAL
        self.__terminal_input.delete(0, END)
        self.__terminal_list.delete(1.0, END)
        self.__terminal_list['state'] = DISABLED

    def terminal_enter(self):
        user_input = self.__terminal_input.get()
        if user_input == '':    #nothing typed in, do nothing
            return
        else:
            self.__terminal_list['state'] = NORMAL
            self.terminal_print(user_input)  #output user input on terminal
            self.__terminal_list['state'] = DISABLED

        self.__terminal_list['state'] = NORMAL

        if user_input == '/help':
            self.help_output()
        elif user_input == '-v':
            self.__terminal_list.insert(END, 'Python Version 3.10.6\n')
            self.__terminal_list.insert(END, 'Developed SUMMER 2022\n\n')
        elif user_input == '-acc':
            self.__terminal_list.insert(END, 'MQTT Endpoint: ' + self.__mqtt_endpoint + '\n')
            self.__terminal_list.insert(END, 'MQTT Topic Prefix: ' + self.__mqtt_topic_prefix + '\n')
            self.__terminal_list.insert(END, 'MQTT Client ID: ' + self.__client_id + '\n\n')
        else:
            pass    #do nothing

        self.__terminal_input.delete(0, END) #clear entry box
        self.__terminal_list['state'] = DISABLED

    def terminal_print(self, text):   #terminal output
        self.__terminal_list['state'] = NORMAL
        text_format = ' >> ' + text
        self.__terminal_list.insert(END, text_format + '\n') #insert at the bottom
        self.__terminal_list.yview(END)    #move scrollbar along with text
        self.__terminal_list['state'] = DISABLED

    def help_output(self):
        help_list = ['\n----------------------------------------',
                    '  -v              program version',
                    '  -acc        account information',
                    '----------------------------------------'
                    ]
        for i in help_list:
            self.__terminal_list.insert(END, i + '\n')
            self.__terminal_list.yview(END)