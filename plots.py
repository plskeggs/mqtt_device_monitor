from tkinter import W, E, N, S

#Matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

nordic_blue = '#00A9CE'

data_rsrp = []
data_button = []

def get_data_rsrp(data):
    data_rsrp.append(float(data))

def get_data_button(data):
    data_button.append(float(data))

def animate_rsrp(i):
    for data in data_rsrp:
        if data == 0:
            yar1.append(0)
        else:
            yar1.append(data)
        xar1.append(i)
        line1.set_data(range(1,1+len(yar1)), yar1)

    ax1.set_xlim(0,i+1)
    data_rsrp.clear()

def animate_button(i):
    for data in data_button:
        if data == 0:
            yar2.append(0)
        else:
            yar2.append(data)
        xar2.append(i)
        line2.set_data(range(1,1+len(yar2)), yar2)

    ax2.set_xlim(0,i+1) #move axis with time
    data_button.clear()

def graph_rsrp(tab3_layout_right):
    global xar1
    global yar1
    global line1
    global ax1
    global fig1
    global anim_rsrp

    xar1 = []
    yar1 = []

    style.use('ggplot')
    fig1 = plt.figure(figsize=(9,5), dpi=50)
    ax1 = fig1.add_subplot(111)
    ax1.set_title("Reference Signal Received Power")
    ax1.set_ylim(-100,20)
    ax1.set_ylabel("RSRP (dBm)")
    line1, = ax1.plot(xar1, yar1, nordic_blue, marker='o')

    plotcanvas1 = FigureCanvasTkAgg(fig1, tab3_layout_right)
    plotcanvas1.get_tk_widget().grid(column=0, row=0, padx=5, pady=(5), sticky=W+E+N+S)

    anim_rsrp = animation.FuncAnimation(fig1, animate_rsrp, interval=5000)

def graph_button(tab3_layout_right):
    global xar2
    global yar2
    global line2
    global ax2
    global fig2
    global anim_button

    xar2 = []
    yar2 = []

    style.use('ggplot')
    fig2 = plt.figure(figsize=(9,5), dpi=50)
    ax2 = fig2.add_subplot(111)
    ax2.set_title("Button")
    ax2.set_ylim(0, 2.5)
    ax2.set_ylabel("Data")
    line2, = ax2.plot(xar2, yar2, nordic_blue, marker='o')

    plotcanvas2 = FigureCanvasTkAgg(fig2, tab3_layout_right)
    plotcanvas2.get_tk_widget().grid(column=0, row=1, padx=5, pady=(0,5), sticky=W+E+N+S)

    anim_button = animation.FuncAnimation(fig2, animate_button, interval=5000)