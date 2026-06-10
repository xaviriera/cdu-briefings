#!/usr/bin/env python3
"""Genera los carteles-guía visuales (HTML -> PNG) de cada carpeta Drive CdU.
Reutiliza el estilo validado del cartel muestra. Render con Edge headless.
Trabajo en serie barato; no consume Opus."""
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
URL_GUIA = "xaviriera.github.io/cdu-briefings/sistema-carpetas"

TEMPLATE = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=JetBrains+Mono:wght@600&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--navy:#163D60;--ochre:#E29F34;--cream:#FDFBF7;--green:#2c7a3f;--red:#b23b3b;--line:#e6dfd2;}}
body{{font-family:'Montserrat',sans-serif;background:#cfd8e0;padding:40px;}}
.card{{width:760px;background:var(--cream);border-radius:22px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.22);margin:0 auto;}}
.top{{background:var(--navy);color:var(--cream);padding:30px 36px;display:flex;align-items:center;gap:22px;}}
.top .ico{{font-size:62px;line-height:1;}}
.top .t-txt h1{{font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--ochre);margin-bottom:4px;}}
.top .t-txt h2{{font-size:30px;font-weight:900;letter-spacing:-.5px;line-height:1.05;}}
.body{{padding:30px 36px 16px;}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:22px;}}
.box{{border-radius:14px;padding:18px 20px;}}
.box.yes{{background:#eaf5ee;border:2px solid var(--green);}}
.box.no{{background:#fbecec;border:2px solid var(--red);}}
.box .bh{{font-size:15px;font-weight:900;letter-spacing:.5px;margin-bottom:12px;display:flex;align-items:center;gap:8px;}}
.box.yes .bh{{color:var(--green);}}
.box.no .bh{{color:var(--red);}}
.box ul{{list-style:none;}}
.box li{{font-size:15px;font-weight:600;color:var(--navy);padding:5px 0 5px 26px;position:relative;line-height:1.35;}}
.box.yes li::before{{content:"\\2713";position:absolute;left:0;color:var(--green);font-weight:900;}}
.box.no li::before{{content:"\\2715";position:absolute;left:0;color:var(--red);font-weight:900;}}
.rows{{display:flex;flex-direction:column;gap:10px;}}
.row{{display:flex;align-items:center;gap:14px;background:#fff;border:1.5px solid var(--line);border-radius:12px;padding:13px 18px;}}
.row .lbl{{font-size:11px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:var(--ochre);min-width:92px;}}
.row .val{{font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:600;color:var(--navy);}}
.row .pill{{background:var(--navy);color:var(--cream);font-size:13px;font-weight:800;padding:5px 12px;border-radius:7px;}}
.foot{{background:var(--navy);color:#cdd9e3;padding:14px 36px;display:flex;justify-content:space-between;align-items:center;font-size:12px;}}
.foot b{{color:var(--ochre);}}
.foot .qr{{font-weight:700;color:var(--cream);}}
</style></head><body><div class="card">
<div class="top"><div class="ico">{ico}</div><div class="t-txt"><h1>{kicker}</h1><h2>{titulo}</h2></div></div>
<div class="body"><div class="cols">
<div class="box yes"><div class="bh">✅ AQUÍ VA</div><ul>{yes}</ul></div>
<div class="box no"><div class="bh">⛔ AQUÍ NO</div><ul>{no}</ul></div>
</div><div class="rows">
<div class="row"><span class="lbl">Se nombra</span><span class="val">{naming}</span><span class="val" style="font-size:12px;color:#9a9a9a;">{naming_ej}</span></div>
<div class="row"><span class="lbl">Trello</span>{trello}</div>
</div></div>
<div class="foot"><span>\U0001F4D6 Guía completa del sistema → <b>{url}</b></span><span class="qr">CdU DE 0 a ÉXITO</span></div>
</div></body></html>"""

CARTELES = [
    {"slug": "00_servicio_kit", "ico": "\U0001F9F0", "kicker": "Carpeta 00 · Drive CdU", "titulo": "KIT DEL SERVICIO",
     "yes": ["Plantillas de contrato F1 · F2 · F3", "Guiones de bienvenida y entrega", "Checklists internos del proceso"],
     "no": ["Ops reales de cliente → carpeta 01", "Documentos de empresa → carpeta 04"],
     "naming": "FASE_1 / FASE_2 / FASE_3 …", "naming_ej": "plantillería estable", "pill": None, "nota": "plantillería (sin tablero)"},
    {"slug": "01_operaciones_servicio", "ico": "\U0001F4CB", "kicker": "Carpeta 01 · Drive CdU", "titulo": "OPERACIONES DEL SERVICIO",
     "yes": ["Cliente que contrató y pagó la Fase 1", "Cada op en su fase: F1 · F2 · F3", "Las cerradas → FINALIZADAS"],
     "no": ["Ops de proveedor → carpeta 02", "Ops en obra/venta → carpeta 03", "Temas de empresa → carpeta 04"],
     "naming": "NNN_NombreCliente_Ciudad", "naming_ej": "p.ej. 001_Nombre_Ciudad", "pill": "OPERACIONES SERVICIO", "nota": "→ card en la lista de su fase"},
    {"slug": "02_operaciones_fuera_servicio", "ico": "\U0001F91D", "kicker": "Carpeta 02 · Drive CdU", "titulo": "OPERACIONES FUERA DEL SERVICIO",
     "yes": ["Ops que llegan de un proveedor", "En análisis · con comisión pactada", "Derivadas a INBRUTO o descartadas"],
     "no": ["Clientes del servicio → carpeta 01", "Ops que ya ejecutamos → carpeta 03"],
     "naming": "Ciudad_Identificador", "naming_ej": "p.ej. Aspe_AvdaJuanCarlos", "pill": "ANALISIS DE OPERACIONES", "nota": "→ 1 lista por op"},
    {"slug": "03_operaciones_iniciadas", "ico": "\U0001F3D7️", "kicker": "Carpeta 03 · Drive CdU", "titulo": "OPERACIONES INICIADAS",
     "yes": ["Ops en ejecución: obra o venta", "Desde servicio / desde fuera-servicio", "Las cerradas → FINALIZADAS"],
     "no": ["Ops aún en estudio → 01 o 02", "Plantillería → carpeta 00"],
     "naming": "NN_NombreOp", "naming_ej": "p.ej. 01_TorresCotillas", "pill": "Board propio por op", "nota": "clon de PLANTILLA"},
    {"slug": "04_empresa", "ico": "\U0001F3E2", "kicker": "Carpeta 04 · Drive CdU", "titulo": "EMPRESA",
     "yes": ["Sociedad, finanzas, fiscal", "Equipo y marketing", "Formación (NUTRICIÓN)"],
     "no": ["Operaciones → carpetas 01 / 02 / 03", "Normativa urbanística → carpeta 05"],
     "naming": "SOCIEDAD / FINANZAS / EQUIPO …", "naming_ej": "+ MARKETING + NUTRICIÓN", "pill": "TAREAS GENERALES EQUIPO", "nota": "→ lista por área"},
    {"slug": "05_normativa_ccaa", "ico": "\U0001F4D0", "kicker": "Carpeta 05 · Drive CdU", "titulo": "NORMATIVA CCAA",
     "yes": ["Requisitos urbanísticos por comunidad", "Doctrina por localidad (Elche, etc.)", "Referencia transversal a todas las ops"],
     "no": ["Docs de una op concreta → su carpeta", "Trámites de un expediente → la op"],
     "naming": "REQUISITOS_POR_LOCALIDADES", "naming_ej": "CV / CATALUNYA / MURCIA", "pill": "TAREAS GENERALES EQUIPO", "nota": "→ lista contactos urbanismo"},
    {"slug": "nutricion", "ico": "\U0001F393", "kicker": "04_EMPRESA · Drive CdU", "titulo": "NUTRICIÓN (FORMACIÓN)",
     "yes": ["Formación del equipo", "CCP · Grado IN · Level Up", "Organizada por áreas"],
     "no": ["Operaciones → carpetas 01/02/03", "Gestión de empresa → resto de 04"],
     "naming": "por área", "naming_ej": "CRECIMIENTO / FINANZAS / FISCALIDAD / INVERSION", "pill": None, "nota": "subcarpeta de 04_EMPRESA"},
]


def render(slug, html):
    html_path = HERE / f"{slug}.html"
    png_path = HERE / f"{slug}.png"
    html_path.write_text(html, encoding="utf-8")
    if png_path.exists():
        png_path.unlink()
    uri = "file:///" + str(html_path).replace("\\", "/").replace(" ", "%20")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=860,640",
                    f"--screenshot={png_path}", uri],
                   capture_output=True, timeout=60)
    return png_path.exists()


def main():
    ok = 0
    for c in CARTELES:
        yes = "".join(f"<li>{x}</li>" for x in c["yes"])
        no = "".join(f"<li>{x}</li>" for x in c["no"])
        if c["pill"]:
            trello = f'<span class="pill">{c["pill"]}</span><span class="val" style="font-size:13px;color:#6b6b6b;">{c["nota"]}</span>'
        else:
            trello = f'<span class="val" style="font-size:14px;color:#6b6b6b;">{c["nota"]}</span>'
        html = TEMPLATE.format(ico=c["ico"], kicker=c["kicker"], titulo=c["titulo"],
                               yes=yes, no=no, naming=c["naming"], naming_ej=c["naming_ej"],
                               trello=trello, url=URL_GUIA)
        if render(c["slug"], html):
            print(f"OK  {c['slug']}.png")
            ok += 1
        else:
            print(f"FALLO {c['slug']}")
    print(f"--- {ok}/{len(CARTELES)} carteles generados ---")


if __name__ == "__main__":
    sys.exit(main())
