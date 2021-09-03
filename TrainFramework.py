from main import NUM_FEATURES, create_layers_features_matrix, match_input_to_layout
from scipy.optimize import minimize
import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

np.random.seed(6)
iter_num = 0


def cross_entropy_loss(w, y, layers_features_matrices, reversed_closed_list):
    loss = 0
    for j in range(len(y)):
        f_x_j = layers_features_matrices[j][reversed_closed_list[y[j]]]
        loss += -np.log(np.dot(f_x_j, w))
    return loss


def grad_cross_entropy_loss(w, y, layers_features_matrices, reversed_closed_list):
    # for one sample, the gradient is: -f_x_j/(f_x_j * w), where f_x_j is the features vector of layer y[j] for sample j
    res = np.zeros(w.shape[0])
    for j in range(len(y)):
        f_x_j = layers_features_matrices[j][reversed_closed_list[y[j]]]
        res += -f_x_j/np.dot(f_x_j, w)
    return res


def csv_to_xy(path):
    df = pd.read_csv(path)
    x = list(df['heared'])
    y = list(df['expected'])

    return x, y


def callback(xk):
    global iter_num
    iter_num += 1
    print(f'finished iteration number {iter_num} with {xk}')


if __name__ == '__main__':
    train = True
    x, y = csv_to_xy('train.csv')
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=40)
    closed_list = list(pd.read_csv('heb_en_layers.csv')['English'])
    reversed_closed_list = {k: i for i, k in enumerate(closed_list)}
    print('csv done')

    if train:
        # train to learn weights
        layers_features_matrices = create_layers_features_matrix(x_train, closed_list)
        args = (y_train, layers_features_matrices, reversed_closed_list)
        w0 = np.ones(NUM_FEATURES) / NUM_FEATURES
        max_iter = 1000
        w = minimize(fun=cross_entropy_loss, args=args, jac=grad_cross_entropy_loss, x0=w0, method='Newton-CG', options={'disp': True, 'maxiter': max_iter}, tol=1e-4)
        print(w.success)
        print(w.x / np.sum(w.x))

        # save learned weights
        if w.success:
            w = w.x / np.sum(w.x)
            with open('learned_weights.pkl', 'wb') as f:
                pickle.dump(w, f)

    else:
        # load pre-trained weights
        with open('learned_weights.pkl', 'rb') as f:
            w = pickle.load(f)

    with open('learned_weights.pkl', 'rb') as f:
        w = pickle.load(f)
    with open('max_vec.pkl', 'rb') as f:
        max_vec = pickle.load(f)
    # predict and evaluate on test-set
    y_pred = match_input_to_layout(x_test, closed_list, w, threshold=0.4, max_vec=max_vec)
    print('\n\n')
    # acc = accuracy_score(y_test, y_pred)
    acc = 0
    n = 40
    for x_i, y_pred_i, y_true_i in zip(x_test, y_pred, y_test):
        if y_pred_i == y_true_i:
            acc += 1/n
            print('Got right: ', end='')
        else:
            print('Got wrong: ', end='')
        print(f'{x_i} ::: {y_pred_i} ::: {y_true_i}')
    print(acc)
