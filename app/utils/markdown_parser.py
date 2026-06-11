import re
from typing import List, Dict, Any

def parse_markdown(content: str) -> Dict[str, Any]:
    lines = content.split('\n')
    result = {
        'headings': [],
        'paragraphs': [],
        'lists': [],
        'code_blocks': [],
        'tables': []
    }
    
    current_list = []
    in_code_block = False
    code_block_lang = ""
    code_block_content = []
    in_table = False
    table_rows = []
    
    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                result['code_blocks'].append({
                    'language': code_block_lang,
                    'content': '\n'.join(code_block_content)
                })
                in_code_block = False
                code_block_lang = ""
                code_block_content = []
            else:
                in_code_block = True
                code_block_lang = line[3:].strip()
            continue
        
        if in_code_block:
            code_block_content.append(line)
            continue
        
        if line.startswith('|'):
            in_table = True
            table_rows.append(line)
            continue
        
        if in_table and not line.startswith('|'):
            result['tables'].append('\n'.join(table_rows))
            in_table = False
            table_rows = []
        
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            result['headings'].append({'level': level, 'text': text})
            continue
        
        list_match = re.match(r'^(\s*[-*+])\s+(.+)', line)
        if list_match:
            current_list.append(list_match.group(2))
            continue
        
        if current_list and not line.strip().startswith(('-', '*', '+')):
            result['lists'].append(current_list)
            current_list = []
        
        if line.strip() and not line.startswith('#') and not line.startswith(('-', '*', '+')):
            result['paragraphs'].append(line.strip())
    
    if current_list:
        result['lists'].append(current_list)
    
    if in_table and table_rows:
        result['tables'].append('\n'.join(table_rows))
    
    return result

def extract_text(content: str) -> str:
    content = re.sub(r'```[\s\S]*?```', '', content)
    content = re.sub(r'`([^`]+)`', r'\1', content)
    content = re.sub(r'#{1,6}\s+', '', content)
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    content = re.sub(r'__([^_]+)__', r'\1', content)
    content = re.sub(r'_([^_]+)_', r'\1', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    content = re.sub(r'\|', ' ', content)
    content = re.sub(r'\s+', ' ', content)
    return content.strip()

def split_into_chunks(content: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        para_length = len(paragraph)
        
        if current_length + para_length <= chunk_size:
            current_chunk.append(paragraph)
            current_length += para_length
        else:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            if para_length > chunk_size:
                sub_chunks = [paragraph[i:i+chunk_size] for i in range(0, len(paragraph), chunk_size - chunk_overlap)]
                chunks.extend(sub_chunks)
                current_chunk = []
                current_length = 0
            else:
                current_chunk = [paragraph]
                current_length = para_length
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks