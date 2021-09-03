from PySimpleGUI import Text, Button, Window, Column, WIN_CLOSED
from main import NUM_FEATURES
from numpy import array
from GISController import giscontroller
from main import takeCommand
from main import match_input_to_layout
# from win32com.client import Dispatch
import pickle

first_layout = [[Text("Press Launch to open the digital twin", font=("Arial", 17))], [Button("Launch")]]
layout = [[Column(first_layout, element_justification='center')]]
first_window = Window("GIS Voice Assistant", layout, margins=(100, 100))
to_second_window = False
gis_controller = None
w = None
closed_list = None
# speaker = Dispatch("SAPI.SpVoice")

while True:
    event, values = first_window.read()
    if event == WIN_CLOSED:
        break
    if event == "Launch":
        gis_controller = giscontroller()
        closed_list = list(gis_controller.layers_checkbox_dict.keys())
        with open('learned_weights.pkl', 'rb') as f:
            w = pickle.load(f)
        with open('max_vec.pkl', 'rb') as f:
            max_vec = pickle.load(f)
        to_second_window = True
        break
first_window.close()

if to_second_window:
    main_layout = [[Text("Press Record to give command", font=("Arial", 15))],
                     [Text("Press Pause to stop recordings", font=("Arial", 15))],
                     [Text("Commands are: show, close and clear", font=("Arial", 15))],
                    [Text('', font=('Arial', 15), key='Listening')],
                     [Button(button_text='', key='Record', image_filename='record.png', image_size=(120, 120))]]
    manual_layout = [[Text('Manual:', font=("Arial", 15, "bold"))],
                     [Text('*Say: \'show <layer_name>\' to mark the layer.\n'
                              ' If you ask for a nested layer, all of its sub layers will be marked.')],
                     [Text('*Say: \'close <layer_name>\' to unmark the layer.\n'
                              ' If you close a nested layer, all of its sub layers will be unmarked.')],
                     [Text('*Say \'clear\' to clear all marked layers.'),
                      [Text('*Say \'done\' to pause')]],
                     [Button(button_text='', key='Exit', image_filename='exit.png', image_size=(120, 120))]]
    second_window = Window("GIS Voice Assistant", main_layout + manual_layout, size=(500, 600))
    listening = second_window['Listening']
    while True:
        event, values = second_window.read()
        if event == WIN_CLOSED:
            break
        if event == "Record":
            statement = takeCommand(second_window)
            if statement is None:
                # speaker.Speak(f"Please Record again")
                listening.update(value='Please Record again')
                second_window.Refresh()
                continue
            statement = statement.lower()
            if statement == 'done':
                break
            command = statement.split(' ')[0]  # show, close, clear
            if command not in ['show', 'close', 'clear']:
                # speaker.Speak(f"Please Record again")
                listening.update(value='Please Record again')
                second_window.Refresh()
                continue
            if command == 'clear':
                gis_controller.clear()
                listening.update(value='')
                second_window.Refresh()
            else:
                heared = " ".join(statement.split(' ')[1:])
                output = match_input_to_layout([heared], closed_list, w, threshold=0.4, max_vec=max_vec)
                layer = output[0]
                if layer is None:
                    # speaker.Speak(f"Please Record again")
                    listening.update(value='Please Record again')
                    second_window.Refresh()
                elif command == 'show':
                    # speaker.Speak(f"Showing {layer}")
                    gis_controller.show(layer)
                    listening.update(value='')
                    second_window.Refresh()
                elif command == 'close':
                    # speaker.Speak(f"Closing {layer}")
                    gis_controller.hide(layer)
                    listening.update(value='')
                    second_window.Refresh()
                else:
                    # speaker.Speak(f"Please Record again")
                    listening.update(value='Please Record again')
                    second_window.Refresh()
        if event == "Exit":
            print('closing')
            break
    second_window.close()
