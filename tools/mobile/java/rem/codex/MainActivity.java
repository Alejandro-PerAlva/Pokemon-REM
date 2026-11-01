package rem.codex;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.webkit.*;
import java.io.*;
import java.net.*;
import java.util.*;

public class MainActivity extends Activity {
    static final String HOST = "appassets.local";
    WebView web;
    String owner, repo, branch;
    File files;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        files = getFilesDir();
        try {
            String c = new String(readAll(getAssets().open("config.json")), "UTF-8");
            owner = jget(c, "owner"); repo = jget(c, "repo"); branch = jget(c, "branch");
            int vc = Integer.parseInt(jget(c, "versionCode"));
            SharedPreferences sp = getSharedPreferences("rem", 0);
            if (sp.getInt("vc", 0) != vc) { new File(files, "model.json").delete(); sp.edit().putInt("vc", vc).commit(); }
        } catch (Exception e) { owner = "x"; repo = "x"; branch = "main"; }
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#161a23"));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false); s.setAllowContentAccess(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        web.addJavascriptInterface(new Bridge(), "AndroidBridge");
        web.setWebViewClient(new Client());
        web.loadUrl("https://" + HOST + "/");
    }

    @Override public void onBackPressed() { if (web.canGoBack()) web.goBack(); else super.onBackPressed(); }

    class Client extends WebViewClient {
        @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
            String host = r.getUrl().getHost();
            if (host == null || !HOST.equals(host)) return err(403, "forbidden");
            try { return handle(r.getUrl().getPath(), r.getUrl().getEncodedPath()); }
            catch (Exception e) { return err(500, String.valueOf(e)); }
        }
        @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
            String host = r.getUrl().getHost();
            return host == null || !HOST.equals(host);
        }
    }

    class Bridge {
        @JavascriptInterface public void saveModel(String json) {
            try { File t = new File(files, "model.tmp"); FileOutputStream o = new FileOutputStream(t); o.write(json.getBytes("UTF-8")); o.close(); t.renameTo(new File(files, "model.json")); } catch (Exception e) { }
        }
    }

    static String jget(String j, String k) {
        int i = j.indexOf("\"" + k + "\""); if (i < 0) return "";
        i = j.indexOf(':', i) + 1; while (j.charAt(i) == ' ' || j.charAt(i) == '"') i++;
        int e = i; while (e < j.length() && "\",}\n ".indexOf(j.charAt(e)) < 0) e++;
        return j.substring(i, e);
    }

    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream o = new ByteArrayOutputStream(); byte[] b = new byte[16384]; int n;
        while ((n = in.read(b)) > 0) o.write(b, 0, n); in.close(); return o.toByteArray();
    }

    WebResourceResponse err(int code, String msg) {
        return new WebResourceResponse("text/plain", "UTF-8", code, "Error", new HashMap<String, String>(), new ByteArrayInputStream(msg.getBytes()));
    }

    WebResourceResponse ok(String mime, InputStream in, boolean cache) {
        Map<String, String> h = new HashMap<String, String>();
        h.put("Cache-Control", cache ? "public, max-age=3600" : "no-store");
        return new WebResourceResponse(mime, mime.startsWith("text/") || mime.contains("json") || mime.contains("javascript") ? "UTF-8" : null, 200, "OK", h, in);
    }

    static String mime(String p) {
        String l = p.toLowerCase();
        if (l.endsWith(".html")) return "text/html"; if (l.endsWith(".js")) return "text/javascript";
        if (l.endsWith(".css")) return "text/css"; if (l.endsWith(".json")) return "application/json";
        if (l.endsWith(".png")) return "image/png"; if (l.endsWith(".wasm")) return "application/wasm";
        if (l.endsWith(".zip")) return "application/zip"; if (l.endsWith(".py")) return "text/plain";
        if (l.endsWith(".txt")) return "text/plain"; return "application/octet-stream";
    }

    WebResourceResponse handle(String path, String enc) throws Exception {
        if (path.equals("/") || path.equals("/index.html")) return asset("www/index.html", false);
        if (path.equals("/api/version")) return ok("application/json", new ByteArrayInputStream("{\"version\":\"mobile\"}".getBytes()), false);
        if (path.equals("/api/model") || path.equals("/api/bundle")) {
            File m = new File(files, "model.json");
            if (m.exists()) return ok("application/json", new FileInputStream(m), false);
            return asset("www/data/model.json", false);
        }
        if (path.equals("/api/reload")) return ok("application/json", new ByteArrayInputStream("{}".getBytes()), false);
        if (path.startsWith("/gfx/")) return gfx(path.substring(5));
        if (path.startsWith("/pbs/")) return pbs(path.substring(5));
        if (path.startsWith("/app/") || path.startsWith("/pyodide/") || path.startsWith("/py/") || path.startsWith("/map/") || path.startsWith("/data/"))
            return asset("www" + path, true);
        return err(404, "No encontrado");
    }

    WebResourceResponse asset(String p, boolean cache) {
        try { return ok(mime(p), getAssets().open(p), cache); } catch (IOException e) { return err(404, "No encontrado"); }
    }

    WebResourceResponse gfx(String rel) throws Exception {
        rel = URLDecoder.decode(rel, "UTF-8");
        if (rel.contains("..")) return err(400, "bad");
        File f = new File(files, "gfx/" + rel);
        if (f.exists()) return ok("image/png", new FileInputStream(f), true);
        try { return ok("image/png", getAssets().open("gfx_local/" + rel), true); } catch (IOException e) { }
        byte[] d = download("https://raw.githubusercontent.com/" + owner + "/" + repo + "/" + branch + "/Graphics/" + encPath(rel));
        if (d == null) return err(404, "sin gráfico");
        f.getParentFile().mkdirs(); FileOutputStream o = new FileOutputStream(f); o.write(d); o.close();
        return ok("image/png", new ByteArrayInputStream(d), true);
    }

    static String encPath(String p) throws Exception {
        String[] parts = p.split("/"); StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length; i++) { if (i > 0) sb.append('/'); sb.append(URLEncoder.encode(parts[i], "UTF-8").replace("+", "%20")); }
        return sb.toString();
    }

    static final String[] FALLBACK = {"abilities.txt","moves.txt","pokemon.txt","items.txt","tm.txt","berryplants.txt","encounters.txt","types.txt","townmap.txt","connections.txt","metadata.txt","rem_vanilla_baseline.txt","rem_changelog.txt","rem_locations.txt","rem_encounters.txt","rem_location_items.txt","rem_shops.txt"};

    WebResourceResponse pbs(String name) throws Exception {
        name = URLDecoder.decode(name, "UTF-8");
        if (name.equals("_list")) {
            StringBuilder sb = new StringBuilder("[");
            byte[] d = download("https://api.github.com/repos/" + owner + "/" + repo + "/contents/PBS?ref=" + branch);
            List<String> names = new ArrayList<String>();
            if (d != null) {
                java.util.regex.Matcher m = java.util.regex.Pattern.compile("\"name\"\\s*:\\s*\"([^\"]+\\.txt)\"").matcher(new String(d, "UTF-8"));
                while (m.find()) { String n = m.group(1); if (!n.startsWith("~") && !n.startsWith(".")) names.add(n); }
            }
            if (names.isEmpty()) names = Arrays.asList(FALLBACK);
            for (int i = 0; i < names.size(); i++) { if (i > 0) sb.append(','); sb.append('"').append(names.get(i)).append('"'); }
            return ok("application/json", new ByteArrayInputStream(sb.append(']').toString().getBytes("UTF-8")), false);
        }
        if (name.equals("_sha")) {
            byte[] d = download("https://api.github.com/repos/" + owner + "/" + repo + "/commits?sha=" + branch + "&path=PBS&per_page=1");
            String sha = "";
            if (d != null) { java.util.regex.Matcher m = java.util.regex.Pattern.compile("\"sha\"\\s*:\\s*\"([0-9a-f]{40})\"").matcher(new String(d, "UTF-8")); if (m.find()) sha = m.group(1); }
            return ok("application/json", new ByteArrayInputStream(("{\"sha\":\"" + sha + "\"}").getBytes()), false);
        }
        if (name.contains("..") || name.contains("/")) return err(400, "bad");
        File f = new File(files, "pbs/" + name);
        byte[] d = download("https://raw.githubusercontent.com/" + owner + "/" + repo + "/" + branch + "/PBS/" + encPath(name) + "?t=" + System.currentTimeMillis());
        if (d != null) { f.getParentFile().mkdirs(); FileOutputStream o = new FileOutputStream(f); o.write(d); o.close(); }
        else if (f.exists()) d = readAll(new FileInputStream(f));
        if (d == null) return err(404, "no disponible");
        return ok("text/plain", new ByteArrayInputStream(d), false);
    }

    byte[] download(String u) {
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
            c.setConnectTimeout(12000); c.setReadTimeout(30000);
            c.setRequestProperty("User-Agent", "PokemonREM-Codex"); c.setRequestProperty("Cache-Control", "no-cache");
            if (c.getResponseCode() != 200) return null;
            return readAll(c.getInputStream());
        } catch (Exception e) { return null; }
    }
}
