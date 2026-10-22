import json
import sys
from sentence_transformers import SentenceTransformer, util


def analizar_perfil_con_embeddings(archivo_json: str):
    # 1. Cargar los datos extraídos previamente por el scraper
    with open(archivo_json, mode="r", encoding="utf-8") as f:
        datos = json.load(f)

    perfil = datos.get("perfil", {})
    videos = datos.get("ultimas_publicaciones", [])

    # Unimos nombre, biografía y descripciones de videos (si existen) para crear el corpus
    textos_videos = " ".join([v.get("descripcion", "") for v in videos if v.get("descripcion")])
    texto_creador = f"{perfil.get('nombre', '')}. {perfil.get('biografia', '')}. {textos_videos}".strip()

    # 2. Definir los Arquetipos de Contenido (Alternativa comercial al Big Five)
    arquetipos = {
        "Entretenimiento y Humor": "Funny videos, comedy sketches, memes, laughs, viral entertainment and jokes.",
        "Educación y Tecnología": "Tutorials, learning, coding, science, technology, tips and educational content.",
        "Estilo de Vida y Fitness": "Gym, workout, health, daily routine, lifestyle, travel, food and wellness.",
        "Negocios y Corporativo": "Official brand, business, marketing, announcements, products and company news.",
        "Comunidad y Tendencias": "New discoveries, trends, music, creators, challenges and global community."
    }

    # 3. Generar Embeddings con Hugging Face (Modelo ligero de 384 dimensiones)
    print("[*] Cargando modelo de Hugging Face (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    embedding_creador = model.encode(texto_creador, convert_to_tensor=True)
    nombres_arquetipos = list(arquetipos.keys())
    embeddings_arquetipos = model.encode(list(arquetipos.values()), convert_to_tensor=True)

    # Calcular Similitud del Coseno entre el perfil y cada arquetipo
    similitudes = util.cos_sim(embedding_creador, embeddings_arquetipos)[0]
    
    afinidades = {
        nombres_arquetipos[i]: round(float(similitudes[i]), 4)
        for i in range(len(nombres_arquetipos))
    }
    # Ordenar de mayor a menor afinidad semántica
    afinidades_ordenadas = dict(sorted(afinidades.items(), key=lambda x: x[1], reverse=True))
    arquetipo_dominante = next(iter(afinidades_ordenadas))

    # 4. Calcular Métricas Cuantitativas de las 10 publicaciones
    seguidores = max(perfil.get("seguidores", 1), 1)
    total_likes = sum(v.get("likes", 0) for v in videos)
    total_comentarios = sum(v.get("comentarios", 0) for v in videos)
    total_compartidos = sum(v.get("compartidos", 0) for v in videos)
    n_videos = max(len(videos), 1)

    promedio_likes = round(total_likes / n_videos, 2)
    promedio_comentarios = round(total_comentarios / n_videos, 2)
    promedio_compartidos = round(total_compartidos / n_videos, 2)

    # Engagement Rate por publicación sobre el total de seguidores (%)
    engagement_rate = round((( (total_likes + total_comentarios + total_compartidos) / n_videos ) / seguidores) * 100, 4)
    # Tasa de viralidad: cuántos compartidos hay por cada 100 likes
    ratio_viralidad = round((total_compartidos / max(total_likes, 1)) * 100, 2)

    reporte = {
        "username": perfil.get("username"),
        "texto_analizado": texto_creador,
        "arquetipo_dominante": arquetipo_dominante,
        "scores_embeddings_hf": afinidades_ordenadas,
        "metricas_engagement": {
            "promedio_likes": promedio_likes,
            "promedio_comentarios": promedio_comentarios,
            "promedio_compartidos": promedio_compartidos,
            "engagement_rate_porcentaje": engagement_rate,
            "ratio_viralidad_compartidos_vs_likes_porcentaje": ratio_viralidad
        }
    }

    archivo_salida = f"{perfil.get('username', 'perfil')}_analisis_hf.json"
    with open(archivo_salida, mode="w", encoding="utf-8") as f_out:
        json.dump(reporte, f_out, ensure_ascii=False, indent=4)

    print(f"\n[+] Arquetipo Principal: {arquetipo_dominante}")
    print(f"[+] Scores Semánticos (Cosine Similarity): {afinidades_ordenadas}")
    print(f"[+] Engagement Rate Promedio: {engagement_rate}% | Ratio de Viralidad: {ratio_viralidad}%")
    print(f"[+] Reporte guardado en: {archivo_salida}")


if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else "tiktok_datos.json"
    analizar_perfil_con_embeddings(archivo) 