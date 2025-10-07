with open("enc_chunks/aes_key.bin", "rb") as f:
    key_bytes = f.read()
print(len(key_bytes), key_bytes.hex())
