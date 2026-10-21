# ==============================================================================
# IMPORTACIÓN DE LIBRERÍAS (Nativas + Playwright)
# ==============================================================================
import csv   # Librería nativa para generar archivos tabulares (.csv)
import json  # Librería nativa para convertir texto JSON en diccionarios de Python
import sys   # Librería nativa para leer el usuario que escribas en la terminal
import time  # Librería nativa para manejo de tiempos (timestamps)
from playwright.sync_api import sync_playwright, Response


def extraer_datos_tiktok(username: str, max_videos: int = 10) -> dict:
    """
    Abre el perfil de TikTok, extrae los metadatos del usuario desde el JSON de
    hidratación e intercepta las peticiones de red para capturar los últimos videos.
    """
    username_limpio = username.lstrip("@")
    url = f"https://www.tiktok.com/@{username_limpio}"
    
    datos_perfil = {}
    videos_extraidos = []
    ids_procesados = set()

    # ==========================================================================
    # 1. INTERCEPTOR DE RED (Espía asíncrono en segundo plano)
    # ==========================================================================
    def interceptar_red(response: Response):
        if "/api/post/item_list/" in response.url and response.status == 200:
            try:
                cuerpo_json = response.json()
                lista_items = cuerpo_json.get("itemList", [])
                
                for item in lista_items:
                    video_id = item.get("id")
                    
                    if video_id and video_id not in ids_procesados and len(videos_extraidos) < max_videos:
                        ids_procesados.add(video_id)
                        stats = item.get("stats", {})
                        
                        videos_extraidos.append({
                            "video_id": video_id,
                            "fecha_timestamp": item.get("createTime"),
                            "likes": stats.get("diggCount", 0),
                            "comentarios": stats.get("commentCount", 0),
                            "compartidos": stats.get("shareCount", 0)
                        })
            except Exception as e:
                print(f"[Aviso] Error al parsear respuesta XHR: {e}")

    # ==========================================================================
    # 2. INICIALIZACIÓN Y CONFIGURACIÓN DEL NAVEGADOR (Playwright)
    # ==========================================================================
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            locale="es-ES"
        )
        
        page = context.new_page()

        # Suscribimos el interceptor de red antes de abrir la página
        page.on("response", interceptar_red)

        print(f"[*] Navegando al perfil: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Esperamos a que el nombre de usuario sea visible en pantalla para confirmar
        # visualmente que sí entró al perfil antes de continuar
        try:
            page.wait_for_selector('[data-e2e="user-title"]', state="visible", timeout=15000)
        except Exception:
            print("[!] La interfaz visual tardó en renderizar, verificando datos internos...")

        # ======================================================================
        # 3. EXTRACCIÓN DEL BLOQUE JSON DE HIDRATACIÓN (Datos del Perfil)
        # ======================================================================
        selector_hidratacion = "script#__UNIVERSAL_DATA_FOR_REHYDRATION__"
        page.wait_for_selector(selector_hidratacion, state="attached", timeout=15000)
        
        contenido_script = page.locator(selector_hidratacion).text_content()
        
        if contenido_script:
            estado_inicial = json.loads(contenido_script)
            
            scope_defecto = estado_inicial.get("__DEFAULT_SCOPE__", {})
            detalle_usuario = scope_defecto.get("webapp.user-detail", {})
            user_info = detalle_usuario.get("userInfo", {})
            
            user_data = user_info.get("user", {})
            stats_data = user_info.get("stats", {})

            datos_perfil = {
                "username": user_data.get("uniqueId", username_limpio),
                "nombre": user_data.get("nickname", ""),
                "biografia": user_data.get("signature", "").replace("\n", " "),
                "seguidores": stats_data.get("followerCount", 0),
                "total_publicaciones": stats_data.get("videoCount", 0)
            }
            
            print(
                f"[+] Perfil cargado: {datos_perfil['nombre']} (@{datos_perfil['username']}) | "
                f"Seguidores: {datos_perfil['seguidores']} | Publicaciones: {datos_perfil['total_publicaciones']}"
            )
            
            # Respaldo por si el HTML inicial ya trae videos inyectados
            items_hidratacion = detalle_usuario.get("itemList", [])
            for item in items_hidratacion:
                if isinstance(item, dict):
                    v_id = item.get("id")
                    if v_id and v_id not in ids_procesados and len(videos_extraidos) < max_videos:
                        ids_procesados.add(v_id)
                        st = item.get("stats", {})
                        videos_extraidos.append({
                            "video_id": v_id,
                            "fecha_timestamp": item.get("createTime"),
                            "likes": st.get("diggCount", 0),
                            "comentarios": st.get("commentCount", 0),
                            "compartidos": st.get("shareCount", 0)
                        })

        # ======================================================================
        # 4. SCROLL ACTIVO Y ESPERA PARA COMPLETAR LAS 10 PUBLICACIONES
        # ======================================================================
        total_disponibles = datos_perfil.get("total_publicaciones", max_videos)
        objetivo_videos = min(max_videos, total_disponibles) if total_disponibles > 0 else max_videos

        intentos_scroll = 0
        while len(videos_extraidos) < objetivo_videos and intentos_scroll < 6:
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(2500)
            intentos_scroll += 1
            print(f"[*] Publicaciones capturadas hasta ahora: {len(videos_extraidos)}/{objetivo_videos}")

        print(f"[*] Total final de publicaciones capturadas: {len(videos_extraidos)}/{objetivo_videos}")
        
        # Pausa de 3 segundos antes de cerrar para que puedas ver el perfil abierto en el navegador
        page.wait_for_timeout(3000)
        browser.close()

    return {
        "perfil": datos_perfil,
        "ultimas_publicaciones": videos_extraidos[:max_videos]
    }


def exportar_resultados(datos: dict, prefijo_archivo: str):
    """
    Toma el diccionario final y genera dos archivos locales:
    1. Un archivo JSON jerárquico.
    2. Un archivo CSV plano ideal para Excel o Pandas.
    """
    # 1. EXPORTACIÓN A JSON
    archivo_json = f"{prefijo_archivo}_datos.json"
    with open(archivo_json, mode="w", encoding="utf-8") as f_json:
        json.dump(datos, f_json, ensure_ascii=False, indent=4)
    print(f"[+] Archivo JSON generado: {archivo_json}")

    # 2. EXPORTACIÓN A CSV (Tabla Desnormalizada)
    archivo_csv = f"{prefijo_archivo}_publicaciones.csv"
    perfil = datos.get("perfil", {})
    publicaciones = datos.get("ultimas_publicaciones", [])

    columnas = [
        "username", "nombre", "biografia", "seguidores", "total_publicaciones",
        "video_id", "fecha_timestamp", "likes", "comentarios", "compartidos"
    ]

    with open(archivo_csv, mode="w", encoding="utf-8-sig", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=columnas)
        writer.writeheader()

        if not publicaciones:
            writer.writerow(perfil)
        else:
            for video in publicaciones:
                fila_combinada = {**perfil, **video}
                writer.writerow(fila_combinada)

    print(f"[+] Archivo CSV generado: {archivo_csv}")


# ==============================================================================
# PUNTO DE ENTRADA DEL SCRIPT (Lee el usuario desde PowerShell)
# ==============================================================================
if __name__ == "__main__":
    # Si pasas un usuario por consola (ej: python scraper_tiktok.py khaby.lame),
    # sys.argv[1] toma "khaby.lame". Si no pasas nada, usa "tiktok" por defecto.
    if len(sys.argv) > 1:
        USUARIO_OBJETIVO = sys.argv[1].lstrip("@")
    else:
        USUARIO_OBJETIVO = "tiktok"
    
    resultado = extraer_datos_tiktok(USUARIO_OBJETIVO, max_videos=10)
    exportar_resultados(resultado, prefijo_archivo=USUARIO_OBJETIVO)