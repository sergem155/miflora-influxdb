import hashlib
import time
import random

def generate_token(): # random 12 bytes
	m=hashlib.md5()
	str = "token.%d.%f" %(time.time(),random.random())
	m.update(str.encode('utf-8'))
	btoken = m.digest()
	btoken = btoken[:12]
	return btoken

def mix_a(mac,product_id):
	mac = mac.replace(':','')
	mac = bytes.fromhex(mac)
	mac = mac[::-1] # reverse mac
	product_id = bytes([product_id % 256, product_id >> 8])
	result=bytearray(8)
	result[0]=mac[0]
	result[1]=mac[2]
	result[2]=mac[5]
	result[3]=product_id[0]
	result[4]=product_id[0]
	result[5]=mac[4]
	result[6]=mac[5]
	result[7]=mac[1]
	return result

def mix_b(mac,product_id):
	mac = mac.replace(':','')
	mac = bytes.fromhex(mac)
	mac = mac[::-1] # reverse mac
	product_id = bytes([product_id % 256, product_id >> 8])
	result=bytearray(8)
	result[0]=mac[0]
	result[1]=mac[2]
	result[2]=mac[5]
	result[3]=product_id[1]
	result[4]=mac[4]
	result[5]=mac[0]
	result[6]=mac[5]
	result[7]=product_id[0]
	return result


def RC4_encrypt(key,value):
	# init keybuf sequentially 
	buf = bytearray(256)
	for i in range(256):
		buf[i] = i
	# salt keybuf with the key
	keylen = len(key)
	acc = 0
	for i in range(256):
		y = (buf[i] + key[i % keylen]) % 256
		acc = (acc + y) % 256
		# swap
		x = buf[i]
		buf[i] = buf[acc]
		buf[acc] = x
	# encrypt
	vallen = len(value)
	result = bytearray(vallen)
	i = 0
	j = 0
	for k in range(vallen):
		# I like to roll-it roll-it
		i = (i + 1) % 256
		j = (j + buf[i]) % 256
		# swap buf[i] and buf[j]
		x = buf[i]
		buf[i] = buf[j]
		buf[j] = x
		# encode
		kb = (buf[i] + buf[j]) % 256
		result[k] = value[k] ^ buf[kb]
	return result
