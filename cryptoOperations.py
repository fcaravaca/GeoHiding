import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from bitstring import BitArray
import reedsolo as rs

KDF_ITER = 1000000
SALT_LENGTH = 16


CODEWORD_BYTES = 20
ECC_BYTES = 4
BLOCK_BYTES = CODEWORD_BYTES - ECC_BYTES


def binary_string_to_bytes(bin_str):
    return BitArray(bin=bin_str).bytes

def bytes_to_binary_string(byte_arr):
    bit_str = []
    for d in byte_arr:
        bit_str += "{0:08b}".format(d)
    return ''.join(c for c in bit_str)


def encode_data(data):
    encoder = rs.RSCodec(ECC_BYTES,CODEWORD_BYTES)
    assert(len(data)%ECC_BYTES== 0)
    #for i in range(int(len(data)/BLOCK_BYTES)):
    #    block = data[i*BLOCK_BYTES:(i+1)*BLOCK_BYTES]
    #    encoded_block = encoder.encode(block)
    #    encoded_data+= encoded_block
    encoded_data = encoder.encode(data)
    return bytes(encoded_data)

def decode_data(data):
    decoder = rs.RSCodec(ECC_BYTES,CODEWORD_BYTES)
    assert (len(data)%CODEWORD_BYTES == 0)
    #for i in range(int(len(data)/CODEWORD_BYTES)):
    #    encoded_block = data[i*CODEWORD_BYTES:(i+1)*CODEWORD_BYTES]
    #    block = decoder.decode(encoded_block)
    #    decoded_data += block[0]
    decoded_data = decoder.decode(data)
    return bytes(decoded_data[0])



# Obtains a Master Secret with a passphrase
def keyDerivationFunction(passphrase, salt=None):
    if salt == None:
        salt = os.urandom(SALT_LENGTH)
    master_secret = hashlib.pbkdf2_hmac("sha512", passphrase.encode(encoding='UTF-8'), salt, KDF_ITER, dklen=32)
    return salt, master_secret


# Input: binary string (e.g. "11110000"), Output: binary string 
def transformBinaryToSecret(plaintext,passphrase):
    plaintext = binary_string_to_bytes(plaintext)
    salt, master_secret = keyDerivationFunction(passphrase)
    encryptor = AES.new(master_secret, AES.MODE_GCM)
    nonce = encryptor.nonce
    ciphered_data, auth_tag = encryptor.encrypt_and_digest(pad(plaintext,BLOCK_BYTES))
    data = ciphered_data + nonce + auth_tag + salt
    assert (len(nonce) == 16)
    assert (len(auth_tag) == 16)
    assert (len(salt) == 16)
    assert(len(data)%16 == 0)
    encoded_data = encode_data(data)
    return bytes_to_binary_string(bytes(encoded_data))

# Input: binary string (e.g. "11110000"), Output: binary string
def transformSecretToBinary(data, passphrase):
    data =  binary_string_to_bytes(data)
    try:
        decoded_data = decode_data(data)
    except:
        raise Exception("Too many errors are detected to be corrected")
    decoded_data = bytes(decoded_data)
    salt = decoded_data[-16:]
    auth_tag = decoded_data[-32:-16]
    nonce = decoded_data[-48:-32]
    ciphertext = decoded_data[:-48]
    _ , master_secret = keyDerivationFunction(passphrase,salt)
    decryptor = AES.new(master_secret, AES.MODE_GCM,nonce=nonce)
    try:
        plaintext = decryptor.decrypt_and_verify(ciphertext,auth_tag)
    except:
        raise Exception("Data integrity has been altered.")
    return bytes_to_binary_string(unpad(plaintext,BLOCK_BYTES))

def sha512HashFromIdPassphrase(id, passphrase):
    id_bytes = str(id).encode('utf-8')
    id_hash = hashlib.sha512(id_bytes).digest()

    # Hash the passphrase and the id hash together
    passphrase_bytes = passphrase.encode('utf-8')
    passphrase_hash = hashlib.sha512(passphrase_bytes).digest()
    combined_hash = hashlib.sha512(id_hash + passphrase_hash).hexdigest()
    return combined_hash



############################# TESTS ###########################

import string
import random

def random_test_data(n):
    test_data = []
    for _ in range(n):
        pass_size = random.randint(4, 25)
        plaintext_size = random.randint(8, 1000*8)
        plaintext = bytes_to_binary_string(os.urandom(plaintext_size))
        passphrase = ''.join(random.choice(string.ascii_letters) for _ in range(pass_size))
        test_data.append((passphrase, plaintext))
    return test_data


N = 5

# No channel noise, should be always be equal
def test_no_noise():
    test_data = random_test_data(N)
    for data in test_data:
        (passphrase, plaintext) = data
        data = transformBinaryToSecret(plaintext, passphrase)
        plaintext_rec = transformSecretToBinary(data, passphrase)
        assert (plaintext == plaintext_rec)
    print("No-noise random test passed!")
    

def test_eight_bit_change():
    test_data = random_test_data(N)
    for data in test_data:
        (passphrase, plaintext) = data
        data = transformBinaryToSecret(plaintext, passphrase)
        for i in range(8):
            pos = random.randint(0,len(data)-1)
            data = list(data)
            data[pos] = '0' if data[pos] == '1' else '1'
            data = ''.join(data)
        plaintext_rec = transformSecretToBinary(data, passphrase)
        assert (plaintext == plaintext_rec)
    print("8-bit-change random test passed")



if __name__ == '__main__':
    test_no_noise()
    test_eight_bit_change()
    
