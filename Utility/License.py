import os
import rsa
import sys
import base64
import random
import tkinter as tk
import tkinter.messagebox
def generate_mapping_for_base64_characters(seed=0, max_index=10000):
    random.seed(seed)
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=Ο"
    mapping = {}
    for index in range(max_index):
        for char in base64_chars:
            while True:
                mapped_code = random.randint(0, 0x10FFFF)
                if not (0xD800 <= mapped_code <= 0xDFFF):
                    break
            mapping[(char, index)] = chr(mapped_code)
    return mapping
def generate_decryption_mapping(encryption_mapping):
    decryption_mapping = {}
    for (char, index), mapped_char in encryption_mapping.items():
        decryption_mapping[(mapped_char, index)] = char
    return decryption_mapping
def complex_encrypt(text,seed=0 ):
    mapping = generate_mapping_for_base64_characters(seed,len(text))
    encrypted_text = ""
    for index, char in enumerate(text):
        encrypted_text += mapping.get((char, index), char)
    return encrypted_text
def complex_decrypt(text, seed=0):
    mapping=generate_decryption_mapping(generate_mapping_for_base64_characters(seed,len(text)))
    decrypted_text = ""
    for index, char in enumerate(text):
        decrypted_text += mapping.get((char, index), char)
    return decrypted_text
try:
    KEY=open(f'..{os.sep}License','r',encoding='UTF32').readlines()
    Public=complex_decrypt(KEY[0])
    Private=complex_decrypt(KEY[1])
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    tk.messagebox.showerror('Error','No License.')
    sys.exit(0)
def Encrypt(Item,Public):
    PublicKey=rsa.PublicKey.load_pkcs1(b'\n'.join([base64.decodebytes(i.encode()) for i in Public.split('Ο')]))
    return base64.encodebytes(rsa.encrypt(Item.encode(),PublicKey)).decode('UTF-8').strip().replace('\n','ο')
def Decrypt(Item,Private):
    PrivateKey=rsa.PrivateKey.load_pkcs1(b'\n'.join([base64.decodebytes(i.encode()) for i in Private.split('Ο')]))
    return rsa.decrypt(base64.decodebytes(Item.encode()),PrivateKey).decode('UTF-8')
