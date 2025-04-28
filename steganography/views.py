

from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
from .stego_utils import encode_message
from .stego_utils import decode_message
import numpy as np
import os
import base64




def text_to_binary(text):
    return ''.join([format(ord(char), '08b') for char in text])


def binary_to_text(binary):
    return ''.join([chr(int(binary[i:i+8], 2)) for i in range(0,len(binary),8)])


def home(request):
    return render(request, 'steganography/home.html')

def encode(request):
    if request.method == "POST" and request.FILES.get('image') and request.POST.get('message') and request.POST.get('bits'):
        image_file = request.FILES['image']
        message = request.POST['message']
        
        if image_file.name.lower().endswith('.avif'):
            return JsonResponse({
                "success": False,
                "error": "AVIF images are not supported for encoding. Please use PNG, JPG/JPEG, GIF, or WEBP"
    })
        
        try:
            bits = int(request.POST['bits'])
            if bits < 1 or bits > 8:
                return JsonResponse({
                    "success": False, "error": "Bits must be between 1 and 8"
        })
        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid bits value."})


        temp_image_name = default_storage.save(image_file.name, image_file)
        temp_image_path = os.path.join(settings.MEDIA_ROOT, temp_image_name)  
        try:
            encoded_image_path = encode_message(temp_image_path, message, bits)
            with open(encoded_image_path, "rb") as encoded_file:
                encoded_image_data = base64.b64encode(encoded_file.read()).decode("utf-8")
            
            os.remove(temp_image_path)
            os.remove(encoded_image_path)
            return JsonResponse({
                "success": True, "encoded_image": encoded_image_data
        
        })
        except Exception as e:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            return JsonResponse({
                "success": False, "error": str(e)
    })
    return render(request, "steganography/encode.html")
    

def decode(request):
    if request.method == "POST" and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            print(f"Received image: {image_file.name}")
            temp_image_name = default_storage.save(image_file.name, image_file)
            temp_image_path = os.path.join(settings.MEDIA_ROOT, temp_image_name)
            print(f"Temporary image saved at: {temp_image_path}") 

            decoded_message = decode_message(temp_image_path)
            os.remove(temp_image_path)
            print("Temporary file removed.")
            
            return JsonResponse({
                "success": True, "message": decoded_message
            })


        except Exception as e:
            print(f"Error during decoding: {str(e)}")
            return JsonResponse({
                "success": False, "error": str(e)
            })

    return render(request, "steganography/decode.html")

