import speech_recognition as sr
from speech_recognition import WaitTimeoutError
import numpy as np
import jellyfish
import nltk
from GISController import giscontroller
import warnings
import pickle

warnings.filterwarnings('ignore')
NUM_FEATURES = 7


def takeCommand(window_object=None):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        try:
            if window_object is not None:
                window_object['Listening'].update(value='Listening')
                window_object.Refresh()
            audio = r.listen(source, timeout=3)
        except WaitTimeoutError:
            print("Pardon me, I didn't hear anything")
            return None

        try:
            statement = r.recognize_google(audio, language='en-in')
            print(f"user said:{statement}\n")

        except Exception as e:
            print("Pardon me, please say that again")
            return None

        return statement


def create_layers_features_matrix(input_texts: list, closed_list: list, max_vec=None):
    """
    :param input_texts: shape == number of samples
    :param closed_list: shape == number of layers
    :return: matrix of shape == (num sample, num layers, num features)
    """
    final_scores = []
    for input_text in input_texts:
        functions = [f_001, f_002, f_004, f_006]
        scores = []
        for layout_name in closed_list:
            features = []
            for f in functions:
                features += f(input_text, layout_name)
            scores.append(features)
        scores = np.array(scores)
        final_scores.append(scores)
    final_scores = np.array(final_scores)
    if max_vec is None:
        max_vec = []
        for j in range(final_scores.shape[2]):
            max_vec.append(max(final_scores[:, :, j].flatten()))
        max_vec = np.array(max_vec)
        with open('max_vec.pkl', 'wb') as f:
            pickle.dump(max_vec, f)
    for j in range(final_scores.shape[2]):
        final_scores[:, :, j] = final_scores[:, :, j] / max_vec[j]
    return final_scores


def match_input_to_layout(input_texts: list, closed_list: list, w, threshold=0.5, max_vec=None):
    layers_features_matrices = create_layers_features_matrix(input_texts, closed_list, max_vec)
    samples_layers_prob = np.array([np.matmul(f_x, w) for f_x in layers_features_matrices])
    final_scores = []
    for sample_probs in samples_layers_prob:
        argmax = int(np.argmax(sample_probs))
        if sample_probs[argmax] > threshold:
            final_scores.append(closed_list[argmax])
            print(f'chosen layout: {closed_list[argmax]}')
        else:
            final_scores.append(None)
            print(f'chosen layout: None')
    return final_scores


def f_001(s1, s2):
    """
    :return: check for exact set matching w1 in s2
    """
    counter = 0
    s1 = s1.split(' ')
    s2 = s2.split(' ')
    for input_word in s1:
        counter += 1 if input_word in s2 else 0
    return [counter / len(s1)]


def f_002(s1, s2):
    """
    :return: Comparing s1 and s2 in levenshtein_distance - number of changes required to get from s1 to s2
    """
    num_letters = sum([len(s) for s in s2.split(' ')])
    res = jellyfish.levenshtein_distance(s1, s2)
    return [num_letters / (res + 1e-3)]


def f_004(s1, s2):
    """
    :return: Comparing s1 and s2 using soundex algorithm
    """
    # return features
    counter_first_letter = 0
    counter_num1 = 0
    counter_num2 = 0
    counter_num3 = 0

    # find lengths,min,max
    s1_words = s1.split(' ')
    s2_words = s2.split(' ')
    s1_len = len(s1_words)
    s2_len = len(s2_words)
    min_len = min(s1_len, s2_len)
    max_len = max(s1_len, s2_len)
    argmin_words, argmax_words = (s1_words, s2_words) if min_len == s1_len else (s2_words, s1_words)

    # run for every min_len-substring in argmax_words and compare with zip
    for i in range(max_len - min_len + 1):
        cur_argmax_words = argmax_words[i: i + min_len]
        for w1, w2 in zip(argmin_words, cur_argmax_words):
            res1 = jellyfish.soundex(w1)
            res2 = jellyfish.soundex(w2)
            if res1[0] == res2[0]:
                counter_first_letter += 1
            if res2[1] == res1[1]:
                counter_num1 += 1
            if res2[2] == res1[2]:
                counter_num2 += 1
            if res2[3] == res1[3]:
                counter_num3 += 1

    n = (max_len - min_len + 1) * min_len
    return [counter_first_letter / n, counter_num1 / n, counter_num2 / n, counter_num3 / n]


def f_006(s1, s2):
    hypothesis = s2  # layer name
    reference = s1  # the input text
    min_len = min(len(s1), len(s2))
    BLEUscore = nltk.translate.bleu_score.sentence_bleu([reference], hypothesis)

    return [BLEUscore]


if __name__ == '__main__':
    gis_controller = giscontroller()
    closed_list = gis_controller.closed_list
    print(f'Known list: {closed_list}')
    with open('learned_weights.pkl', 'rb') as f:
        w = pickle.load(f)
    with open('max_vec.pkl', 'rb') as f:
        max_vec = pickle.load(f)
    while True:
        statement = takeCommand()
        if statement is None:
            print('say again')
            continue
        statement = statement.lower()
        if statement == 'done':
            break
        command = statement.split(' ')[0]  # show, hide, clear
        if command not in ['show', 'close', 'clear']:
            continue
        if command == 'clear':
            gis_controller.clear()
        else:
            heared = " ".join(statement.split(' ')[1:])
            output = match_input_to_layout([heared], closed_list, w)
            layer = output[0]
            # print(layer)
            if command == 'show':
                gis_controller.show(layer)
            elif command == 'close':
                gis_controller.hide(layer)
        # print(match_input_to_layout([statement], closed_list, w)[0])
