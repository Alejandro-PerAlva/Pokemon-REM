#!/usr/bin/env python3
"""Compila PokemonREM_Codex.apk (WebView + Pyodide). Uso: python3 tools/mobile/build_apk.py [salida.apk]"""
import json, os, re, shutil, struct, subprocess, sys, time, zlib, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
M = os.path.join(ROOT, 'tools', 'mobile')
SDK = os.path.expanduser('~/Library/Android/sdk'); BT = os.path.join(SDK, 'build-tools', '34.0.0')
AJAR = os.path.join(SDK, 'platforms', 'android-34', 'android.jar')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'releases', 'apk', 'PokemonREM_Codex.apk')
ST = os.environ.get('REM_STAGE') or os.path.join(M, 'stage')
sys.path.insert(0, ROOT); sys.path.insert(0, M)
os.environ['JAVA_HOME']='/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home'; os.environ['PATH']=os.environ['JAVA_HOME']+'/bin:'+os.environ['PATH']
def sh(*a, **k): subprocess.run(a, check=True, **k)
def rd(p): return open(p, encoding='utf-8').read()
def wr(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(t)
def sub(t, old, new, n=1):
    assert t.count(old) == n, (old[:60], t.count(old)); return t.replace(old, new)

remote = subprocess.check_output(['git', '-C', ROOT, 'remote', 'get-url', 'origin']).decode().strip()
m = re.search(r'[:/]([^/:]+)/([^/]+?)(?:\.git)?$', remote); owner, repo = m.group(1), m.group(2)
branch = subprocess.check_output(['git', '-C', ROOT, 'branch', '--show-current']).decode().strip() or 'main'
vc = int(time.time() // 60)
shutil.rmtree(ST, ignore_errors=True)
A = os.path.join(ST, 'assets'); W = os.path.join(A, 'www')
wr(os.path.join(A, 'config.json'), json.dumps({'owner': owner, 'repo': repo, 'branch': branch, 'versionCode': vc}))

# ---- front: copia y parches
APP = os.path.join(ROOT, 'pokedex_app')
for d in ('css', 'js'): shutil.copytree(os.path.join(APP, d), os.path.join(W, 'app', d))
for f in ('view_progression.js', 'view_characters.js', 'view_story.js', 'selftest.js'): os.remove(os.path.join(W, 'app', 'js', f))
shutil.copy(os.path.join(M, 'mobile.js'), os.path.join(W, 'app', 'js', 'mobile.js'))
shutil.copy(os.path.join(M, 'pbs_update.js'), os.path.join(W, 'app', 'js', 'pbs_update.js'))
shutil.copy(os.path.join(M, 'mobile.css'), os.path.join(W, 'app', 'css', 'mobile.css'))
html = rd(os.path.join(APP, 'index.html'))
for f in ('view_progression', 'view_characters', 'view_story', 'selftest'):
    html = sub(html, '<script src="/app/js/%s.js"></script>\n' % f, '')
html = sub(html, '</body>', '<script src="/app/js/pbs_update.js"></script>\n<script src="/app/js/mobile.js"></script>\n</body>')
html = sub(html, '<link rel="stylesheet" href="/app/css/world.css">', '<link rel="stylesheet" href="/app/css/world.css">\n<link rel="stylesheet" href="/app/css/mobile.css">')
html = sub(html, 'content="width=device-width,initial-scale=1"', 'content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"')
html = sub(html, 'Pokémon REM Master Codex</title>', 'Pokémon REM Codex</title>')
wr(os.path.join(W, 'index.html'), html)
J = lambda n: os.path.join(W, 'app', 'js', n)
t = rd(J('ui.js'))
t = sub(t, ", 'shops', 'missions'],", ", 'shops'],")
t = sub(t, ", { label: 'Misiones de Pía', href: '#/missions', match: ['missions'] }", '')
t = re.sub(r"\n    \{ id: 'progression'.*?\n  \];", "\n  ];", t, count=1, flags=re.S)
wr(J('ui.js'), t)
t = rd(J('view_home.js'))
t = ''.join(l for l in t.splitlines(True) if "href: '#/progression'" not in l and "href: '#/characters'" not in l)
t = sub(t, ' y las misiones de Pía.', '.')
t = sub(t, "['Pasos de progresión', c.steps, '#/progression'], ['Capítulos', c.chapters, '#/story'],\n", '')
t = sub(t, "['Personajes', c.characters, '#/characters'], ['Tiendas', c.shops, '#/shops'], ['Misiones de Pía', c.missions, '#/missions']", "['Tiendas', c.shops, '#/shops']")
wr(J('view_home.js'), t)
t = rd(J('view_atlas.js'))
for lab in ('Eventos principales', 'Jefe y combates clave', 'Personajes presentes', 'Capítulos de las Crónicas ambientados aquí'):
    t = sub(t, "add('%s'" % lab, "0 && add('%s'" % lab)
wr(J('view_atlas.js'), t)
for fn in ('view_atlas.js', 'view_map.js', 'view_pokedex.js'):
    t = rd(J(fn))
    t = re.sub(r"^[ \t]*\{ key: 'note', label: 'Nota( táctica)?'.*$\n", '', t, flags=re.M)
    if fn != 'view_pokedex.js':
        for a, b in (("'Acto '", "'Zona '"), ("' Acto '", "' Zona '"), ("', acto '", "', zona '"), ("' · Acto '", "' · Zona '"), ("'Acto'", "'Zona'"), ("por acto", "por zona"), ("' Acto ' +", "' Zona ' +")):
            t = t.replace(a, b)
        t = t.replace(" (primera visita)'", "'")
    wr(J(fn), t)
for fn in os.listdir(os.path.join(W, 'app', 'js')):
    p = J(fn); t = rd(p)
    o = t
    for a, b in (('Misiones de Pía', 'Misiones'), ('Misión de Pía', 'Entrega especial'), ('Recompensa de las misiones de captura de Pía', 'Entrega especial'),
                 ('Pía recompensa con objetos a quien captura cierto número de especies distintas. ', ''),
                 (", h('a', { class: 'btn', href: '#/progression' }, '🧭 Progresión')", ''), ("'Progresión n.º '", "'Orden n.º '")):
        t = t.replace(a, b)
    if t != o: wr(p, t)

# ---- modelo (PBS local, saneado) + Python para Pyodide
import mobile_entry
model = mobile_entry.build(os.path.join(ROOT, 'PBS'), os.path.join(M, 'assets.json'), ROOT)
wr(os.path.join(W, 'data', 'model.json'), json.dumps(model, ensure_ascii=False, separators=(',', ':')))
os.makedirs(os.path.join(W, 'map'))
shutil.copy(os.path.join(ROOT, 'docs', 'Mapa', 'Mapa_Final__Esqueleto.png'), os.path.join(W, 'map'))
for n in range(674, 718):
    p = os.path.join(ROOT, 'Graphics', 'Icons', 'item%03d.png' % n)
    if os.path.exists(p):
        os.makedirs(os.path.join(A, 'gfx_local', 'Icons'), exist_ok=True); shutil.copy(p, os.path.join(A, 'gfx_local', 'Icons'))

# ---- icono (pokéball simple)
def png(w, h, px):
    raw = b''.join(b'\x00' + bytes(sum((px(x, y) for x in range(w)), ())) for y in range(h))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b'')
def ball(x, y, s=192):
    c = s / 2; dx, dy = x - c + .5, y - c + .5; r = (dx * dx + dy * dy) ** .5
    if r > c - 4: return (0, 0, 0, 0)
    if r > c - 14 or abs(dy) < 7 or r < 24 and r > 14: return (22, 26, 35, 255)
    if r <= 14: return (244, 246, 251, 255)
    return (229, 72, 77, 255) if dy < 0 else (244, 246, 251, 255)
RES = os.path.join(ST, 'res'); os.makedirs(os.path.join(RES, 'mipmap-xxhdpi'))
open(os.path.join(RES, 'mipmap-xxhdpi', 'ic_launcher.png'), 'wb').write(png(192, 192, ball))
wr(os.path.join(ST, 'AndroidManifest.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="rem.codex" android:versionCode="%d" android:versionName="1.0">
  <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34"/>
  <uses-permission android:name="android.permission.INTERNET"/>
  <application android:label="Pokémon REM Codex" android:icon="@mipmap/ic_launcher" android:allowBackup="false" android:usesCleartextTraffic="false" android:hardwareAccelerated="true">
    <activity android:name=".MainActivity" android:exported="true" android:configChanges="orientation|screenSize|keyboardHidden|smallestScreenSize|screenLayout" android:theme="@android:style/Theme.DeviceDefault.NoActionBar">
      <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
    </activity>
  </application>
</manifest>''' % vc)

# ---- compilación
CL = os.path.join(ST, 'classes'); os.makedirs(CL)
sh(os.path.expanduser('~/.sdkman/candidates/java/8.0.362-zulu/bin/javac'), '-g', '-source', '8', '-target', '8', '-nowarn', '-bootclasspath', AJAR, '-d', CL, os.path.join(M, 'java', 'rem', 'codex', 'MainActivity.java'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cls = glob.glob(CL + '/rem/codex/*.class')
sh(os.path.join(BT, 'd8'), '--lib', AJAR, '--min-api', '24', '--output', ST, *cls)
sh(os.path.join(BT, 'aapt2'), 'compile', '--dir', RES, '-o', os.path.join(ST, 'res.zip'))
unsigned = os.path.join(ST, 'unsigned.apk')
sh(os.path.join(BT, 'aapt2'), 'link', '-o', unsigned, '-I', AJAR, '--manifest', os.path.join(ST, 'AndroidManifest.xml'), '-A', A, os.path.join(ST, 'res.zip'), '--min-sdk-version', '24', '--target-sdk-version', '34')
import zipfile
with zipfile.ZipFile(unsigned, 'a', zipfile.ZIP_DEFLATED) as z: z.write(os.path.join(ST, 'classes.dex'), 'classes.dex')
aligned = os.path.join(ST, 'aligned.apk')
sh(os.path.join(BT, 'zipalign'), '-f', '-p', '4', unsigned, aligned)
ks = os.path.join(M, 'cache', 'debug.keystore')
if not os.path.exists(ks):
    sh('keytool', '-genkeypair', '-keystore', ks, '-storepass', 'android', '-keypass', 'android', '-alias', 'rem', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-dname', 'CN=PokemonREM', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sh(os.path.join(BT, 'apksigner'), 'sign', '--ks', ks, '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', OUT, aligned)
print('APK', OUT, round(os.path.getsize(OUT) / 1e6, 1), 'MB', owner + '/' + repo, branch)
