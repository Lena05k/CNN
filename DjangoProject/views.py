from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import onnxruntime
import numpy as np
from PIL import Image
import os

imageClassList = {'0': 'Пингвин', '1': 'Тупик', '2': 'Альбатрос'}

def scoreImagePage(request):
    return render(request, 'index.html')

@csrf_exempt
def predictImage(request):
    try:
        fileObj = request.FILES['filePath']
        fs = FileSystemStorage()
        savedName = fs.save('images/' + fileObj.name, fileObj)
        filePath = fs.path(savedName)  # реальный путь на диске, без URL-encoding
        modelName = request.POST.get('modelName')
        scorePrediction = predictImageData(modelName, filePath)
        return JsonResponse({'prediction': scorePrediction})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def predictImageData(modelName, filePath):
    img = Image.open(filePath).convert("RGB")
    img = np.asarray(img.resize((32, 32), Image.LANCZOS))
    model_path = os.path.join(settings.MEDIA_ROOT, 'models', 'cifar100_CNN_RESNET20.onnx')
    sess = onnxruntime.InferenceSession(model_path)
    outputOFModel = np.argmax(sess.run(None, {'input': np.asarray([img]).astype(np.float32)}))
    score = imageClassList[str(outputOFModel)]
    return score
