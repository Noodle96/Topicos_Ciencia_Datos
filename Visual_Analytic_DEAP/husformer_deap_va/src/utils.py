import torch
import torch.nn as nn
import os
from src.dataset import Multimodal_Datasets


def get_data(args, dataset, split='train'):
    data_path = os.path.join(args.data_path, dataset) + f'_{split}.dt'
    if not os.path.exists(data_path):
        print(f"  - Creating new {split} data")
        data = Multimodal_Datasets(args.data_path, dataset, split)
        torch.save(data, data_path)
    else:
        print(f"  - Found cached {split} data")
        data = torch.load(data_path)
    return data


def save_load_name(args, name=''):
    load_name = name + '_' + args.model
    return load_name


def save_model(args, model, name=''):
    if not os.path.exists('output/'):
        os.makedirs('output/')
    name = save_load_name(args, name)
    torch.save(model, f'output/{args.name}.pt')


def load_model(args, name=''):
    name = save_load_name(args, name)
    model = torch.load(f'output/{args.name}.pt')
    return model


def remake_label(target):
    """
    FIX (2026-07-04, husformer_deap_va): esta función se usaba en focalloss.forward()
    pero no existía en ningún archivo del repo original (NameError garantizado en
    cuanto se llamara a la loss).

    Reconstruye el target de valencia (esquema -1/1/2 usado en labeling.py y en el
    make_data/Pre-DEAP.py original) como índices de clase 0/1/2, que es lo que
    espera torch.log_softmax(...).gather(dim=1, index=target) más abajo en
    focalloss.forward(): el índice de clase debe ser >= 0, así que el único mapeo
    consistente con alpha=[0.1, 0.1, 0.8] (3 pesos, uno por clase) es:
        valencia baja  (-1) -> clase 0
        valencia media ( 1) -> clase 1
        valencia alta  ( 2) -> clase 2
    Si en el futuro se cambia el esquema de etiquetas (labeling.py), esta función
    debe actualizarse junto con él.
    """
    return torch.where(target == -1, torch.zeros_like(target), target)


class focalloss(nn.Module):
    def __init__(self, alpha=[0.1, 0.1, 0.8], gamma=3, reduction='mean'):
        super(focalloss, self).__init__()
        self.alpha = torch.tensor(alpha)
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, pred, target):
        target = remake_label(target).type(torch.int64)
        alpha = self.alpha[target]
        log_softmax = torch.log_softmax(pred, dim=1)
        logpt = torch.gather(log_softmax, dim=1, index=target.view(-1, 1))
        logpt = logpt.view(-1)
        ce_loss = -logpt 
        pt = torch.exp(logpt)
        focal_loss = alpha * ((1 - pt) ** self.gamma * ce_loss).t()
        if self.reduction == "mean":
            return torch.mean(focal_loss)
        if self.reduction == "sum":
            return torch.sum(focal_loss)
        return focal_loss
