from Crypto.Cipher import AES

key = b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
with open("enc_chunks/chunk000.enc", "rb") as f:
    ciphertext = f.read()

iv = bytes.fromhex("585e7e11eb50e0f2e7b2605d")
tag = bytes.fromhex("2d7cc2fda347157342f24d84838f61cb")

cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
plaintext = cipher.decrypt_and_verify(ciphertext, tag)

with open("decrypted_chunk000.mp4", "wb") as f:
    f.write(plaintext)