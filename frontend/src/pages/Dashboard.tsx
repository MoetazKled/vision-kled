import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export function Dashboard() {
  const [stats, setStats] = useState<Record<string, number>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.stats().then(setStats).catch((err: Error) => setError(err.message));
  }, []);

  async function startTrial() {
    setBusy(true);
    try {
      const lead = await api.trialLead();
      navigate(`/leads/${lead.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر بدء التجربة");
    } finally {
      setBusy(false);
    }
  }

  const cards = [
    { key: "leads", label: "عملاء" },
    { key: "demos", label: "مواقع ديمو" },
    { key: "subscriptions", label: "اشتراكات" },
    { key: "opted_out", label: "إيقاف تواصل" },
  ];

  return (
    <>
      <section className="hero">
        <div className="hero-main">
          <h1>ابنِ الديمو، ثم أغلق الصفقة من المحادثة</h1>
          <p className="lede">
            هذه لوحة Moetez Khaled. اضغط الزر لفتح محادثة تجريبية مع عميل جاهز،
            أو أضف عميلاً من الصفحة التالية.
          </p>
          <div className="hero-actions">
            <button className="btn accent" onClick={() => void startTrial()} disabled={busy}>
              ابدأ تجربة كاملة
            </button>
            <Link className="btn ghost" to="/leads" style={{ color: "#f4efe6", borderColor: "#f4efe6" }}>
              أضف عميلاً بنفسك
            </Link>
          </div>
        </div>
        <div className="steps">
          <div className="step">
            <b>1</b>
            <div>أضف اسماً ورقماً، أو استخدم التجربة الجاهزة</div>
          </div>
          <div className="step">
            <b>2</b>
            <div>رد في المحادثة كأنك العميل على واتساب</div>
          </div>
          <div className="step">
            <b>3</b>
            <div>شاهد موقع الديمو ثم سجّل الاشتراك يدوياً</div>
          </div>
        </div>
      </section>
      {error && <div className="error">{error}</div>}
      <div className="grid">
        {cards.map((card) => (
          <div className="stat" key={card.key}>
            <div className="n">{stats[card.key] ?? 0}</div>
            <div className="l">{card.label}</div>
          </div>
        ))}
      </div>
    </>
  );
}
