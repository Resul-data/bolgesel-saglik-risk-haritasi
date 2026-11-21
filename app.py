"""ABD eyalet düzeyinde bölgesel sağlık ve çevre göstergeleri."""
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

from eyalet_verisi import EYALET_KODU, EYALET_MERKEZ

app = Flask(__name__)

VERI_YOLU = Path(__file__).parent / "data" / "uc_katmanli_eyalet_verisi.csv"
DF = pd.read_csv(VERI_YOLU)
DF["kod"] = DF["eyalet"].map(EYALET_KODU)
DF["lat"] = DF["eyalet"].map(lambda e: EYALET_MERKEZ[e][0])
DF["lon"] = DF["eyalet"].map(lambda e: EYALET_MERKEZ[e][1])

EYALET_ORT = {
    "ilac": DF["tansiyon_ilaci_kullanim_yuzde_yas_standart"].mean(),
    "olum": DF["kalp_hastaligi_olum_hizi_100bin_2023"].mean(),
    "pm25": DF["pm25_2023_ugm3"].mean(),
}


@app.route("/")
def anasayfa():
    return render_template("index.html")


@app.route("/harita_verisi")
def harita_verisi():
    """Scattermapbox trace'ini (open-street-map tabanı, API key gerektirmez) elle
    kurar — sunucu tarafında plotly paketine ihtiyaç duymaz, Plotly.js CDN'den
    frontend'de yüklenir."""
    hover_metni = DF.apply(
        lambda r: (f"<b>{r['eyalet']}</b><br>"
                   f"Hipertansiyonu olanlarda ilaç kullanımı: %{r['tansiyon_ilaci_kullanim_yuzde_yas_standart']}<br>"
                   f"Kalp hast. ölüm hızı: {r['kalp_hastaligi_olum_hizi_100bin_2023']}/100bin<br>"
                   f"PM2.5: {r['pm25_2023_ugm3']} µg/m³"),
        axis=1,
    ).tolist()

    trace = {
        "type": "scattermapbox",
        "lat": DF["lat"].tolist(),
        "lon": DF["lon"].tolist(),
        "mode": "markers",
        "marker": {
            "size": (DF["tansiyon_ilaci_kullanim_yuzde_yas_standart"] * 1.3).tolist(),
            "color": DF["kalp_hastaligi_olum_hizi_100bin_2023"].tolist(),
            "colorscale": "Reds",
            "showscale": True,
            "colorbar": {"title": "Kalp hast.\nölüm hızı"},
            "sizemode": "diameter",
        },
        "text": hover_metni,
        "hoverinfo": "text",
    }
    layout = {
        "mapbox": {
            "style": "open-street-map",
            "center": {"lat": 39.5, "lon": -98.5},
            "zoom": 3.2,
        },
        "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
        "height": 550,
    }

    return jsonify({
        "data": [trace],
        "layout": layout,
        "eyaletler": sorted(DF["eyalet"].tolist()),
    })


@app.route("/risk_hesapla", methods=["POST"])
def risk_hesapla():
    eyalet = request.form.get("eyalet")
    satir = DF[DF["eyalet"] == eyalet]
    if satir.empty:
        return jsonify({"hata": "Eyalet bulunamadı"}), 400
    s = satir.iloc[0]

    pm25_fark = s["pm25_2023_ugm3"] - EYALET_ORT["pm25"]
    if pm25_fark > 1:
        yorum = "Bu eyalette hava kirliliği eyalet ortalamasının belirgin üzerinde."
    elif pm25_fark < -1:
        yorum = "Bu eyalette hava kirliliği eyalet ortalamasının belirgin altında."
    else:
        yorum = "Bu eyaletin hava kirliliği eyalet ortalamasına yakın."

    return jsonify({
        "ilac": round(s["tansiyon_ilaci_kullanim_yuzde_yas_standart"], 1),
        "ilac_ort": round(EYALET_ORT["ilac"], 1),
        "olum": round(s["kalp_hastaligi_olum_hizi_100bin_2023"], 1),
        "olum_ort": round(EYALET_ORT["olum"], 1),
        "pm25": round(s["pm25_2023_ugm3"], 1),
        "pm25_ort": round(EYALET_ORT["pm25"], 1),
        "yorum": yorum,
        "uyari": "Bu sizin kişisel sağlık riskiniz DEĞİLDİR — yaşadığınız eyaletin popülasyon düzeyinde gözlenen istatistikleridir. Tıbbi tavsiye yerine geçmez.",
    })


if __name__ == "__main__":
    app.run(port=5001)
