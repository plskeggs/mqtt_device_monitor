from tkinter.ttk import Style

myGrey = '#D9D9D9'  #even lighter grey
light_grey = '#ECEFF1'

def tab_theme():
    '''Customize theme for tabs'''
    style = Style()
    style.theme_create("tab_decor", parent="alt", settings= {
        "TNotebook": {"configure": {"background": light_grey,
                                    "tabmargins": [2,0,1,0]}},
        "TNotebook.Tab": {
            "configure":  {"padding": [75,10], "background": light_grey,
                           "font": 'Arial 14'},
            "map":        {"background": [("selected", myGrey)],
                           "expand": [("selected", [1,1,1,0])] }
                         }
        }
    )
    style.theme_use("tab_decor")
    style.layout("Tab",     #get rid of dotted line on selected tab
    [('Notebook.tab', {'sticky': 'nswe', 'children':
        [('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children':
            #[('Notebook.focus', {'side': 'top', 'sticky': 'nswe', 'children':
                [('Notebook.label', {'side': 'top', 'sticky': ''})],
            #})],
        })],
    })]
    )