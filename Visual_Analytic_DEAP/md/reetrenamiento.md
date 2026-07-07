1) Checklist para cuando reentrenes con 40 épocas
Sí, generate_trial_projections.py es uno de los que hay que volver a correr. La cadena completa depende del checkpoint entrenado (hus.pt), así que después de reentrenar hay que regenerar todo lo que se deriva de él, en este orden:

Entrenar: cd husformer_deap_va && python main.py (con 40 épocas) → sobreescribe output/hus.pt.
python -m backend.scripts.husformer.extract_representations → recalcula last_hs/attn_cross_summary/attn_final_summary por ventana desde el checkpoint nuevo.
python -m backend.scripts.husformer.generate_trial_projections → recalcula la agregación por trial y las proyecciones 2D a partir de los .npz nuevos del paso 2.