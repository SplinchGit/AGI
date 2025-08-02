with open('Chat/chat_manager.py', 'rb') as f:
    data = f.read()

# Replace special characters
bad_char = bytes([0x13])  # \x13
good_char = b'*'  # Simple asterisk

clean_data = data.replace(bad_char, good_char)

with open('Chat/chat_manager.py', 'wb') as f:
    f.write(clean_data)

print('Fixed special characters')