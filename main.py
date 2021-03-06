import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from utils import *

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default="config/raw.json", help='config file')
args = parser.parse_args()
params = open_config_file(args.config)

print('------------ Options -------------')
for k, v in vars(params).items():
    print('%s: %s' % (str(k), str(v)))
print('-------------- End ----------------')
print()

np.random.seed(params.seed)
name_dict = {'lr': 'Logistic Regression', 'svm': 'SVM', 'krr': 'Kernel Ridge Regression', 'ksvm': 'Kernel SVM'}
classifier_name = name_dict[params.clf]
if hasattr(params, 'k'):
    if isinstance(params.k, int):
        k_list = [params.k]*3
    else:
        k_list = params.k
else:
    k_list = None
if hasattr(params, 'lmbda'):
    if not isinstance(params.lmbda, list):
        lmbda_list = [params.lmbda]*3
    else:
        lmbda_list = params.lmbda
else:
    lmbda_list = None

# loading data
data = []
labels = []
for k in range(3):
    if params.data_type == 'mat100':
        data_df = pd.read_csv(Path(params.data_dir, f'Xtr{k}_mat100.csv'), header=None, delimiter=' ')
        data.append(data_df)
    else:
        data_df = pd.read_csv(Path(params.data_dir, f'Xtr{k}.csv'))
        data.append(data_df)
    labels_df = pd.read_csv(Path(params.label_dir, f'Ytr{k}.csv'))
    labels.append(labels_df)

# switch from {0,1} binary labels to {-1,1}
if params.relabel:
    for k in range(3):
        labels[k]['Bound'][labels[k]['Bound'] == 0] = -1

# train and validate models on each dataset
if params.val_before_train:
    for k in range(3):
        (data_train, labels_train), (data_val, labels_val) = train_val_split(data[k], labels[k], val_size=params.val_size, seed=params.seed)
        x_tr, y_tr = data_train, labels_train['Bound'].values
        x_val, y_val = data_val, labels_val['Bound'].values
        if params.use_kernel:
            if hasattr(params, 'k'):
                params.k = k_list[k]
            if hasattr(params, 'lmbda'):
                params.lmbda = lmbda_list[k]
            K_tr = get_kernel_matrix(x_tr, x_tr, params)
            K_tr_val = get_kernel_matrix(x_tr, x_val, params)
            clf = get_kernel_classsifier(K_tr, params)
            clf.fit(y_tr)
            pred_tr = clf.predict(K_tr)
            pred_val = clf.predict(K_tr_val)
        else:
            x_tr, x_val = x_tr.values, x_val.values
            clf = get_classsifier(x_tr, y_tr, params)
            clf.fit(x_tr, y_tr)
            pred_tr = clf.predict(x_tr)
            pred_val = clf.predict(x_val)
        acc_tr = accuracy(pred_tr, y_tr)
        acc_val = accuracy(pred_val, y_val)
        print(f'classifier: {classifier_name} | dataset: {k} | training accuracy: {acc_tr:.3f} | validation accuracy: {acc_val:.3f}')
    print()

# get predictions on test datasets
print('generating prediction on test datasets\n')
test_preds_df = generate_test_predictions(data, labels, params, classifier_name, k_list, lmbda_list)
submission_name = get_submission_name(params)
sumbission_path = Path(params.result_dir, submission_name)
sumbission_path.parent.mkdir(parents=True, exist_ok=True)
sumbission_path = sumbission_path.as_posix()
test_preds_df.to_csv(sumbission_path, index=False)
print(f'result successfully saved at: {sumbission_path}')