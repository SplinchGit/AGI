with open('Chat/message_handler.py', 'rb') as f:
    data = f.read()

# Count null bytes
null_count = data.count(b'\x00')
print(f'Found {null_count} null bytes')

# Remove null bytes
clean_data = data.replace(b'\x00', b'')

# Write cleaned data
with open('Chat/message_handler.py', 'wb') as f:
    f.write(clean_data)

print('File cleaned!')