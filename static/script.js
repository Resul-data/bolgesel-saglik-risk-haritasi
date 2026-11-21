fetch('/harita_verisi').then(r => r.json()).then(d => {
  const sel = document.getElementById('eyalet-select');
  d.eyaletler.forEach(e => {
    const opt = document.createElement('option');
    opt.value = e;
    opt.textContent = e;
    sel.appendChild(opt);
  });

  if (window.Plotly) {
    Plotly.newPlot('harita', d.data, d.layout, { responsive: true });
  } else {
    document.getElementById('harita').textContent = 'Harita için Plotly.js bağlantısı gerekiyor.';
  }
});

document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const res = await fetch('/risk_hesapla', { method: 'POST', body: fd });
  const d = await res.json();

  const sonucDiv = document.getElementById('sonuc');
  sonucDiv.style.display = 'block';
  if (!res.ok) {
    sonucDiv.textContent = d.hata;
    return;
  }
  sonucDiv.innerHTML = `
    <b>${fd.get('eyalet')} için popülasyon bağlamı:</b><br><br>
    💊 Hipertansiyonu olanlarda ilaç kullanımı: <b>%${d.ilac}</b> (eyalet ortalaması: %${d.ilac_ort})<br>
    ❤️ Kalp hastalığı ölüm hızı: <b>${d.olum}</b>/100bin (eyalet ortalaması: ${d.olum_ort})<br>
    🌫️ PM2.5 hava kirliliği: <b>${d.pm25} µg/m³</b> (eyalet ortalaması: ${d.pm25_ort} µg/m³)<br><br>
    <i>${d.yorum}</i>
    <div class="uyari" style="margin-top:12px;">${d.uyari}</div>
  `;
});
