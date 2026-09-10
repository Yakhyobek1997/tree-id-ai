import React, { useEffect, useRef, useState } from 'react';
import { Camera, Leaf, ShieldCheck, Ruler, Plus, X, Loader2, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyzeTree, getAnalysisCapabilities } from '../services/api';

const organOptions = [
  ['auto', 'Umumiy ko‘rinish / avtomatik'], ['leaf', 'Barg'], ['bark', 'Po‘stloq'],
  ['flower', 'Gul'], ['fruit', 'Meva'],
];
const statusLabels = {
  candidate: 'Model taklifi', uncertain: 'Noaniq', not_identified: 'Aniqlanmadi',
  unavailable: 'Xizmat mavjud emas', needs_configuration: 'AI hali ulanmagan',
  needs_consent: 'Rozilik kerak', needs_better_images: 'Yangi rasm kerak',
  completed: 'Tahlil yakunlandi', partial: 'Qisman tahlil',
};
const qualityLabels = { accepted: 'Yaxshi', warning: 'Yaxshilash mumkin', rejected: 'Qayta oling', duplicate: 'Takroriy' };

function PredictionCard({ title, icon: Icon, result }) {
  return (
    <section className="bg-white rounded-2xl border border-gray-200 p-6">
      <h3 className="flex items-center gap-2 font-semibold text-lg"><Icon className="w-5 h-5 text-green-700" />{title}</h3>
      <p className="text-sm text-gray-500 mt-2">{statusLabels[result.status] || result.status}</p>
      <p className="text-xl font-semibold mt-3 break-words">{result.label || 'Hozircha xulosa yo‘q'}</p>
      <p className="text-sm text-gray-600 mt-3">{result.message}</p>
      {result.candidates?.length > 0 && (
        <ol className="mt-4 space-y-3">
          {result.candidates.map((candidate, index) => (
            <li key={`${candidate.label}-${index}`} className="border-t border-gray-100 pt-3">
              <div className="flex justify-between gap-3 text-sm">
                <span className="break-words">{candidate.description || candidate.label}</span>
                <span className="font-mono whitespace-nowrap">{(candidate.score * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full mt-2" aria-hidden="true">
                <div className="h-full bg-green-600 rounded-full" style={{ width: `${candidate.score * 100}%` }} />
              </div>
            </li>
          ))}
        </ol>
      )}
      {result.model_score != null && <p className="text-xs text-gray-500 mt-4">Foizlar — model ballari. Ular platformaning sinovda o‘lchangan aniqligi emas.</p>}
      {result.model_version && <p className="text-xs text-gray-400 mt-3">Model versiyasi: {result.model_version}</p>}
    </section>
  );
}

export default function AnalysisPage() {
  const [views, setViews] = useState([]);
  const [capabilities, setCapabilities] = useState(null);
  const [connectionError, setConnectionError] = useState(false);
  const [context, setContext] = useState({ planted_date: '', dbh_cm: '', height_m: '' });
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState(null);
  const urls = useRef(new Set());

  useEffect(() => {
    let active = true;
    getAnalysisCapabilities().then((value) => { if (active) setCapabilities(value); })
      .catch(() => { if (active) setConnectionError(true); });
    return () => { active = false; urls.current.forEach((url) => URL.revokeObjectURL(url)); };
  }, []);

  const addImages = (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = '';
    setError('');
    if (files.length + views.length > 5) return setError('Bir daraxt uchun ko‘pi bilan 5 ta rasm tanlang.');
    if (files.some((file) => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024)) {
      return setError('JPEG, PNG yoki WebP tanlang. Har bir rasm 10 MB dan oshmasin.');
    }
    const added = files.map((file) => {
      const url = URL.createObjectURL(file);
      urls.current.add(url);
      return { file, url, organ: 'auto' };
    });
    setViews((previous) => [...previous, ...added]);
    setReport(null);
  };

  const removeImage = (index) => {
    URL.revokeObjectURL(views[index].url);
    urls.current.delete(views[index].url);
    setViews((previous) => previous.filter((_, i) => i !== index));
    setReport(null);
  };

  const scan = async (event) => {
    event.preventDefault();
    if (!views.length) return setError('Avval kamida bitta rasm tanlang.');
    setLoading(true);
    setError('');
    setReport(null);
    const data = new FormData();
    views.forEach((view) => { data.append('images', view.file); data.append('organs', view.organ); });
    Object.entries(context).forEach(([key, value]) => { if (value) data.append(key, value); });
    data.append('external_consent', String(consent));
    try {
      const response = await analyzeTree(data);
      setReport(response.report);
    } catch (err) {
      setError(err.response?.data?.message || 'Tahlilni olish imkoni bo‘lmadi. Server ulanishini tekshiring.');
    } finally {
      setLoading(false);
    }
  };

  const download = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `tree-analysis-${report.id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="max-w-5xl mx-auto text-gray-900">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <p className="text-green-700 font-semibold text-sm mb-2">TREE ID · DARAXT TAHLILI</p>
          <h1 className="text-3xl md:text-4xl font-bold">Daraxtingizni yaqindan o‘rganing</h1>
          <p className="text-gray-600 mt-3 max-w-2xl">Bitta daraxtning bargi, po‘stlog‘i va umumiy ko‘rinishini yuklang. Har bir natija mavjud dalillar bilan ko‘rsatiladi.</p>
        </div>
        <div className="bg-white border border-green-200 rounded-xl px-4 py-3 text-sm">
          <p className="font-semibold">Aniqlik maqsadi: 98%</p>
          <p className="text-gray-500 mt-1">Hozircha sinovda tasdiqlanmagan</p>
        </div>
      </div>

      {connectionError && <p role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5">Backend bilan aloqa yo‘q. Serverni ishga tushirib, sahifani yangilang.</p>}
      {capabilities && !capabilities.configured && (
        <p className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-4 mb-5">AI xizmati hali ulanmagan. Hozir rasm sifati va ekilgan sanadan o‘tgan vaqtni tekshirishingiz mumkin. Tur va kasallik tahlili xizmat sozlangach ishlaydi.</p>
      )}

      <form onSubmit={scan} className="bg-white border border-gray-200 rounded-2xl p-5 md:p-8 shadow-sm">
        <fieldset disabled={loading}>
          <legend className="text-xl font-semibold mb-2">1. Bir daraxt, bir nechta ko‘rinish</legend>
          <p className="text-sm text-gray-500 mb-5">1–5 ta rasm · JPEG / PNG / WebP · har biri 10 MB gacha. Yaxshi yoritilgan, fokusdagi suratlarni tanlang.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {views.map((view, index) => (
              <div key={view.url} className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="relative">
                  <img src={view.url} alt={`Daraxtning ${index + 1}-ko‘rinishi`} className="w-full h-44 object-cover" />
                  <button type="button" aria-label={`${index + 1}-rasmni olib tashlash`} onClick={() => removeImage(index)} className="absolute top-2 right-2 rounded-full p-2 bg-white shadow"><X className="w-4 h-4" /></button>
                </div>
                <label className="block p-3 text-sm">Rasmda nima ko‘rinadi?
                  <select value={view.organ} onChange={(event) => { setViews((previous) => previous.map((item, i) => i === index ? { ...item, organ: event.target.value } : item)); setReport(null); }} className="w-full mt-2 border border-gray-300 rounded-lg p-2 bg-white">
                    {organOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </label>
              </div>
            ))}
            {views.length < 5 && (
              <label className="min-h-[180px] flex flex-col items-center justify-center border-2 border-dashed border-green-300 bg-green-50 rounded-xl cursor-pointer p-5 focus-within:ring-2 focus-within:ring-green-600">
                <Plus className="w-7 h-7 text-green-700 mb-3" />
                <span className="font-semibold text-green-800">Rasm qo‘shish</span>
                <input type="file" multiple accept="image/jpeg,image/png,image/webp" onChange={addImages} className="sr-only" aria-label="Daraxt rasmlarini tanlash" />
              </label>
            )}
          </div>

          <h2 className="text-xl font-semibold mt-8 mb-2">2. Qo‘shimcha ma’lumotlar</h2>
          <p className="text-sm text-gray-500 mb-4">Ixtiyoriy. Yosh va keyingi o‘sish kuzatuvlari uchun o‘zingiz bilgan ma’lumotlarni kiriting.</p>
          <div className="grid sm:grid-cols-3 gap-4">
            <label className="text-sm">Ekilgan sana
              <input type="date" value={context.planted_date} onChange={(event) => { setContext({ ...context, planted_date: event.target.value }); setReport(null); }} className="block w-full border border-gray-300 rounded-lg p-3 mt-2" />
            </label>
            <label className="text-sm">Tana diametri (sm, 1,3 m balandlikda)
              <input type="number" min="0.1" max="2000" step="0.1" placeholder="Masalan, 24" value={context.dbh_cm} onChange={(event) => { setContext({ ...context, dbh_cm: event.target.value }); setReport(null); }} className="block w-full border border-gray-300 rounded-lg p-3 mt-2" />
            </label>
            <label className="text-sm">Daraxt balandligi (m)
              <input type="number" min="0.1" max="150" step="0.1" placeholder="Masalan, 8" value={context.height_m} onChange={(event) => { setContext({ ...context, height_m: event.target.value }); setReport(null); }} className="block w-full border border-gray-300 rounded-lg p-3 mt-2" />
            </label>
          </div>
          <label className="flex items-start gap-3 text-sm text-gray-600 mt-6">
            <input type="checkbox" checked={consent} onChange={(event) => { setConsent(event.target.checked); setReport(null); }} className="mt-1 shrink-0" />
            <span>Tur va kasallikni tahlil qilish uchun rasmlarni Pl@ntNet xizmatiga yuborishga roziman. Rasmlarning EXIF/GPS metama’lumotlari yuborilmaydi.</span>
          </label>
          <button type="submit" disabled={!views.length || loading} className="w-full mt-6 bg-green-700 text-white rounded-xl py-4 px-5 font-semibold hover:bg-green-800 disabled:opacity-50 flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Camera className="w-5 h-5" />}
            {loading ? 'Rasmlar tahlil qilinmoqda…' : 'Daraxtni tahlil qilish'}
          </button>
        </fieldset>
        {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}
      </form>

      <div aria-live="polite" aria-busy={loading}>
        {report && (
          <div className="mt-8 space-y-5">
            <div className="flex flex-wrap justify-between items-center gap-3">
              <h2 className="text-2xl font-semibold">{statusLabels[report.status] || report.status}</h2>
              <button type="button" onClick={download} className="flex items-center gap-2 border border-gray-300 bg-white rounded-lg px-4 py-2 text-sm"><Download className="w-4 h-4" />Hisobotni yuklash</button>
            </div>
            <div className="grid md:grid-cols-2 gap-5">
              <PredictionCard title="Daraxt turi" icon={Leaf} result={report.species} />
              <PredictionCard title="Kasallik ehtimollari" icon={ShieldCheck} result={report.health} />
            </div>
            <section className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="font-semibold text-lg flex items-center gap-2"><Ruler className="w-5 h-5 text-green-700" />Yosh va o‘lchovlar</h3>
              {report.age.years_since_planting != null && <p className="text-xl font-semibold mt-3">Ekilganidan beri {report.age.years_since_planting} yil</p>}
              <p className="text-sm text-gray-600 mt-3">{report.age.message}</p>
              <p className="text-sm text-gray-500 mt-2">Biologik yosh va rivojlanish bosqichi: aniqlanmagan.</p>
              {(report.age.measurements.dbh_cm || report.age.measurements.height_m) && <p className="text-sm mt-3">Siz kiritgan o‘lchovlar: diametr {report.age.measurements.dbh_cm ?? '—'} sm · balandlik {report.age.measurements.height_m ?? '—'} m.</p>}
            </section>
            <section className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="font-semibold text-lg mb-3">Rasmlar sifati · {report.images_used} ta foydalanish mumkin</h3>
              <ul className="space-y-3 text-sm">
                {report.quality.map((quality) => (
                  <li key={quality.view}>
                    <p className="font-medium">{quality.view}-rasm: {qualityLabels[quality.status]} · {quality.width} × {quality.height} px</p>
                    {quality.issues.map((issue) => <p key={issue} className="text-gray-600 mt-1">{issue}</p>)}
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-4">{report.external_processing ? 'Tahlil uchun rasmlar Pl@ntNet xizmatiga yuborildi.' : 'Rasmlar tashqi xizmatga yuborilmadi.'} Hisobot saqlandi.</p>
            </section>
            <p className="text-xs text-gray-500 break-all">Hisobot: {report.id} · {new Date(report.created_at).toLocaleString()}</p>
          </div>
        )}
      </div>
      <div className="flex flex-wrap justify-between gap-3 mt-6 text-sm text-gray-600">
        <Link to="/identify" className="underline">Avval ro‘yxatga olingan daraxtni qidirish</Link>
        <a href="https://plantnet.org/" target="_blank" rel="noreferrer" className="underline">AI integratsiyasi: Pl@ntNet</a>
      </div>
    </div>
  );
}
