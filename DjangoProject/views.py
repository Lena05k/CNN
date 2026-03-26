from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import onnxruntime
import numpy as np
from PIL import Image
import os

imageClassList = {'0': 'Пингвин', '1': 'Тупик', '2': 'Альбатрос'}  #Сюда указать классы

def scoreImagePage(request):
    return render(request, 'index.html')

def predictImage(request):
    fileObj = request.FILES['filePath']
    fs = FileSystemStorage()
    filePathName = fs.save('images/'+fileObj.name,fileObj)
    filePathName = fs.url(filePathName)
    modelName = request.POST.get('modelName')
    scorePrediction = predictImageData(modelName, '.'+filePathName)
    context = {'scorePrediction': scorePrediction}
    return render(request, 'index.html', context)

def predictImageData(modelName, filePath):
    img = Image.open(filePath).convert("RGB")
    img = np.asarray(img.resize((32, 32), Image.ANTIALIAS))
    model_path = os.path.join(settings.MEDIA_ROOT, 'cifar100_CNN_RESNET20.onnx')
    sess = onnxruntime.InferenceSession(model_path)
    outputOFModel = np.argmax(sess.run(None, {'input': np.asarray([img]).astype(np.float32)}))
    score = imageClassList[str(outputOFModel)]
    return score
