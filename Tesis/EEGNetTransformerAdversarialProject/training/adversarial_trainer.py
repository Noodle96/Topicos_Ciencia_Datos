# training/adversarial_trainer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


@dataclass(frozen=True)
class AdversarialEpochStats:
    """
    Estadísticas agregadas de una época adversarial.
    """
    loss_total: float
    loss_class: float
    loss_domain: float
    acc_class: float
    acc_domain: float


def _accuracy_from_logits(logits: torch.Tensor, targets: torch.Tensor) -> float:
    """
    Calcula accuracy (0..1) usando argmax.
    """
    preds: torch.Tensor = torch.argmax(logits, dim=1)
    correct: torch.Tensor = (preds == targets).sum()
    total: int = int(targets.numel())
    return float(correct.item()) / float(total) if total > 0 else 0.0


def _compute_grl_lambda(
    step: int,
    total_steps: int,
    lambda_max: float = 1.0,
) -> float:
    """
    Scheduler típico de DANN (Ganin et al.):
      lambda(p) = 2/(1+exp(-10p)) - 1
    donde p = step/total_steps

    - Empieza cerca de 0
    - Sube gradualmente hacia lambda_max
    """
    if total_steps <= 0:
        return float(lambda_max)

    p: float = float(step) / float(total_steps)
    # Clamp para seguridad numérica
    p = max(0.0, min(1.0, p))

    # Formula DANN
    val: float = 2.0 / (1.0 + float(torch.exp(torch.tensor(-10.0 * p)).item())) - 1.0
    return float(lambda_max) * float(val)


def train_one_epoch_adversarial(
    *,
    model: nn.Module,
    dataloader: DataLoader,
    criterion_class: nn.Module,
    criterion_domain: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    total_epochs: int,
    lambda_max: float = 1.0,
    use_amp: bool = True,
    debug_print_every: int = 0,
) -> AdversarialEpochStats:
    """
    Entrena 1 época en modo adversarial (DANN).

    Espera que el dataloader entregue tuplas:
      (x, y_class, y_domain)

    y que el modelo retorne:
      (class_logits, domain_logits) = model(x, grl_lambda=<float>)

    Args:
        model: modelo adversarial.
        dataloader: DataLoader con batches (x, y_class, y_domain).
        criterion_class: CrossEntropy para clases (bckg/seizure).
        criterion_domain: CrossEntropy para dominio (patient_id u otro).
        optimizer: optimizador.
        device: cuda/cpu.
        epoch: época actual (1..total_epochs).
        total_epochs: total de épocas.
        lambda_max: máximo peso del branch de dominio.
        use_amp: mixed precision para ahorrar VRAM.
        debug_print_every: si >0, imprime cada N batches.

    Returns:
        AdversarialEpochStats con pérdidas y accuracies.
    """
    model.train()

    scaler: Optional[torch.cuda.amp.GradScaler]
    if use_amp and device.type == "cuda":
        scaler = torch.cuda.amp.GradScaler()
    else:
        scaler = None

    running_total: float = 0.0
    running_class: float = 0.0
    running_domain: float = 0.0

    correct_class: int = 0
    correct_domain: int = 0
    total_samples: int = 0

    # total_steps para schedule global dentro de una época
    total_steps: int = len(dataloader)

    for batch_idx, batch in enumerate(dataloader, start=1):
        x, y_class, y_domain = batch  # type: ignore[misc]

        x = x.to(device, non_blocking=True)
        y_class = y_class.to(device, non_blocking=True)
        y_domain = y_domain.to(device, non_blocking=True)

        bsz: int = int(y_class.size(0))
        total_samples += bsz

        # (Opcional) schedule tipo DANN para GRL
        # Usamos step global dentro de la época
        grl_lambda: float = _compute_grl_lambda(
            step=batch_idx - 1,
            total_steps=total_steps,
            lambda_max=lambda_max,
        )

        optimizer.zero_grad(set_to_none=True)

        if scaler is not None:
            with torch.cuda.amp.autocast():
                class_logits, domain_logits = model(x, grl_lambda=grl_lambda)  # type: ignore[call-arg]
                loss_class: torch.Tensor = criterion_class(class_logits, y_class)
                loss_domain: torch.Tensor = criterion_domain(domain_logits, y_domain)
                loss_total: torch.Tensor = loss_class + (grl_lambda * loss_domain)

            scaler.scale(loss_total).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            class_logits, domain_logits = model(x, grl_lambda=grl_lambda)  # type: ignore[call-arg]
            loss_class = criterion_class(class_logits, y_class)
            loss_domain = criterion_domain(domain_logits, y_domain)
            loss_total = loss_class + (grl_lambda * loss_domain)

            loss_total.backward()
            optimizer.step()

        # Acumular pérdidas ponderadas por batch
        running_total += float(loss_total.item()) * bsz
        running_class += float(loss_class.item()) * bsz
        running_domain += float(loss_domain.item()) * bsz

        # Accuracy
        pred_class: torch.Tensor = torch.argmax(class_logits, dim=1)
        pred_domain: torch.Tensor = torch.argmax(domain_logits, dim=1)

        correct_class += int((pred_class == y_class).sum().item())
        correct_domain += int((pred_domain == y_domain).sum().item())

        if debug_print_every > 0 and (batch_idx % debug_print_every == 0):
            acc_c: float = float((pred_class == y_class).float().mean().item())
            acc_d: float = float((pred_domain == y_domain).float().mean().item())
            print(
                f"[TRAIN][Epoch {epoch}/{total_epochs}][Batch {batch_idx}/{total_steps}] "
                f"lambda={grl_lambda:.4f} "
                f"loss_total={loss_total.item():.4f} "
                f"loss_class={loss_class.item():.4f} "
                f"loss_domain={loss_domain.item():.4f} "
                f"acc_class={acc_c:.3f} "
                f"acc_domain={acc_d:.3f}"
            )

    # Promedios
    denom: float = float(total_samples) if total_samples > 0 else 1.0

    avg_total: float = running_total / denom
    avg_class: float = running_class / denom
    avg_domain: float = running_domain / denom

    acc_class: float = float(correct_class) / denom
    acc_domain: float = float(correct_domain) / denom

    print(
        f"✅ [TRAIN][Epoch {epoch}/{total_epochs}] "
        f"loss_total={avg_total:.4f} loss_class={avg_class:.4f} loss_domain={avg_domain:.4f} "
        f"acc_class={acc_class:.4f} acc_domain={acc_domain:.4f}"
    )

    return AdversarialEpochStats(
        loss_total=avg_total,
        loss_class=avg_class,
        loss_domain=avg_domain,
        acc_class=acc_class,
        acc_domain=acc_domain,
    )


@torch.no_grad()
def validate_one_epoch_adversarial(
    *,
    model: nn.Module,
    dataloader: DataLoader,
    criterion_class: nn.Module,
    criterion_domain: nn.Module,
    device: torch.device,
    epoch: int,
    total_epochs: int,
    lambda_eval: float = 1.0,
    use_amp: bool = True,
) -> AdversarialEpochStats:
    """
    Valida 1 época en modo adversarial.

    Nota importante:
    - En validación NO hacemos backward.
    - Puedes fijar lambda_eval=1.0, o 0.0 si quieres ignorar dominio al reportar.

    Returns:
        AdversarialEpochStats
    """
    model.eval()

    running_total: float = 0.0
    running_class: float = 0.0
    running_domain: float = 0.0

    correct_class: int = 0
    correct_domain: int = 0
    total_samples: int = 0

    for batch in dataloader:
        x, y_class, y_domain = batch  # type: ignore[misc]

        x = x.to(device, non_blocking=True)
        y_class = y_class.to(device, non_blocking=True)
        y_domain = y_domain.to(device, non_blocking=True)

        bsz: int = int(y_class.size(0))
        total_samples += bsz

        if use_amp and device.type == "cuda":
            with torch.cuda.amp.autocast():
                class_logits, domain_logits = model(x, grl_lambda=lambda_eval)  # type: ignore[call-arg]
                loss_class: torch.Tensor = criterion_class(class_logits, y_class)
                loss_domain: torch.Tensor = criterion_domain(domain_logits, y_domain)
                loss_total: torch.Tensor = loss_class + (lambda_eval * loss_domain)
        else:
            class_logits, domain_logits = model(x, grl_lambda=lambda_eval)  # type: ignore[call-arg]
            loss_class = criterion_class(class_logits, y_class)
            loss_domain = criterion_domain(domain_logits, y_domain)
            loss_total = loss_class + (lambda_eval * loss_domain)

        running_total += float(loss_total.item()) * bsz
        running_class += float(loss_class.item()) * bsz
        running_domain += float(loss_domain.item()) * bsz

        pred_class: torch.Tensor = torch.argmax(class_logits, dim=1)
        pred_domain: torch.Tensor = torch.argmax(domain_logits, dim=1)

        correct_class += int((pred_class == y_class).sum().item())
        correct_domain += int((pred_domain == y_domain).sum().item())

    denom: float = float(total_samples) if total_samples > 0 else 1.0

    avg_total: float = running_total / denom
    avg_class: float = running_class / denom
    avg_domain: float = running_domain / denom

    acc_class: float = float(correct_class) / denom
    acc_domain: float = float(correct_domain) / denom

    print(
        f"📌 [VAL][Epoch {epoch}/{total_epochs}] "
        f"loss_total={avg_total:.4f} loss_class={avg_class:.4f} loss_domain={avg_domain:.4f} "
        f"acc_class={acc_class:.4f} acc_domain={acc_domain:.4f}"
    )

    return AdversarialEpochStats(
        loss_total=avg_total,
        loss_class=avg_class,
        loss_domain=avg_domain,
        acc_class=acc_class,
        acc_domain=acc_domain,
    )
