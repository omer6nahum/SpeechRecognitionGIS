import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from main import match_input_to_layout, create_layers_features_matrix
import matplotlib.gridspec as gridspec

np.random.seed(28)


def cut_str(s, k):
    if len(s) <= k:
        return s
    return s[:k] + '...'


with open('learned_weights.pkl', 'rb') as f:
    w = pickle.load(f)
with open('max_vec.pkl', 'rb') as f:
    max_vec = pickle.load(f)
closed_list = list(pd.read_csv('heb_en_layers.csv')['English'])
reversed_closed_list = {k: i for i, k in enumerate(closed_list)}

input_text = ['change into clusters ranking in relation to 2015']
input_text += ['sports field']
input_text += ['we do well senior citizen']

scores_matrix = create_layers_features_matrix(input_text, closed_list, max_vec=max_vec)
samples_layers_prob = np.array([np.matmul(f_x, w) for f_x in scores_matrix])

k = 5
f = plt.figure(figsize=(15, 6))
gs = gridspec.GridSpec(9, 50)
ax1 = plt.subplot(gs[1:2, :43])
ax2 = plt.subplot(gs[4:5, :43])
ax3 = plt.subplot(gs[7:8, :43])
ax4 = plt.subplot(gs[:, 45:46])
axes = [ax1, ax2, ax3, ax4]

for i in range(len(axes) - 1):
    sns.heatmap([samples_layers_prob[i]], linewidths=.5, cmap="YlGnBu", vmin=0, vmax=1,
                ax=axes[i], cbar_ax=axes[-1])
    axes[i].set_title(f'{input_text[i]}')
    chosen_k = [np.argmax([samples_layers_prob[i]])] + list(np.random.randint(0, samples_layers_prob.shape[1], size=k-1))
    print(np.max(samples_layers_prob[i]))
    print(w)
    axes[i].set_xticks(np.array(chosen_k) + 0.5)
    axes[i].set_xticklabels([cut_str(closed_list[j], 20) for j in chosen_k], rotation=20)
f.suptitle('Layers Scores', fontsize=20)

axes[-1].set_yticks(np.arange(0, 1.01, 0.2))
axes[-1].set_yticklabels(['0.0', '0.2', '0.4 - threshold', '0.6', '0.8', '1.0'])
plt.show()