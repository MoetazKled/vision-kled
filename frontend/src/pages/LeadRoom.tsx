import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Lead } from "../api";

type Message = { role: string; content: string };

const CHIPS = [
  "أيوا، عندي دقيقتين",
  "أنا محامي في تونس",
  "لا ما عنديش موقع",
  "الناس يلقوني من التوصيات",
  "نعم، حب نشوف النسخة",
];

export function LeadRoom() {
  const { id } = useParams();
  const leadId = Number(id);
  const [lead, setLead] = useState<Lead | null>(null);
  const [history, setHistory] = useState<Message[]>([]);
  const [phase, setPhase] = useState("");
  const [demoUrl, setDemoUrl] = useState<string | undefined>();
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  async function load() {
    const data = await api.lead(leadId);
    setLead(data.lead);
    setHistory(data.history);
    setPhase(data.phase);
    setDemoUrl(data.demos[0]?.url);
    if (data.history.length === 0) {
      const started = await api.start(leadId);
      setHistory(started.history);
    }
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [leadId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  async function sendText(text: string) {
    if (!text.trim()) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.chat(leadId, text.trim());
      setDraft("");
      setLead(result.lead);
      setPhase(result.phase);
      setDemoUrl(result.demo_url);
      const data = await api.lead(leadId);
      setHistory(data.history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل الإرسال");
    } finally {
      setBusy(false);
    }
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    await sendText(draft);
  }

  async function buildDemo() {
    setBusy(true);
    try {
      const result = await api.buildDemo(leadId);
      setDemoUrl(result.demo_url);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل بناء الديمو");
    } finally {
      setBusy(false);
    }
  }

  if (!lead) {
    return <p className="muted">{error || "جاري فتح المحادثة…"}</p>;
  }

  return (
    <>
      <p className="muted">
        <Link to="/leads">كل العملاء</Link>
      </p>
      <h1>{lead.name || "عميل جديد"}</h1>
      <p className="lede">
        {lead.phone} · {lead.product} · مرحلة {phase || lead.status}
      </p>
      {error && <div className="error">{error}</div>}
      <div className="room">
        <section className="chat">
          <div className="chat-head">
            <div>
              <strong>{lead.name}</strong>
              <br />
              <small>محادثة تجريبية — اكتب رد العميل هنا</small>
            </div>
            <span className="tag">{phase || lead.status}</span>
          </div>
          <div className="hint">اضغط رداً جاهزاً أو اكتب في الصندوق ثم أرسل.</div>
          <div className="bubbles">
            {history.map((msg, index) => (
              <div key={index} className={`bubble ${msg.role === "user" ? "user" : "assistant"}`}>
                {msg.content}
              </div>
            ))}
            <div ref={bottom} />
          </div>
          <div className="chips">
            {CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                className="chip"
                disabled={busy || lead.opted_out}
                onClick={() => void sendText(chip)}
              >
                {chip}
              </button>
            ))}
          </div>
          <form className="composer" onSubmit={send}>
            <textarea
              value={draft}
              placeholder="اكتب هنا كأنك العميل على واتساب"
              onChange={(e) => setDraft(e.target.value)}
              disabled={lead.opted_out || busy}
            />
            <button className="btn accent" disabled={busy || lead.opted_out}>
              إرسال
            </button>
          </form>
        </section>
        <aside>
          <div className="card side-card">
            <h3>الملف</h3>
            <p>المهنة: {lead.profession || "غير محددة"}</p>
            <p>موقع حالي: {lead.has_website || "غير معروف"}</p>
            <p>كيف يجدونه: {lead.how_found || "غير معروف"}</p>
            <p>اللغة: {lead.language}</p>
          </div>
          <div className="card side-card">
            <h3>الديمو</h3>
            {demoUrl ? (
              <p>
                <a className="btn" href={demoUrl} target="_blank" rel="noreferrer">
                  افتح الموقع التجريبي
                </a>
              </p>
            ) : (
              <p className="muted">لم يُبنَ بعد. وافق من المحادثة أو ابنِه من هنا.</p>
            )}
            <button className="btn ghost" onClick={() => void buildDemo()} disabled={busy}>
              بناء الديمو الآن
            </button>
          </div>
          <div className="card side-card">
            <h3>الاشتراك</h3>
            <p className="muted">التسجيل يدوي في المرحلة 0. التحويل البنكي خارج المنصة.</p>
            <button className="btn ghost" onClick={() => void api.subscribe(leadId)}>
              تسجيل اشتراك
            </button>
          </div>
        </aside>
      </div>
    </>
  );
}
