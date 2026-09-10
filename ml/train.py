"""
OceanGuard UNet Training Engine
Trains on Sentinel-1 SAR Oil Spill Dataset (harikrishnacs) with land-aware loss and augmentation.
Runs even in synthetic fallback mode if dataset not downloaded.

Usage:
  python -m ml.train --epochs 5 --batch-size 8 --data-dir ./data/kaggle_sentinel1

Outputs checkpoints to ./checkpoints/
"""
import argparse
import json
import os
from pathlib import Path
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False
    print("Torch not available - training will be simulated")

from .dataset import Sentinel1ChipDataset, download_dataset, scan_dataset_structure
from .config import MODEL_VERSION, BATCH_SIZE, EPOCHS, LR, CHECKPOINT_ROOT

def dice_loss(pred, target, smooth=1e-6):
    pred = torch.sigmoid(pred)
    pred = pred.contiguous().view(-1)
    target = target.contiguous().view(-1)
    intersection = (pred * target).sum()
    dice = (2. * intersection + smooth) / (pred.sum() + target.sum() + smooth)
    return 1 - dice

def bce_dice_loss(pred, target):
    bce = nn.BCEWithLogitsLoss()(pred, target)
    d = dice_loss(pred, target)
    return bce * 0.5 + d * 0.5

if HAS_TORCH:
    class DoubleConv(nn.Module):
        def __init__(self, in_ch, out_ch):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
            )
        def forward(self, x):
            return self.net(x)

    class UNetSmall(nn.Module):
        """Lightweight UNet for 400x400 SAR chips, 1 channel -> 1 mask + classification head"""
        def __init__(self, in_ch=1, out_ch=1, features=[32,64,128,256]):
            super().__init__()
            self.enc1 = DoubleConv(in_ch, features[0])
            self.pool1 = nn.MaxPool2d(2)
            self.enc2 = DoubleConv(features[0], features[1])
            self.pool2 = nn.MaxPool2d(2)
            self.enc3 = DoubleConv(features[1], features[2])
            self.pool3 = nn.MaxPool2d(2)
            self.bottleneck = DoubleConv(features[2], features[3])
            self.up3 = nn.ConvTranspose2d(features[3], features[2], 2, stride=2)
            self.dec3 = DoubleConv(features[3], features[2])
            self.up2 = nn.ConvTranspose2d(features[2], features[1], 2, stride=2)
            self.dec2 = DoubleConv(features[1]*2 if False else features[2], features[1])  # will adjust after cat
            # correct adjust: after cat channels double
            self.dec2 = DoubleConv(features[2], features[1])
            self.up1 = nn.ConvTranspose2d(features[1], features[0], 2, stride=2)
            self.dec1 = DoubleConv(features[1], features[0])
            self.final = nn.Conv2d(features[0], out_ch, 1)
            # Fix dec2 input: features[1]+features[1]
            self.dec2 = DoubleConv(features[1]*2, features[1])
            self.dec3 = DoubleConv(features[2]*2, features[2])
            # classification head (image-level spill presence)
            self.cls_head = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(features[3], 64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, 1)
            )
        def forward(self, x):
            e1 = self.enc1(x)
            p1 = self.pool1(e1)
            e2 = self.enc2(p1)
            p2 = self.pool2(e2)
            e3 = self.enc3(p2)
            p3 = self.pool3(e3)
            b = self.bottleneck(p3)
            # classification branch
            cls_logit = self.cls_head(b)
            u3 = self.up3(b)
            # crop/pad to match e3
            if u3.shape[2:] != e3.shape[2:]:
                u3 = torch.nn.functional.interpolate(u3, size=e3.shape[2:])
            c3 = torch.cat([e3, u3], dim=1)
            d3 = self.dec3(c3)
            u2 = self.up2(d3)
            if u2.shape[2:] != e2.shape[2:]:
                u2 = torch.nn.functional.interpolate(u2, size=e2.shape[2:])
            c2 = torch.cat([e2, u2], dim=1)
            d2 = self.dec2(c2)
            u1 = self.up1(d2)
            if u1.shape[2:] != e1.shape[2:]:
                u1 = torch.nn.functional.interpolate(u1, size=e1.shape[2:])
            c1 = torch.cat([e1, u1], dim=1)
            d1 = self.dec1(c1)
            mask_logit = self.final(d1)
            return mask_logit, cls_logit

def train_loop(args):
    if not HAS_TORCH:
        print("[SIMULATED TRAIN] Torch not available. Simulating training steps...")
        for epoch in range(args.epochs):
            loss = 0.8 * (0.9 ** epoch)
            print(f"SimEpoch {epoch+1}/{args.epochs} loss={loss:.4f} dice={0.45+epoch*0.05:.3f} (synthetic)")
        # synthesize checkpoint marker
        ckpt = CHECKPOINT_ROOT
        ckpt.mkdir(parents=True, exist_ok=True)
        (ckpt / "simulated_checkpoint.json").write_text(json.dumps({"model_version": MODEL_VERSION, "simulated": True, "epochs": args.epochs}))
        print(f"Simulated checkpoint at {ckpt / 'simulated_checkpoint.json'}")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    data_path = Path(args.data_dir) if args.data_dir else download_dataset()
    if data_path is None:
        print("Dataset not found, using synthetic fallback")
        train_ds = Sentinel1ChipDataset(None, split="train", synthetic_fallback=True, max_samples=args.max_samples)
        val_ds = Sentinel1ChipDataset(None, split="val", synthetic_fallback=True, max_samples=max(100, args.max_samples//4))
    else:
        info = scan_dataset_structure(data_path)
        print(f"Dataset inventory: {info['total_images']} images ({info['oil_count']} oil, {info['nooil_count']} nooil)")
        train_ds = Sentinel1ChipDataset(data_path, split="train", max_samples=args.max_samples)
        val_ds = Sentinel1ChipDataset(data_path, split="val", max_samples=max(100, args.max_samples//4 if args.max_samples else None))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)

    model = UNetSmall().to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)

    best_val = float('inf')
    CHECKPOINT_ROOT.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for imgs, masks, labels in train_loader:
            imgs, masks, labels = imgs.to(device), masks.to(device), labels.to(device)
            optimizer.zero_grad()
            mask_logits, cls_logits = model(imgs)
            # Resize masks if needed (model output is 400*? may be 400)
            if mask_logits.shape[2:] != masks.shape[2:]:
                mask_logits = torch.nn.functional.interpolate(mask_logits, size=masks.shape[2:])
            loss_mask = bce_dice_loss(mask_logits, masks)
            loss_cls = nn.BCEWithLogitsLoss()(cls_logits.squeeze(1), labels)
            loss = loss_mask * 0.7 + loss_cls * 0.3
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= max(1, len(train_loader))

        # validation
        model.eval()
        val_loss = 0.0
        iou_sum = 0.0
        with torch.no_grad():
            for imgs, masks, labels in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                mask_logits, cls_logits = model(imgs)
                if mask_logits.shape[2:] != masks.shape[2:]:
                    mask_logits = torch.nn.functional.interpolate(mask_logits, size=masks.shape[2:])
                loss = bce_dice_loss(mask_logits, masks)
                val_loss += loss.item()
                # IoU approx
                preds = (torch.sigmoid(mask_logits) > 0.5).float()
                inter = (preds * masks).sum(dim=(1,2,3))
                union = (preds + masks).clamp(0,1).sum(dim=(1,2,3))
                iou = (inter / (union + 1e-6)).mean().item()
                iou_sum += iou
        val_loss /= max(1, len(val_loader))
        val_iou = iou_sum / max(1, len(val_loader))
        scheduler.step(val_loss)
        print(f"Epoch {epoch+1}/{args.epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_IoU={val_iou:.3f} lr={optimizer.param_groups[0]['lr']:.2e}")

        # checkpoint
        ckpt_path = CHECKPOINT_ROOT / f"unet_epoch{epoch+1:02d}_val{val_loss:.3f}.pt"
        torch.save({
            "epoch": epoch+1,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "val_loss": val_loss,
            "val_iou": val_iou,
            "model_version": MODEL_VERSION
        }, ckpt_path)
        if val_loss < best_val:
            best_val = val_loss
            best_path = CHECKPOINT_ROOT / "best_unet.pt"
            torch.save(model.state_dict(), best_path)
            print(f"  -> New best model saved to {best_path}")

    print(f"Training complete. Best val {best_val:.4f}. Checkpoints in {CHECKPOINT_ROOT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OceanGuard SAR UNet Training")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--data-dir", type=str, default=None, help="Path to kaggle dataset")
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-samples", type=int, default=None, help="Limit samples for quick test")
    args = parser.parse_args()
    train_loop(args)
