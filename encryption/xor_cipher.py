def xor_encrypt(data, key):

    encrypted = bytearray()

    key_length = len(key)

    for i in range(len(data)):

        key_bit = key[i % key_length]

        encrypted_byte = data[i] ^ key_bit

        encrypted.append(encrypted_byte)

    return encrypted


def xor_decrypt(data, key):

    return xor_encrypt(data, key)