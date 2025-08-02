with open('UI/chat_cli.py', 'rb') as f:
    data = f.read()

# Count null bytes
null_count = data.count(b'\x00')
print(f'Found {null_count} null bytes in CLI')

# Remove null bytes
clean_data = data.replace(b'\x00', b'')

# Write cleaned data
with open('UI/chat_cli.py', 'wb') as f:
    f.write(clean_data)

print('CLI file cleaned!')