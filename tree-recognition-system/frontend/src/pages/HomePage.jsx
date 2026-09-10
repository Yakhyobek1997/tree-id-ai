import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BarChart3, Camera, Check, HeartHandshake, Leaf, MapPin, ScanLine, ShieldCheck, Sprout, Trees, Users } from 'lucide-react';
import heroImage from '../assets/forest-hero.png';

const features = [
  [ScanLine, 'AI orqali tanish', 'Rasm yoki kamera orqali daraxt turini aniqlang'],
  [BarChart3, "O‘sishni kuzatish", "Vaqt o‘tishi bilan o‘zgarishlarni tahlil qiling"],
  [Leaf, 'Salomatlik tahlili', 'Daraxt holati va ehtimoliy kasalliklarni aniqlang'],
  [Users, 'Jamiyatga hissa', 'Daraxtlarni saqlashda faol ishtirok eting'],
];
const species = [
  ['Sharq chinori', 'Platanus orientalis', '#315f25,#a8c56c'], ['Qayin', 'Betula pendula', '#90b54c,#e6e5b3'],
  ["Qora qarag‘ay", 'Pinus nigra', '#183e2b,#7e9b60'], ['Likvidambar', 'Liquidambar styraciflua', '#7b2418,#e5a34f'],
  ['Zaytun', 'Olea europaea', '#576b3b,#bac29e'], ['Terak', 'Populus', '#316c3a,#b5db74'],
];

function HomePage() {
  return <div className="home-page">
    <section className="hero-section" style={{backgroundImage:`url(${heroImage})`}}><div className="hero-overlay"/><div className="home-shell hero-content">
      <p className="eyebrow">Tabiatni himoya qilish — barchamizning mas’uliyatimiz</p><h1>Daraxtlarni <span>asrab qolaylik</span></h1>
      <p className="hero-copy">AI yordamida daraxtlarni taniymiz, kuzatamiz va kelajak avlod uchun asraymiz.</p>
      <div className="hero-benefits"><span><ScanLine/> Aniq tanish</span><span><ShieldCheck/> Ishonchli tahlil</span><span><Leaf/> Tabiat uchun</span></div>
      <div className="hero-actions"><Link className="primary-action" to="/scan"><Camera/> Hozir daraxtni tanish <ArrowRight/></Link><Link className="secondary-action" to="/stats"><BarChart3/> Statistikani ko‘rish</Link></div>
    </div></section>
    <main className="home-shell home-main">
      <section className="feature-grid">{features.map(([Icon,title,text])=><article className="feature-card" key={title}><div className="icon-box"><Icon/></div><h3>{title}</h3><p>{text}</p></article>)}</section>
      <section className="mission-grid"><div className="mission-photo" style={{backgroundImage:`url(${heroImage})`}}><div className="mission-caption"><Trees/><h2>Tabiatni asrash texnologiya bilan mumkin</h2><span>Platformamiz qanday ishlashini ko‘ring</span></div></div>
        <div className="mission-copy"><p className="eyebrow">Bizning maqsad</p><h2>Yashil dunyo — barqaror kelajak</h2><p>Har bir daraxt hayot manbai. Platformamiz sun’iy intellekt yordamida daraxtlarni tanish, ularni kuzatish va tabiatni asrashga hissa qo‘shish imkonini beradi.</p><Link to="/scan">Batafsil ma’lumot <ArrowRight/></Link></div>
        <div className="stats-panel">{[[Trees,'50,000+','Aniqlangan daraxtlar'],[Users,'10,000+','Faol foydalanuvchilar'],[MapPin,'100+','Daraxt turlari'],[Leaf,'25+','Shahar va hududlar']].map(([Icon,n,l])=><div key={l}><Icon/><strong>{n}</strong><span>{l}</span></div>)}</div></section>
      <section className="species-section"><div className="section-heading"><div><h2>Mashhur daraxt turlari</h2><p>Bizning platformada eng ko‘p aniqlanadigan daraxtlar</p></div><Link to="/trees">Barcha turlarni ko‘rish <ArrowRight/></Link></div><div className="species-grid">{species.map(([name,latin,tone])=><article className="species-card" key={name}><div className="species-image" style={{background:`linear-gradient(145deg,${tone})`}}><Trees/></div><div><strong>{name}</strong><span>{latin}</span></div><Link to="/trees" aria-label={`${name} haqida`}><ArrowRight/></Link></article>)}</div></section>
      <section className="steps-section"><div className="section-heading"><div><p className="eyebrow">Qanday ishlaydi?</p><h2>Uch qadamda daraxtni taning</h2></div></div><div className="steps-grid">{[['01',Camera,'Rasm oling','Daraxtni suratga oling yoki galereyadan tanlang'],['02',ScanLine,'AI tahlil qiladi','Sun’iy intellekt daraxt turi va holatini tahlil qiladi'],['03',Check,'Natijani oling','Daraxt haqida to‘liq ma’lumot va tavsiyalarni ko‘ring']].map(([n,Icon,t,x])=><article key={n}><span>{n}</span><div className="icon-box"><Icon/></div><h3>{t}</h3><p>{x}</p></article>)}</div></section>
    </main>
    <section className="bottom-cta" style={{backgroundImage:`url(${heroImage})`}}><div><p>Kelajak bizning qo‘limizda</p><h2>Ko‘proq daraxt — tozaroq havo — yaxshiroq hayot</h2><Link className="primary-action" to="/scan">Hozir boshlash <ArrowRight/></Link></div></section>
    <footer><div className="home-shell"><div className="footer-brand"><Sprout/><div><strong>Daraxtlarni asrab qolaylik</strong><span>Yashil kelajak uchun birga</span></div></div><p>© 2026 Tree Recognition. Tabiatni birga asraymiz <HeartHandshake/></p></div></footer>
  </div>;
}
export default HomePage;
