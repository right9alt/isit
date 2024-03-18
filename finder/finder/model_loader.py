import torch, io, torchvision
from finder.utils import constants
from torchvision.models import resnet50
import clip

def load_classify_model(model_path):
  model = torchvision.models.resnet18(pretrained=False)
  num_ftrs = model.fc.in_features
  model.fc = torch.nn.Linear(num_ftrs, len(constants.CLASSES))  # Изменение последнего слоя для соответствия количеству классов
  model.load_state_dict(torch.load(model_path))
  model.eval()
  return model

def load_photo_model():
  # Загрузка предобученной модели ResNet50
  model = resnet50(pretrained=True)
  model = torch.nn.Sequential(*list(model.children())[:-1])
  model.eval()
  return model

def load_clip_model():
  device = "cuda" if torch.cuda.is_available() else "cpu"
  model, preprocess = clip.load("ViT-B/32", device=device)
  return model, preprocess, device
