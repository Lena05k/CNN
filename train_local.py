#!/usr/bin/env python
"""
Локальное обучение модели классификации крокодилов, аллигаторов, кайманов
Использование: python train_local.py
"""

from PIL import Image
from glob import glob
import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader, Dataset
from torchvision import transforms as T
from sklearn.metrics import classification_report
import os
from pathlib import Path

# ==============================================================================
# Конфигурация
# ==============================================================================

# Ваши классы
CLASSES = ['Пингвин', 'Тупик', 'Альбатрос']
IMAGE_SIZE = 32
BATCH_SIZE = 32
EPOCHS = 60
LEARNING_RATE = 0.001

# Пути к данным (локально)
DATA_DIR = Path('data')

# ==============================================================================
# Загрузка данных
# ==============================================================================

print("="*60)
print("Загрузка данных...")
print("="*60)

images = []
images_t = []
classes = []
classes_t = []

for CLASS_IDX, CLASS_NAME in enumerate(CLASSES):
    # Локальный путь
    path_class = DATA_DIR / CLASS_NAME / '*.*'
    print(f'Путь: {path_class}')
    
    all_photos = list(glob(str(path_class)))
    print(f"Класс '{CLASS_NAME}': найдено {len(all_photos)} изображений")
    
    for i, photo in enumerate(all_photos, 1):
        try:
            img = Image.open(photo).convert('RGB')
            img = img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
            
            # 80% train, 20% test
            if i > int(len(all_photos) * 0.8):
                images_t.append(np.asarray(img))
                classes_t.append(CLASS_IDX)
            else:
                images.append(np.asarray(img))
                classes.append(CLASS_IDX)
        except Exception as e:
            print(f"  ⚠️  Ошибка {photo}: {e}")

train_X = np.array(images)
train_y = np.array(classes)
test_X = np.array(images_t)
test_y = np.array(classes_t)

print(f"\n=== Статистика ===")
print(f"Train: {len(train_X)} изображений")
print(f"Test: {len(test_X)} изображений")
print(f"Размер: {IMAGE_SIZE}x{IMAGE_SIZE}x3")

if len(train_X) == 0:
    print("\n❌ Нет данных для обучения!")
    print(f"Проверьте папки: {DATA_DIR}/крокодил/, {DATA_DIR}/аллигатор/, {DATA_DIR}/кайман/")
    exit(1)

# ==============================================================================
# Аугментация данных
# ==============================================================================

print("\nНастройка аугментации...")

train_transform = T.Compose([
    T.ToPILImage(),
    T.RandomHorizontalFlip(p=0.5),
    T.RandomRotation(15),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    T.ToTensor(),
])

test_transform = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
])

class AugmentedDataset(Dataset):
    def __init__(self, images, labels, transform=None):
        self.images = images
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img = self.images[idx]
        label = self.labels[idx]
        
        if self.transform:
            img = self.transform(img)
        
        return img, F.one_hot(torch.tensor(label, dtype=torch.int64), num_classes=len(CLASSES)).float()

from torch.utils.data import Dataset

train_dataset = AugmentedDataset(train_X, train_y, transform=train_transform)
test_dataset = AugmentedDataset(test_X, test_y, transform=test_transform)

dataloader = {
    'train': DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, drop_last=True),
    'test': DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, drop_last=False)
}

print(f"Train batches: {len(dataloader['train'])}")
print(f"Test batches: {len(dataloader['test'])}")

# ==============================================================================
# Модель с Transfer Learning
# ==============================================================================

print("\nЗагрузка модели ResNet18...")

from torchvision import models

class TransferLearningModel(nn.Module):
    def __init__(self, num_classes=3):
        super(TransferLearningModel, self).__init__()
        
        # Загружаем предобученную ResNet18
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        
        # Замораживаем ранние слои
        for param in list(self.backbone.parameters())[:-20]:
            param.requires_grad = False
        
        # Заменяем последний слой
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        # ResNet ожидает NCHW
        if x.dim() == 4 and x.shape[3] == 3:
            x = x.permute(0, 3, 1, 2)
        return self.backbone(x)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Устройство: {device}")

model = TransferLearningModel(num_classes=len(CLASSES)).to(device)

# ==============================================================================
# Оптимизатор и функция потерь
# ==============================================================================

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)

# ==============================================================================
# Обучение
# ==============================================================================

print("\n" + "="*60)
print("Обучение модели...")
print("="*60)

train_losses = []
val_losses = []
train_accs = []
val_accs = []

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    # Training
    for inputs, labels in dataloader['train']:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        _, label_class = labels.max(1)
        total += labels.size(0)
        correct += predicted.eq(label_class).sum().item()
    
    train_loss = running_loss / len(dataloader['train'])
    train_acc = 100. * correct / total
    train_losses.append(train_loss)
    train_accs.append(train_acc)
    
    # Validation
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for inputs, labels in dataloader['test']:
            # Пропускаем батчи размером 1 (проблема с BatchNorm)
            if inputs.size(0) <= 1:
                continue
                
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            _, predicted = outputs.max(1)
            _, label_class = labels.max(1)
            val_total += labels.size(0)
            val_correct += predicted.eq(label_class).sum().item()
    
    if val_total > 0:
        val_loss = val_loss / val_total
        val_acc = 100. * val_correct / val_total
    else:
        val_loss = 0.0
        val_acc = 0.0
    val_losses.append(val_loss)
    val_accs.append(val_acc)
    
    scheduler.step()
    
    print(f'Epoch {epoch+1}/{EPOCHS}:')
    print(f'  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
    print(f'  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')
    print('-' * 50)

print('Обучение завершено!')

# ==============================================================================
# Оценка качества
# ==============================================================================

print("\n" + "="*60)
print("Оценка качества модели")
print("="*60)

for part in ['train', 'test']:
    y_pred = []
    y_true = []
    
    with torch.no_grad():
        for inputs, labels in dataloader[part]:
            inputs = inputs.to(device)
            outputs = model(inputs).cpu().numpy()
            y_pred.append(outputs)
            y_true.append(labels.numpy())
    
    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)
    
    print(f'\n{part.upper()}')
    print(classification_report(
        y_true.argmax(axis=-1),
        y_pred.argmax(axis=-1),
        digits=4,
        target_names=CLASSES
    ))

# ==============================================================================
# Сохранение модели
# ==============================================================================

print("\n" + "="*60)
print("Сохранение модели")
print("="*60)

# Сохранение весов
PATH_PTH = 'model_weights.pth'
torch.save(model.state_dict(), PATH_PTH)
print(f"✓ Веса сохранены: {PATH_PTH}")

# Сохранение всей модели
PATH_PT = 'model_full.pt'
torch.save(model, PATH_PT)
print(f"✓ Модель сохранена: {PATH_PT}")

# Экспорт в ONNX
print("\nЭкспорт в ONNX...")
model.eval()
dummy_input = torch.randn(1, 3, 32, 32).to(device)

ONNX_FILENAME = 'cifar100_CNN_RESNET20.onnx'

torch.onnx.export(
    model,
    dummy_input,
    ONNX_FILENAME,
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
)

print(f"✓ Модель экспортирована: {ONNX_FILENAME}")

# Копирование в папку media Django
import shutil
django_model_path = os.path.join('media', ONNX_FILENAME)
os.makedirs('media', exist_ok=True)
shutil.copy(ONNX_FILENAME, django_model_path)
print(f"✓ Модель скопирована: {django_model_path}")

print("\n" + "="*60)
print("ГОТОВО!")
print("="*60)
print("\nСледующие шаги:")
print("1. Перезапустите Django: python manage.py runserver")
print("2. Откройте http://localhost:8000")
print("3. Загрузите изображение для классификации")
