# Archivo maestro de preparacion para el test individual de Battleback
# Objetivo: 1 solo fondo de prueba al reiniciar cuota (20:26 local)
# Enfoque: Pixel Art puro estilo Nintendo DS (Gen 4/5), perspectiva diagonal de combate integrada, sin aros artificiales.

TEST_BATTLEBACK_01 = {
    "name": "bb_test_01_pradera_pokemon_style",
    "aspect_ratio": "4:3",
    "target_resolution": (512, 384),
    "reset_time_local": "20:26:06",
    "prompt": (
        "Authentic 2D pixel art battle background for a Pokemon Nintendo DS game "
        "(Pokemon HeartGold, SoulSilver, Black and White Gen 4 Gen 5 style). "
        "Classic handheld RPG 16-bit 32-bit pixel art, vibrant saturated anime colors, "
        "clean crisp pixel clusters, stylized outlines, limited color palette, "
        "absolutely NO 3D CGI renders, NO photo textures, NO blur. "
        "Dynamic Pokemon battle scene composition staged diagonally for two battlers: "
        "- In the bottom-left foreground (x=25%, y=80%): a wide, flat natural grassy clearing "
        "forming a firm, intuitive ground shelf for the player Pokemon in the foreground. "
        "- In the upper-right midground (x=75%, y=46%): a gentle elevated grassy knoll or "
        "natural mound smoothly rising as the intuitive stage for the opponent Pokemon. "
        "- Both battler standing areas are organic parts of the meadow landscape, naturally integrated "
        "with rolling green hills and small wildflowers, NO floating oval rings, NO artificial pedestals. "
        "- Background: Stylized round Pokemon-style leafy trees framing the scene, rolling green hills "
        "sloping diagonally, and a bright sunny sky with fluffy pixelated white clouds. "
        "Palette calibrated to Pokemon routes: bright lime meadow green (#aad07c) and fresh grass (#91a969)."
    )
}

if __name__ == "__main__":
    print("=== CONFIGURACION LISTA PARA EL TEST ===")
    print("Fondo:", TEST_BATTLEBACK_01["name"])
    print("Hora de reinicio de cuota:", TEST_BATTLEBACK_01["reset_time_local"])
    print("Resolución final:", TEST_BATTLEBACK_01["target_resolution"])
    print("\nPrompt preparado:\n", TEST_BATTLEBACK_01["prompt"])
