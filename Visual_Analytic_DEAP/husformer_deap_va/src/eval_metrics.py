import torch
import numpy as np
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score, f1_score


def multiclass_acc(preds, truths):
    multi_acc = np.sum(np.round(preds) == np.round(truths)) / float(len(truths))

    return multi_acc


def logits_to_label(results):
    """
    FIX (2026-07-04, husformer_deap_va, bug #10): convierte los logits
    multi-clase que produce el modelo (shape (batch, 3), uno por clase 0/1/2)
    en la etiqueta original de valencia en la escala {-1, 1, 2} (la misma que
    usan labeling.py y el campo 'label' dentro de husformer.pkl).

    Antes de este fix, mae1()/eval_hus() hacían results.view(-1) asumiendo
    que 'results' era un único valor continuo por ventana (diseño de
    regresión con output_dim=1). Pero output_dim tuvo que fijarse en 3 (ver
    bug #3 en main.py) para que focalloss.forward() pudiera hacer
    log_softmax(pred, dim=1).gather(..., index=target) con target en
    {0,1,2} sin salirse de rango. Con output_dim=3, results.view(-1) aplana
    las 3 clases junto con el batch, dando 3x más elementos que 'truths' -> el
    ValueError de broadcasting que se vio al correr con --batch_size 8.

    La forma estándar de pasar de logits multi-clase a una predicción
    evaluable es tomar la clase de mayor probabilidad (argmax) y, como
    'truths' está en la escala original (-1/1/2, no 0/1/2), revertir aquí el
    mapeo de remake_label() (src/utils.py): índice de clase 0 -> etiqueta -1,
    los índices 1 y 2 se quedan igual.
    """
    predicted_class = results.argmax(dim=1)
    predicted_label = torch.where(
        predicted_class == 0,
        -torch.ones_like(predicted_class),
        predicted_class,
    )
    return predicted_label


def mae1(results, truths, exclude_zero=False):
    test_preds = logits_to_label(results).view(-1).cpu().detach().numpy()
    test_truth = truths.view(-1).cpu().detach().numpy()
    mae = np.mean(np.absolute(test_preds - test_truth))
    return mae

def eval_hus(results, truths, exclude_zero=True):

    test_preds = logits_to_label(results).view(-1).cpu().detach().numpy()
    test_truth = truths.view(-1).cpu().detach().numpy()

    non_zeros = np.array([i for i, e in enumerate(test_truth) if e != 0 or (not exclude_zero)])
    test_preds_a5 = np.clip(test_preds, a_min=-2., a_max=2.)
    test_truth_a5 = np.clip(test_truth, a_min=-2., a_max=2.)

    mae = np.mean(np.absolute(test_preds - test_truth))   # Average L1 distance between preds and truths
    corr = np.corrcoef(test_preds, test_truth)[0][1]
    mult_a5 = multiclass_acc(test_preds_a5, test_truth_a5)

    _, _, f1, _ = precision_recall_fscore_support(test_preds[non_zeros], test_truth[non_zeros], average='weighted')
    print("-" * 50)
    print("MAE: ", mae)
    print("Correlation Coefficient: ", corr)
    print("mult_acc: ", mult_a5)
    print('f1_score:', f1)
    print("-" * 50)
