import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export function Demos() {
  const [rows, setRows] = useState<
    { id: number; lead_id: number; slug: string; url: string; template: string }[]
  >([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.demos().then(setRows).catch((err: Error) => setError(err.message));
  }, []);

  return (
    <>
      <h1>مواقع الديمو</h1>
      <p className="lede">كل موقع يُولَّد بعد المحادثة ويُفتح من هنا.</p>
      {error && <div className="error">{error}</div>}
      {rows.length === 0 ? (
        <div className="empty">
          <p>لا يوجد ديمو بعد. ابدأ محادثة وابنِ الأول من زر «بناء الديمو الآن».</p>
          <Link className="btn accent" to="/leads">
            اذهب إلى العملاء
          </Link>
        </div>
      ) : (
        <div className="lead-grid">
          {rows.map((row) => (
            <article className="lead-card" key={row.id}>
              <span className="tag">{row.template}</span>
              <strong>عميل #{row.lead_id}</strong>
              <a className="btn accent" href={row.url} target="_blank" rel="noreferrer">
                افتح الديمو
              </a>
              <Link className="btn ghost" to={`/leads/${row.lead_id}`}>
                ارجع للمحادثة
              </Link>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
