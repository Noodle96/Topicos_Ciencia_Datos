import torch
from torch import nn
import torch.nn.functional as F

from modules.transformer import TransformerEncoder


class HUSFORMERModel(nn.Module):
    def __init__(self, hyp_params):

        super(HUSFORMERModel, self).__init__()
        self.orig_d_m1, self.orig_d_m2, self.orig_d_m3,self.orig_d_m4,self.orig_d_m5  = hyp_params.orig_d_m1, hyp_params.orig_d_m2, hyp_params.orig_d_m3,hyp_params.orig_d_m4,hyp_params.orig_d_m5
        # FIX (2026-07-06, husformer_deap_va, bug #4): el repo original traía
        # este valor hardcodeado en 30, pero el README de Husformer recomienda
        # 40 -- Russell decidió usar 40 para ser fiel a la config recomendada
        # por los autores (todavía no se había corrido la primera prueba de
        # 40 épocas, así que no había costo de re-entrenar).
        self.d_m = 40
        self.num_heads = hyp_params.num_heads
        self.layers = hyp_params.layers
        self.attn_dropout = hyp_params.attn_dropout
        self.relu_dropout = hyp_params.relu_dropout
        self.res_dropout = hyp_params.res_dropout
        self.out_dropout = hyp_params.out_dropout
        self.embed_dropout = hyp_params.embed_dropout
        self.attn_mask = hyp_params.attn_mask

        # FIX (2026-07-06, husformer_deap_va): 'combined_dim' estaba
        # hardcodeado en 30 POR SEPARADO de self.d_m, en vez de derivarse de
        # él. 'last_hs' (la salida de self.final_conv, ver forward() más
        # abajo) tiene dimensión self.d_m, y es exactamente lo que recibe
        # self.out_layer -- si combined_dim se queda en 30 mientras d_m sube a
        # 40, self.out_layer queda con nn.Linear(30, output_dim) esperando un
        # vector de 30, pero last_hs le llega de tamaño 40: truena de
        # inmediato en el primer forward con un error de multiplicación de
        # matrices (shapes incompatibles). Por eso combined_dim se deriva
        # ahora de self.d_m en vez de repetir el número a mano -- así, si en
        # el futuro se vuelve a cambiar d_m, no hace falta acordarse de tocar
        # esta línea también.
        combined_dim = self.d_m
        output_dim = hyp_params.output_dim
        self.channels = hyp_params.m1_len+hyp_params.m2_len+hyp_params.m3_len+hyp_params.m4_len+hyp_params.m5_len
        
        # 1. Temporal convolutional layers
        self.proj_m1 = nn.Conv1d(self.orig_d_m1, self.d_m, kernel_size=1, padding=0, bias=False)
        self.proj_m2 = nn.Conv1d(self.orig_d_m2, self.d_m, kernel_size=1, padding=0, bias=False)
        self.proj_m3 = nn.Conv1d(self.orig_d_m3, self.d_m, kernel_size=1, padding=0, bias=False)
        self.proj_m4 = nn.Conv1d(self.orig_d_m4, self.d_m, kernel_size=1, padding=0, bias=False)
        self.proj_m5 = nn.Conv1d(self.orig_d_m5, self.d_m, kernel_size=1, padding=0, bias=False)
        self.final_conv = nn.Conv1d(self.channels, 1, kernel_size=1, padding=0, bias=False)
        
        # 2. Cross-modal Attentions
        self.trans_m1_all = self.get_network(self_type='m1_all', layers=3)
        self.trans_m2_all = self.get_network(self_type='m2_all', layers=3)
        self.trans_m3_all = self.get_network(self_type='m3_all', layers=3)
        self.trans_m4_all = self.get_network(self_type='m4_all', layers=3)
        self.trans_m5_all = self.get_network(self_type='m5_all', layers=3)
        
        # 3. Self Attentions
        self.trans_final = self.get_network(self_type='policy', layers=5)
        
        # 4. Projection layers
        self.proj1 = self.proj2 = nn.Linear(combined_dim, combined_dim)
        self.out_layer = nn.Linear(combined_dim, output_dim)

    def get_network(self, self_type='l', layers=-1):
        if self_type in ['m1_all','m2_all','m3_all','m4_all','m5_all','policy']:
            embed_dim, attn_dropout = self.d_m, self.attn_dropout
        else:
            raise ValueError("Unknown network type")
        
        return TransformerEncoder(embed_dim=embed_dim,
                                  num_heads=self.num_heads,
                                  layers=max(self.layers, layers),
                                  attn_dropout=attn_dropout,
                                  relu_dropout=self.relu_dropout,
                                  res_dropout=self.res_dropout,
                                  embed_dropout=self.embed_dropout,
                                  attn_mask=self.attn_mask)
            
    def forward(self,m1,m2,m3,m4,m5,return_attn=False):
        # FIX (2026-07-06, husformer_deap_va, bug #6): antes, cada
        # self.trans_*_all(...)/self.trans_final(...) devolvía un único
        # tensor -- los pesos de atención cross-modal que ya calculaba
        # internamente MultiheadAttention (ver modules/multihead_attention.py,
        # nunca se tocó, siempre los retornó) se descartaban 2 niveles más
        # arriba, en TransformerEncoderLayer.forward() (modules/transformer.py),
        # con "x, _ = self.self_attn(...)". Se corrigió TransformerEncoderLayer
        # y TransformerEncoder para que YA NO descarten esos pesos, sino que
        # los devuelvan junto con la salida normal -- por eso ahora cada
        # self.trans_*_all(...) devuelve una tupla (salida, lista_de_pesos_por_capa)
        # en vez de un tensor solo.
        #
        # El parámetro 'return_attn' (default False) es lo que mantiene esto
        # 100% compatible con el resto del pipeline ya probado: train.py y
        # test.py siguen llamando al modelo como "preds, hiddens = net(m1,...,m5)"
        # sin cambiar una sola línea, y con return_attn=False (el default) el
        # forward sigue devolviendo exactamente (output, last_hs) como antes
        # -- desempacar la atención de cada trans_*_all no tiene costo extra
        # (ya se calculaba, solo se estaba tirando), así que no afecta ni la
        # velocidad ni el resultado del entrenamiento ya validado. El único
        # que necesita return_attn=True es el futuro script de extracción de
        # representaciones/atención para las vistas del sistema.
        m_1 = m1.transpose(1, 2)
        m_2 = m2.transpose(1, 2)
        m_3 = m3.transpose(1, 2)
        m_4 = m4.transpose(1, 2)
        m_5 = m5.transpose(1, 2)
        # Project features
        proj_x_m1 = m_1 if self.orig_d_m1 == self.d_m else self.proj_m1(m_1)
        proj_x_m2 = m_2 if self.orig_d_m2 == self.d_m else self.proj_m2(m_2)
        proj_x_m3 = m_3 if self.orig_d_m3 == self.d_m else self.proj_m3(m_3)
        proj_x_m4 = m_4 if self.orig_d_m4 == self.d_m else self.proj_m4(m_4)
        proj_x_m5 = m_5 if self.orig_d_m5 == self.d_m else self.proj_m5(m_5)

        proj_x_m1 = proj_x_m1.permute(2, 0, 1)
        proj_x_m2 = proj_x_m2.permute(2, 0, 1)
        proj_x_m3 = proj_x_m3.permute(2, 0, 1)
        proj_x_m4 = proj_x_m4.permute(2, 0, 1)
        proj_x_m5 = proj_x_m5.permute(2, 0, 1)

        proj_all = torch.cat([proj_x_m1 , proj_x_m2 , proj_x_m3 , proj_x_m4 , proj_x_m5], dim=0)

        m1_with_all, attn_m1_all = self.trans_m1_all(proj_x_m1, proj_all, proj_all)
        m2_with_all, attn_m2_all = self.trans_m2_all(proj_x_m2, proj_all, proj_all)
        m3_with_all, attn_m3_all = self.trans_m3_all(proj_x_m3, proj_all, proj_all)
        m4_with_all, attn_m4_all = self.trans_m4_all(proj_x_m4, proj_all, proj_all)
        m5_with_all, attn_m5_all = self.trans_m5_all(proj_x_m5, proj_all, proj_all)

        last_hs1 = torch.cat([m1_with_all, m2_with_all, m3_with_all, m4_with_all, m5_with_all] , dim = 0)
        last_hs2, attn_final = self.trans_final(last_hs1)
        last_hs2 = last_hs2.permute(1, 0, 2)
        last_hs = self.final_conv(last_hs2).squeeze(1)

        output = self.out_layer(last_hs)

        if return_attn:
            # Cada attn_m*_all es una LISTA de tensores (uno por capa de las
            # 3 capas de cada trans_*_all), forma (batch, tgt_len, src_len):
            # para trans_m1_all, tgt_len=m1_len (128, ventana de EEG) y
            # src_len=self.channels (640, la concatenación de las 5
            # modalidades) -- exactamente "cuánta atención le da cada
            # instante de EEG a cada instante de cada modalidad", que es lo
            # que necesita la Vista de Atención Cross-Modal del paper.
            # attn_final es lo mismo pero de la auto-atención final (5 capas),
            # sobre la secuencia ya concatenada de las 5 modalidades.
            attn_weights = {
                'm1_all': attn_m1_all,
                'm2_all': attn_m2_all,
                'm3_all': attn_m3_all,
                'm4_all': attn_m4_all,
                'm5_all': attn_m5_all,
                'final': attn_final,
            }
            return output, last_hs, attn_weights

        return output, last_hs
