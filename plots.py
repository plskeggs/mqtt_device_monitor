from datetime import datetime
from tkinter import BOTH, TRUE, W, E, N, S

#Matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

def animate1(i):
    yar1.append(99-i)
    xar1.append(i)    #eventually plot current time instead
    line1.set_data(xar1,yar1)
    ax1.set_xlim(0,i+1)

def graph1(tab3_layout_right):
    global xar1 
    global yar1
    global line1
    global ax1
    global fig1
    global anim1 

    xar1 = []
    yar1 = []

    style.use('ggplot')
    fig1 = plt.figure(figsize=(9,5), dpi=50)
    ax1 = fig1.add_subplot(111)
    ax1.set_title("Reference Signal Received Power")
    ax1.set_ylim(0,100)
    ax1.set_ylabel("RSRP (dBm)")
    line1, = ax1.plot(xar1, yar1, 'b', marker='o')

    plotcanvas1 = FigureCanvasTkAgg(fig1, tab3_layout_right)
    plotcanvas1.get_tk_widget().grid(column=0, row=0, padx=5, pady=(5), sticky=W+E+N+S)

    anim1 = animation.FuncAnimation(fig1, animate1, interval=3000, blit=False)

def animate2(i):
    yar2.append(99-i)
    xar2.append(i)          #eventually plot current time instead
    line2.set_data(xar2,yar2)
    ax2.set_xlim(0,i+1)

def graph2(tab3_layout_right):
    global xar2 
    global yar2
    global line2
    global ax2
    global fig2
    global anim2 

    xar2 = []   
    yar2 = []

    style.use('ggplot')
    fig2 = plt.figure(figsize=(9,5), dpi=50)
    ax2 = fig2.add_subplot(111)
    ax2.set_title("Custom App: VOLTAGE")
    ax2.set_ylim(0,100)
    ax2.set_ylabel("Voltage()") #adjust units, maybe to mV since avg data=5000
    line2, = ax2.plot(xar2, yar2, 'b', marker='o')

    plotcanvas2 = FigureCanvasTkAgg(fig2, tab3_layout_right)
    plotcanvas2.get_tk_widget().grid(column=0, row=1, padx=5, pady=(0,5), sticky=W+E+N+S)

    anim2 = animation.FuncAnimation(fig2, animate2, interval=3000, blit=False)
