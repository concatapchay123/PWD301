import os
import zipfile
import xml.etree.ElementTree as ET

downloads = 'C:/Users/LENOVO/Downloads'
matches = [f for f in os.listdir(downloads) if '17-10' in f and f.endswith('.docx')]
if not matches:
    print('No matching docx found!')
    exit(1)

docx_path = os.path.join(downloads, matches[0])
out_dir = 'audit-results/2026-10-17-lms-fix/input_report'
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(docx_path, 'r') as z:
    z.extractall(os.path.join(out_dir, 'raw'))

tree = ET.parse(os.path.join(out_dir, 'raw', 'word', 'document.xml'))
root = tree.getroot()

paragraphs = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
    if texts:
        paragraphs.append(''.join(texts))

full_text = '\n\n'.join(paragraphs)
with open(os.path.join(out_dir, 'extracted_text.txt'), 'w', encoding='utf-8') as f:
    f.write(full_text)

media_dir = os.path.join(out_dir, 'raw', 'word', 'media')
media_files = []
if os.path.exists(media_dir):
    media_files = os.listdir(media_dir)

print(f"Extracted successfully: {len(paragraphs)} paragraphs, {len(media_files)} media files.")
