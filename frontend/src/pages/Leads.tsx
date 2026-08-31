import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, Lead } from "../api";

const empty = {
  name: "",
  phone: "+216",
  product: "portfolio",
  country: "Tunisia",
  profession: "",
  notes: "",
};

function usable(lead: Lead) {
  return Boolean(lead.name?.trim() || lead.phone?.replace("+", "").trim());
}

function initial(name: string) {
  return (name.trim()[0] || "؟").toUpperCase();
}

export function Leads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [form, setField] = useState(empty);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const product = params.get("product");
    if (product) setField((current) => ({ ...current, product }));
  }, [params]);

  async function refresh() {
    setLeads(await api.leads());
  }

  useEffect(() => {
    refresh().catch((err: Error) => setError(err.message));
  }, []);

  const visible = useMemo(() => leads.filter(usable), [leads]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const lead = await api.createLead({ ...form, source: "manual", consent_opt_in: true });
      setField(empty);
      await refresh();
      navigate(`/leads/${lead.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل الحفظ");
    } finally {
      setBusy(false);
    }
  }

  async function startTrial() {
    const lead = await api.trialLead();
    navigate(`/leads/${lead.id}`);
  }

  async function remove(id: number) {
    await api.deleteLead(id);
    await refresh();
  }

  return (
    <>
      <div className="toolbar">
        <div>
          <h1>العملاء والمحادثة</h1>
          <p className="lede">
            املأ النموذج ثم احفظ: ستُفتح المحادثة مباشرة. لا يُرسل واتساب حقيقي من هنا.
          </p>
        </div>
        <button className="btn accent" onClick={() => void startTrial()}>
          تجربة جاهزة
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <form className="form card" onSubmit={onSubmit} style={{ marginBottom: 8 }}>
        <label>
          الاسم
          <input
            value={form.name}
            placeholder="مثال: سارة بن علي"
            onChange={(e) => setField({ ...form, name: e.target.value })}
            required
          />
        </label>
        <label>
          الهاتف مع رمز الدولة
          <input
            value={form.phone}
            placeholder="+216..."
            onChange={(e) => setField({ ...form, phone: e.target.value })}
            required
          />
        </label>
        <label>
          المنتج
          <select
            value={form.product}
            onChange={(e) => setField({ ...form, product: e.target.value })}
          >
            <option value="portfolio">Vision Portfolio</option>
            <option value="business">Vision Presence</option>
            <option value="bac">Vision Bac</option>
          </select>
        </label>
        <label>
          المهنة / النشاط
          <input
            value={form.profession}
            placeholder="محامي، مطعم، مستقل..."
            onChange={(e) => setField({ ...form, profession: e.target.value })}
          />
        </label>
        <label>
          البلد
          <input
            value={form.country}
            onChange={(e) => setField({ ...form, country: e.target.value })}
          />
        </label>
        <label>
          ملاحظات
          <input
            value={form.notes}
            onChange={(e) => setField({ ...form, notes: e.target.value })}
          />
        </label>
        <div>
          <button className="btn accent" type="submit" disabled={busy}>
            حفظ وافتح المحادثة
          </button>
        </div>
      </form>
      {visible.length === 0 ? (
        <div className="empty">
          <p>لا يوجد عملاء بعد. احفظ النموذج أعلاه أو اضغط تجربة جاهزة.</p>
        </div>
      ) : (
        <div className="lead-grid">
          {visible.map((lead) => (
            <article className="lead-card" key={lead.id}>
              <header>
                <div className="avatar">{initial(lead.name)}</div>
                <span className={`tag ${lead.status === "demo_ready" ? "ready" : "new"}`}>
                  {lead.opted_out ? "إيقاف" : lead.status}
                </span>
              </header>
              <div>
                <strong>{lead.name || "بدون اسم"}</strong>
                <div className="muted">{lead.phone}</div>
                <div className="muted">{lead.product}</div>
              </div>
              <Link className="btn" to={`/leads/${lead.id}`}>
                افتح المحادثة
              </Link>
              <button className="btn danger" onClick={() => void remove(lead.id)}>
                حذف
              </button>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
