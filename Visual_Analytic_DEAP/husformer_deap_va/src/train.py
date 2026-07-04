import torch
from torch import nn
import sys
from src import models
from src.utils import *
import torch.optim as optim
import numpy as np
import time
from torch.optim.lr_scheduler import ReduceLROnPlateau
import os
import csv
import pickle
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score, f1_score
from src.eval_metrics import *

def initiate(hyp_params, train_loader, valid_loader, test_loader):
    model = getattr(models, hyp_params.model+'Model')(hyp_params)
    if hyp_params.use_cuda:
        model = model.cuda()

    optimizer = getattr(optim, hyp_params.optim)(model.parameters(), lr=hyp_params.lr)
    criterion = focalloss()
    scheduler = ReduceLROnPlateau(optimizer, mode='min', patience=hyp_params.when, factor=0.1, verbose=True)
    settings = {'model': model,
                'optimizer': optimizer,
                'criterion': criterion,
                'scheduler': scheduler}
    return train_model(settings, hyp_params, train_loader, valid_loader, test_loader)

def train_model(settings, hyp_params, train_loader, valid_loader, test_loader):
    model = settings['model']
    optimizer = settings['optimizer']
    criterion = settings['criterion']
    scheduler = settings['scheduler']
    
    def train(model, optimizer, criterion):
        epoch_loss = 0
        model.train()
        num_batches = hyp_params.n_train // hyp_params.batch_size
        proc_loss, proc_size = 0, 0
        start_time = time.time()
        mae_train2 = 0
        for i_batch, (batch_X, batch_Y, batch_META) in enumerate(train_loader):
            sample_ind, m1,m2,m3,m4,m5 = batch_X
            eval_attr = batch_Y.squeeze(-1)   # if num of labels is 1
            model.zero_grad()
            if hyp_params.use_cuda:
                with torch.cuda.device(0):
                    m1,m2,m3,m4,m5,eval_attr = m1.cuda(),m2.cuda(),m3.cuda(),m4.cuda(),m5.cuda(),eval_attr.cuda()
            batch_size = m1.size(0)
            batch_chunk = hyp_params.batch_chunk
            combined_loss = 0
            net = nn.DataParallel(model) if batch_size > 10 else model
            if batch_chunk > 1:
                raw_loss = combined_loss = 0
                m1_chunks = m1.chunk(batch_chunk, dim=0)
                m2_chunks = m2.chunk(batch_chunk, dim=0)
                m3_chunks = m3.chunk(batch_chunk, dim=0)
                m4_chunks = m4.chunk(batch_chunk, dim=0)
                m5_chunks = m5.chunk(batch_chunk, dim=0)
                eval_attr_chunks = eval_attr.chunk(batch_chunk, dim=0)
                
                for i in range(batch_chunk):
                    m1_i, m2_i, m3_i, m4_i, m5_i = m1_chunks[i],m2_chunks[i],m3_chunks[i],m4_chunks[i],m5_chunks[i]
                    eval_attr_i = eval_attr_chunks[i]
                    preds_i, hiddens_i = net(m1_i, m2_i, m3_i, m4_i, m5_i)
                    
                    raw_loss_i = criterion(preds_i, eval_attr_i) / batch_chunk
                    raw_loss += raw_loss_i
                    raw_loss_i.backward()
                combined_loss = raw_loss 
            else:
                preds, hiddens = net(m1,m2,m3,m4,m5)
                raw_loss = criterion(preds, eval_attr)
                combined_loss = raw_loss 
                combined_loss.backward()
                mae_train1 = mae1(preds,eval_attr)
            mae_train2 += mae_train1
            torch.nn.utils.clip_grad_norm_(model.parameters(), hyp_params.clip)
            optimizer.step()
            
            proc_loss += raw_loss.item() * batch_size
            proc_size += batch_size
            epoch_loss += combined_loss.item() * batch_size
            if i_batch % hyp_params.log_interval == 0 and i_batch > 0:
                avg_loss = proc_loss / proc_size
                elapsed_time = time.time() - start_time
                memory_used = torch.cuda.max_memory_allocated() / (1024.0 * 1024.0)
                print('Epoch {:2d} | Batch {:3d}/{:3d} | Time/Batch(ms) {:5.2f} | Train Loss {:5.4f} | memory_used {:5.4f} MB'.
                      format(epoch, i_batch, num_batches, elapsed_time * 1000 / hyp_params.log_interval, avg_loss,memory_used))
                proc_loss, proc_size = 0, 0
                start_time = time.time()
                
        mae_train = mae_train2 / num_batches
        print('mae_train:',mae_train)
        return epoch_loss / hyp_params.n_train, mae_train

    def evaluate(model, criterion, test=False):
        model.eval()
        loader = test_loader if test else valid_loader
        total_loss = 0.0
    
        results = []
        truths = []

        with torch.no_grad():
            for i_batch, (batch_X, batch_Y, batch_META) in enumerate(loader):
                sample_ind,m1,m2,m3,m4,m5 = batch_X
                eval_attr = batch_Y.squeeze(dim=-1) # if num of labels is 1
            
                if hyp_params.use_cuda:
                    with torch.cuda.device(0):
                        m1,m2,m3,m4,m5,eval_attr = m1.cuda(),m2.cuda(),m3.cuda(),m4.cuda(),m5.cuda(),eval_attr.cuda()      
                batch_size = m1.size(0)
                net = nn.DataParallel(model) if batch_size > 10 else model
                preds, _ = net(m1,m2,m3,m4,m5)
                total_loss += criterion(preds, eval_attr).item() * batch_size

                # Collect the results into dictionary
                results.append(preds)
                truths.append(eval_attr)
                
        avg_loss = total_loss / (hyp_params.n_test if test else hyp_params.n_valid)

        results = torch.cat(results)
        truths = torch.cat(truths)
        mae = mae1(results, truths)
        return avg_loss, results, truths, mae
    mae_train1 = []
    mae_valid1 = []
    mae_test1 = []
    best_valid = 1e8

    # FIX (2026-07-04, husformer_deap_va): antes de este fix, TODAS las métricas
    # por época (train_loss, mae_train, valid_loss, mae_valid, test_loss,
    # mae_test, memoria, etc.) vivían solo como listas de Python en RAM y como
    # texto impreso por consola -> se perdían apenas terminaba el proceso, y no
    # había forma de graficarlas después sin volver a entrenar desde cero.
    #
    # Ahora se escriben, época por época, a un CSV en disco
    # (output/<name>_metrics.csv). Dos decisiones de diseño explícitas, pedidas
    # por Russell:
    #   1) "Guardar todo lo necesario para graficar más adelante": se guarda
    #      una fila con TODO lo que ya se calculaba por época (no solo lo que
    #      se imprimía), incluyendo el train_loss (antes se descartaba con
    #      "_, mae_train = train(...)") y el learning_rate vigente (útil para
    #      ver en la gráfica exactamente quë época bajó el LR por el
    #      scheduler).
    #   2) "Que cada corrida sobreescriba, no se acumule con corridas viejas":
    #      el archivo se abre en modo 'w' (sobreescribir) UNA sola vez, antes
    #      de la época 1 de esta corrida, y se escribe el encabezado. A partir
    #      de ahí cada época se agrega con 'a' (append) -- pero dentro de la
    #      MISMA corrida, así que no se mezcla con datos de una corrida
    #      anterior. Abrir/cerrar el archivo en cada época (en vez de dejarlo
    #      abierto durante las 40 épocas) es intencional: así, si el proceso se
    #      corta a la mitad (Ctrl+C, corte de luz, OOM en una época tardía),
    #      las épocas ya completadas quedan guardadas en el CSV de todos
    #      modos, no se pierden por no haber hecho un flush/close final.
    metrics_csv_path = f'output/{hyp_params.name}_metrics.csv'
    if not os.path.exists('output/'):
        os.makedirs('output/')
    metrics_csv_header = [
        'epoch', 'timestamp', 'duration_sec',
        'train_loss', 'mae_train',
        'valid_loss', 'mae_valid', 'valid_corr', 'valid_mult_acc', 'valid_f1',
        'test_loss', 'mae_test', 'test_corr', 'test_mult_acc', 'test_f1',
        'memory_used_mb', 'n_parameters', 'learning_rate', 'model_saved',
    ]
    with open(metrics_csv_path, 'w', newline='') as metrics_csv_file:
        csv.writer(metrics_csv_file).writerow(metrics_csv_header)
    print(f"[metrics] Guardando metricas por epoca en {metrics_csv_path} (se sobreescribe en cada corrida nueva)")

    for epoch in range(1, hyp_params.num_epochs+1):
        start = time.time()
        train_loss,mae_train = train(model, optimizer, criterion)
        val_loss, val_results, val_truths, mae_valid = evaluate(model,criterion, test=False)
        test_loss, test_results, test_truths, mae_test = evaluate(model,criterion, test=True)
        mae_train1.append(mae_train)
        mae_valid1.append(mae_valid)
        mae_test1.append(mae_test)

        # FIX (2026-07-04, husformer_deap_va): antes 'results'/'truths' de
        # evaluate() se descartaban con '_' -- ya se estaban calculando cada
        # época de todos modos (para mae_valid/mae_test), así que reusarlos
        # aquí para obtener corr/mult_acc/f1 por época (además del MAE) no
        # agrega ningún costo extra de cómputo. verbose=False para no
        # imprimir 2 bloques extra por época en consola (el print final,
        # sobre el mejor modelo en test, se mantiene igual que antes).
        _, valid_corr, valid_mult_acc, valid_f1 = eval_hus(val_results, val_truths, exclude_zero=True, verbose=False)
        _, test_corr, test_mult_acc, test_f1 = eval_hus(test_results, test_truths, exclude_zero=True, verbose=False)

        end = time.time()
        duration = end-start
        scheduler.step(val_loss)    # Decay learning rate by validation loss
        memory_used = torch.cuda.max_memory_allocated() / (1024.0 * 1024.0)
        print("-"*50)
        print('Epoch {:2d} | Time {:5.4f} sec | Valid Loss {:5.4f} | MAE-valid{:5.4f} | Test Loss {:5.4f} | MAE-test{:5.4f} | memory_used{:5.4f} MB'.format(epoch, duration, val_loss, mae_valid,test_loss,mae_test,memory_used))
        print("-"*50)
        n_parameters = sum(p.numel() for p in model.parameters())
        print('n_parameters:',n_parameters)
        model_saved_this_epoch = False
        if val_loss < best_valid:
            print(f"Saved model at output/{hyp_params.name}.pt!")
            save_model(hyp_params, model, name=hyp_params.name)
            best_valid = val_loss
            model_saved_this_epoch = True

        current_lr = optimizer.param_groups[0]['lr']
        with open(metrics_csv_path, 'a', newline='') as metrics_csv_file:
            csv.writer(metrics_csv_file).writerow([
                epoch,
                time.strftime('%Y-%m-%d %H:%M:%S'),
                f'{duration:.4f}',
                f'{train_loss:.6f}',
                f'{mae_train:.6f}',
                f'{val_loss:.6f}',
                f'{mae_valid:.6f}',
                f'{valid_corr:.6f}',
                f'{valid_mult_acc:.6f}',
                f'{valid_f1:.6f}',
                f'{test_loss:.6f}',
                f'{mae_test:.6f}',
                f'{test_corr:.6f}',
                f'{test_mult_acc:.6f}',
                f'{test_f1:.6f}',
                f'{memory_used:.4f}',
                n_parameters,
                current_lr,
                model_saved_this_epoch,
            ])

    model = load_model(hyp_params, name=hyp_params.name)
    _, results, truths,_ = evaluate(model, criterion, test=True)
    n_parameters = sum(p.numel() for p in model.parameters())
    print('n_parameters:',n_parameters)
    eval_hus(results, truths, True)
    
    sys.stdout.flush()
    input('[Press Any Key to start another run]')
