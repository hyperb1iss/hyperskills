"""Normalize visible Claude stream events without copying hidden thinking."""
from pathlib import Path


def visible_content(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return []
    return [item for item in content if isinstance(item, dict) and item.get('type') == 'text']


def normalize(events, skills_root):
    actions, reads, loaded = [], {}, set()
    root = Path(skills_root).resolve()
    for event in events:
        if not isinstance(event, dict) or event.get('type') not in ('assistant', 'user'):
            continue
        message = event.get('message', {})
        if not isinstance(message, dict):
            continue
        content = message.get('content', [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get('type')
            if kind == 'text':
                actions.append({'type': 'text', 'role': event['type'], 'text': block.get('text', '')})
            elif kind == 'tool_use':
                action = {k: block[k] for k in ('type', 'id', 'name', 'input') if k in block}
                actions.append(action)
                tool_input = block.get('input', {})
                if block.get('name') == 'Read' and isinstance(tool_input, dict):
                    filename = tool_input.get('file_path')
                    if isinstance(filename, str):
                        try:
                            relative = Path(filename).resolve().relative_to(root)
                        except ValueError:
                            continue
                        if len(relative.parts) >= 2:
                            reads[block.get('id')] = relative.parts[0]
            elif kind == 'tool_result':
                actions.append({'type': kind, 'tool_use_id': block.get('tool_use_id'), 'is_error': block.get('is_error', False), 'content': visible_content(block.get('content'))})
                name = reads.get(block.get('tool_use_id'))
                if name and not block.get('is_error', False):
                    loaded.add(name)
    return {'actions': actions, 'skill_read_attempts': sorted(set(reads.values())), 'skills_read_successfully': sorted(loaded)}
