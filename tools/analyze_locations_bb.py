import os

def analyze():
    with open('PBS/rem_locations.txt', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    locations = []
    current = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            if current:
                locations.append(current)
            current = {'key': line[1:-1]}
        elif '=' in line and current is not None:
            k, v = line.split('=', 1)
            current[k.strip()] = v.strip()
    if current:
        locations.append(current)

    print(f"Total locations: {len(locations)}")
    
    # List each location with Key, Name, Category, Act, and brief description
    for i, loc in enumerate(locations, 1):
        key = loc.get('key')
        name = loc.get('Name', '')
        cat = loc.get('Category', '')
        act = loc.get('Act', '')
        desc = loc.get('Description', '')[:80]
        boss = loc.get('BossInfo', '')
        print(f"{i:2d}. [{key}] {name} | Tipo: {cat} | Acto: {act} | Jefe: {boss[:30] if boss else 'None'}")

if __name__ == '__main__':
    analyze()
