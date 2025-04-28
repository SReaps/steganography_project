from PIL import Image
from PIL import UnidentifiedImageError
import numpy as np
import string
import os
import pillow_avif  

SupportedFiles = ['PNG','JPG','JPEG','GIF','WEBP']

def text_to_binary(text):
    return ''.join([format(ord(char), '08b') for char in text])

def binary_to_text(binary):
    chars = []
    for i in range(0, len(binary),8):
        byte = binary[i:i+8]

        if len(byte) ==8:
            chars.append(chr(int(byte,2)))
    return ''.join(chars)

def load_image(ImagePath):
    try:
        with Image.open(ImagePath) as img:
            if img.format == 'AVIF':
                raise ValueError("AVIF file types are not supported for steganography")

            if img.format not in SupportedFiles:
                raise ValueError(f"Unsupported file types: {img.format}")

            image = img.convert("RGBA" if img.mode not in ("RGB","RGBA") else img.mode)
            if img.format == 'GIF':
                image = image.convert("RGBA")
            return image
    except UnidentifiedImageError:
        raise ValueError("Unidentified image file. Please upload a valid image")

def encode_message(ImagePath,message,bits):
    try:
        if not (1 <= bits <= 8):
            raise ValueError("Bits must be between 1 and 8")

        image = load_image(ImagePath)
        np_img = np.array(image,dtype=np.uint8)

        if np_img.shape[2] == 4:
            rgb = np_img[:, :, :3] 
            alpha = np_img[:, :, 3] #transparency 
        else:
            rgb = np_img
            alpha = None

        flat = rgb.flatten()

        BitHeader = format(bits - 1,'03b')
        BinaryMessage = text_to_binary(message)
        Delimiter = '1111111111111110'
        padding = (bits -(len(BinaryMessage) % bits)) %bits
        BinaryMessage = BinaryMessage +('0'*padding)+Delimiter
        UpdatedMessage = BitHeader +BinaryMessage


        available_bits = len(flat)*bits
        Buffer = 16
        if len(UpdatedMessage)+Buffer >available_bits:
            raise ValueError("Message too long to fit in this image at this bit depth")

        mask = 0xFF ^((1 <<bits)-1)
        CurrentBit = 0 #current position

        for i in range(len(flat)):
            if i < 3:
                flat[i] = (flat[i] & 0b11111110)|int(UpdatedMessage[CurrentBit]) #clears the LSB and sets that LSB to the next bit
                CurrentBit += 1

            elif CurrentBit < len(UpdatedMessage):#checks if there are still any bits left
                cover = UpdatedMessage[CurrentBit:CurrentBit+bits].ljust(bits,'0')#gets the next group of bits and pads it with 0s if needed
                flat[i] = (flat[i] & mask)|int(cover,2) #Clear the LSBs and insert new bits
                CurrentBit += bits

            else:
                break

        RGBEncoded = flat.reshape(rgb.shape)
        if alpha is not None:
            ImgEncoded = np.dstack((RGBEncoded,alpha))
        else:
            ImgEncoded = RGBEncoded

        FormatOutput = image.format if image.format in SupportedFiles else 'PNG'
        EncodedImagePath = os.path.splitext(ImagePath)[0] +"_encoded." +FormatOutput.lower()

           
        save_kwargs = {"format": FormatOutput} # Prepare save settings
        if FormatOutput == "WEBP":
            save_kwargs.update({"lossless": True}) # Enable lossless saving for WebP

        Image.fromarray(ImgEncoded).save(EncodedImagePath, **save_kwargs)
        return EncodedImagePath

    except Exception as e:
        raise ValueError(f"Error during encoding: {str(e)}")

def TextChecker(text):
    for c in text:
        if c not in string.printable:
            return False
    return any(c.isalnum() for c in text)



def decode_message(ImagePath):
    try:
        image = load_image(ImagePath)
        np_img = np.array(image, dtype=np.uint8)

        if np_img.shape[2] == 4: #checks if the image has 4 channels -RGBA
            np_img = np_img[:, :, :3]  #and then excludes alpha

        flat = np_img.flatten()

        BitsReader= ''.join([str(flat[i] & 1) for i in range(3)])
        BitDepth = int(BitsReader,2)+1
        print(f"Extracted bit depth from header: {BitDepth}")

        bits = []
        for i in range(3,len(flat)):
            cover = format(flat[i] & ((1 << BitDepth) -1),f'0{BitDepth}b')
            bits.append(cover)

        BinaryMessage = ''.join(bits)
        Delimiter = '1111111111111110'
        CurrentBit = BinaryMessage.find(Delimiter)

        if CurrentBit == -1:
            raise ValueError("Delimiter not found")

        MessageBits = BinaryMessage[:CurrentBit]
        MessageBits = MessageBits[:len(MessageBits) -(len(MessageBits) %8)]
        message = ''.join(chr(int(MessageBits[i:i+8],2)) for i in range(0,len(MessageBits),8))

        if not TextChecker(message):
            raise ValueError("Decoded message is not a valid ASCII")

        #print("Decoded message:",message)
        return message

    except Exception as e:
        raise ValueError(f"Error during decoding: {str(e)}")



def calculate_char_limit(ImagePath, bits):
    try:
        image = load_image(ImagePath)
        width, height = image.size
        TotalPixels = width * height
        TotalBits = TotalPixels *3 *bits

        BitsReserved = 3 + 16  #header + Delimiter
        Buffer = 16        
        LeftOver = TotalBits - BitsReserved - Buffer

        max_chars = LeftOver //8
        return max_chars
    except Exception as e:
        raise ValueError(f"Error, calculating character limit: {str(e)}")