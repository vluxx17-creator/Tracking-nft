import re

def parse_price(text: str):
    match = re.search(r'(\d+)\s*(?:TON|ton|Stars|звезд|⭐)?', text)
    return int(match.group(1)) if match else None

def parse_link(text: str):
    match = re.search(r'(https?://t\.me/[^\s]+)', text)
    if match:
        return match.group(1)
    match2 = re.search(r'(t\.me/[^\s]+)', text)
    if match2:
        return "https://" + match2.group(1)
    return None

def extract_username(sender):
    if sender.username:
        return f"@{sender.username}"
    return f"{sender.first_name} ({sender.id})"
