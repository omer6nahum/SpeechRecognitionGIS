import speech_recognition as sr
from speech_recognition import WaitTimeoutError
import csv
import pickle
import random
import pandas as pd


def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=3)
        except WaitTimeoutError:
            print("Pardon me, I didn't hear anything")
            return "None"

        try:
            statement = r.recognize_google(audio, language='en-in')
            print(f"user said:{statement}\n")

        except Exception as e:
            print("Pardon me, please say that again")
            return "None"

        return statement


if __name__ == "__main__":
    layers = pd.read_csv('heb_en_layers.csv')
    layers_en = list(layers['English'])
    with open('train.csv', 'a+', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # writer.writerow(['heared', 'expected'])
        for layer in random.sample(layers_en, 10):
            print(layer)
            heared = takeCommand().lower()
            writer.writerow([heared, layer.lower()])

