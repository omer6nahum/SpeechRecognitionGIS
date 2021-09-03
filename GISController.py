from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium import webdriver
from time import sleep
from googletrans import Translator
import csv
import pandas as pd
from collections import defaultdict
import login_details
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_layers_csv_creation_v2(layers):
    translator = Translator()
    with open('heb_en_layers_v2.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='|')
        writer.writerow(['Hebrew', 'English'])
        for layer in layers:
            translated_layer = translator.translate(layer, lang_src='he', lang_tgt='en').text.lower()
            writer.writerow([layer, translated_layer])


def create_layers_csv_creation(layers, boxes):
    translator = Translator()

    en_layers_checkbox_dict = {}
    super_layers_dict = {}
    with open('heb_en_layers_.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='|')
        writer.writerow(['Hebrew', 'English'])
        for layer, checkbox in zip(layers, boxes):
            if layer.text != '':
                translated_layer = translator.translate(layer.text, lang_src='he', lang_tgt='en').text.lower()
                if '\n' in translated_layer:
                    super_layer = translated_layer.split('\n')[0]
                    super_layer_heb = layer.text.split('\n')[0]
                    writer.writerow([super_layer_heb, super_layer])
                    super_layers_dict[super_layer] = translated_layer.split('\n')[1:]
                    en_layers_checkbox_dict[super_layer] = ('super_layer', checkbox)
                else:
                    en_layers_checkbox_dict[translated_layer] = checkbox
                    writer.writerow([layer.text, translated_layer])

    return en_layers_checkbox_dict, super_layers_dict


def create_layer_checkbox_dict(layers, boxes):
    heb_en_layers = pd.read_csv('heb_en_layers.csv')
    translator = {row['Hebrew']: row['English'] for _, row in heb_en_layers.iterrows()}
    closed_list = list(heb_en_layers['English'])
    en_layers_checkbox_dict = {}
    super_layers_dict = {}
    for layer, checkbox in zip(layers, boxes):
        try:
            if layer.text != '':
                if '\n' in layer.text:
                    super_layer_heb = layer.text.split('\n')[0]
                    super_layer = translator[super_layer_heb]
                    super_layers_dict[super_layer] = [translator[w] for w in layer.text.split('\n')[1:]]
                    en_layers_checkbox_dict[super_layer] = ('super_layer', checkbox)
                else:
                    translated_layer = translator[layer.text]
                    en_layers_checkbox_dict[translated_layer] = checkbox
        except KeyError:
            print('Call Bat-el and ask to add to csv')
            continue

    return en_layers_checkbox_dict, super_layers_dict, closed_list


class giscontroller:
    def __init__(self, url=None):
        self.wait = None
        self.suplayer_to_sublayer_dict, self.layers_arrow_dict, self.layers_checkbox_dict = self.open_webscene(url)
        self.sublayer_to_suplayer_dict = defaultdict(str)
        for sup_layer, sub_layers in self.suplayer_to_sublayer_dict.items():
            for sub_layer in sub_layers:
                self.sublayer_to_suplayer_dict[sub_layer] = sup_layer

    @staticmethod
    def login(driver):
        sleep(2)
        submit = driver.find_elements_by_xpath("//*[@id=\"loginComponents\"]/section[1]/div/div/div/div")
        submit[0].click()
        sleep(3)

        input_mail = driver.find_elements_by_xpath("//*[@id=\"i0116\"]")
        input_mail[0].send_keys(login_details.username)
        submit = driver.find_elements_by_xpath("//*[@id=\"idSIButton9\"]")
        submit[0].click()
        sleep(4)

        input_mail = driver.find_elements_by_xpath("//*[@id=\"i0118\"]")
        input_mail[0].send_keys(login_details.password)
        submit = driver.find_elements_by_xpath("//*[@id=\"idSIButton9\"]")
        submit[0].click()
        sleep(3)

        submit = driver.find_elements_by_xpath("//*[@id=\"idBtn_Back\"]")
        submit[0].click()
        sleep(10)

    @staticmethod
    def scrape_layers(layers):
        sup_layers_dict = defaultdict(list)
        layers_checkbox_dict = {}
        layers_arrow_dict = {}
        heb_en_layers = pd.read_csv('heb_en_layers_v2.csv')
        translator = {row['Hebrew']: row['English'] for _, row in heb_en_layers.iterrows()}
        for layer in layers:
            if layer.text != '':
                try:
                    dropdown_arrows = layer.find_elements_by_class_name(
                        "esri-layer-list__child-toggle")  # Scrape all dropdown arrows for sub layers including super layer
                    # sub_arrow_idx = 0
                    layer_name = translator[layer.text.split('\n')[0]]
                    layers_checkbox_dict[layer_name] = layer  # Save current super layer checkbox
                    if len(dropdown_arrows) > 0:
                        layers_arrow_dict[layer_name] = dropdown_arrows[0]
                        # sub_arrow_idx += 1
                        layers_arrow_dict[layer_name].click()
                        sleep(0.5)
                        sub_layers = layer.find_elements_by_tag_name("li")  # Scrape all sub layers
                        for sub_layer in sub_layers:
                            # sleep(0.5)
                            if len(sub_layer.find_elements_by_class_name("esri-icon-notice-triangle")) > 0:
                                print("Warning, layer not loaded, under {}".format(layer_name))
                                continue
                            if sub_layer.text != '':
                                try:
                                    sub_layer_translated = translator[sub_layer.text]
                                    sup_layers_dict[layer_name].append(sub_layer_translated)
                                    layers_checkbox_dict[sub_layer_translated] = sub_layer
                                except KeyError:
                                    print('Need to add layer {} to csv'.format(sub_layer.text))
                                    continue
                        # layers_arrow_dict[layer_name].click()
                        giscontroller.wait_click(layers_arrow_dict[layer_name])
                    else:
                        continue
                except KeyError:
                    print('Need to add layer {} to csv'.format(layer.text))
                    continue

        return sup_layers_dict, layers_arrow_dict, layers_checkbox_dict

    @staticmethod
    def wait_click(button, seconds=5):
        for i in range(2 * int(seconds)):
            try:
                button.click()
                break
            except ElementNotInteractableException:
                sleep(0.5)

    def open_webscene(self, url=None):
        if url is None:
            url = "https://technion-gis.maps.arcgis.com/apps/webappviewer3d/index.html?id=8b620f3241ed4b548a865a2ff102d0b1"

        driver = webdriver.Chrome(login_details.driver_path)
        driver.get(url=url)
        driver.maximize_window()
        # self.wait = WebDriverWait(driver, 10)

        self.login(driver)
        sleep(6)
        open_layers_button = driver.find_elements_by_xpath("//*[@id=\"uniqName_3_5\"]/div[1]")
        open_layers_button[0].click()
        sleep(6)

        layers_container = driver.find_elements_by_xpath("//*[@id=\"widgets_LayerList_Widget_17_panel\"]")
        layers_list = layers_container[0].find_elements_by_tag_name("li")
        return self.scrape_layers(layers_list)

    def show(self, layer):
        if len(self.sublayer_to_suplayer_dict[layer]) > 0:
            sup_layer = self.sublayer_to_suplayer_dict[layer]
            if self.layers_arrow_dict[sup_layer].get_attribute('title') == 'Expand':
                self.layers_arrow_dict[sup_layer].click()
            try:
                t = self.layers_checkbox_dict[layer].find_element_by_class_name("esri-icon-non-visible")
                self.wait_click(t)
            except NoSuchElementException:
                print('already presented')
                pass
        elif layer in self.suplayer_to_sublayer_dict.keys():
            if self.layers_arrow_dict[layer].get_attribute('title') == 'Expand':
                self.layers_arrow_dict[layer].click()
            non_visible_checkboxes = self.layers_checkbox_dict[layer].find_elements_by_class_name("esri-icon-non-visible")
            for checkbox in non_visible_checkboxes:
                self.wait_click(checkbox)
        else:
            try:
                t = self.layers_checkbox_dict[layer].find_element_by_class_name("esri-icon-non-visible")
                # self.wait.until(EC.element_to_be_clickable(t))
                # t.click()
                self.wait_click(t)
            except NoSuchElementException:
                print('already presented')
                pass

    def hide(self, layer):
        if len(self.sublayer_to_suplayer_dict[layer]) > 0:
            sup_layer = self.sublayer_to_suplayer_dict[layer]
            if self.layers_arrow_dict[sup_layer].get_attribute('title') == 'Expand':
                self.layers_arrow_dict[sup_layer].click()
            try:
                t = self.layers_checkbox_dict[layer].find_element_by_class_name("esri-icon-visible")
                self.wait_click(t)
            except NoSuchElementException:
                print('already hidden')
                pass
            if len(self.layers_checkbox_dict[sup_layer].find_elements_by_class_name("esri-icon-visible")) == 0 \
                and self.layers_arrow_dict[sup_layer].get_attribute('title') == 'Collapse':
                self.layers_arrow_dict[sup_layer].click()

        elif layer in self.suplayer_to_sublayer_dict.keys():
            if self.layers_arrow_dict[layer].get_attribute('title') == 'Expand':
                self.layers_arrow_dict[layer].click()
            visible_checkboxes = self.layers_checkbox_dict[layer].find_elements_by_class_name("esri-icon-visible")
            for checkbox in visible_checkboxes:
                self.wait_click(checkbox)
            if self.layers_arrow_dict[layer].get_attribute('title') == 'Collapse':
                self.layers_arrow_dict[layer].click()
        else:
            try:
                t = self.layers_checkbox_dict[layer].find_element_by_class_name("esri-icon-visible")
                self.wait_click(t)

            except NoSuchElementException:
                print('already presented')
                pass

    def clear(self):
        for layer in self.layers_checkbox_dict:
            self.hide(layer)


if __name__ == '__main__':
    gis = giscontroller()
