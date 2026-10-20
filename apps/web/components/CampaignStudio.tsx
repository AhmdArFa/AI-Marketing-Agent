"use client";

import { useState } from "react";

const ENGINE = process.env.NEXT_PUBLIC_ENGINE_URL ?? "http://localhost:8000";

type Post = Record<string, any>;

export default function CampaignStudio() {
  const [company, setCompany] = useState("Vo Technology");
  const [product, setProduct] = useState("4S PLUS");
  const [language, setLanguage] = useState("ar");
  const [audience, setAudience] = useState("prospecting");
  const [count, setCount] = useState(3);
  const [campaign, setCampaign] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approved, setApproved] = useState<Record<string, boolean>>({});
  const [publishState, setPublishState] = useState<Record<string, any>>({});
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const r = await fetch(`${ENGINE}/v1/generate/campaign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: company,
          product_name: product,
          language,
          audience,
          count,
          domain: "automotive_erp",
        }),
      });
      if (!r.ok) throw new Error(String(r.status));
      setCampaign(await r.json());
    } catch {
      setError("Engine unreachable. Start it: cd services/engine-py && uvicorn app.main:app --port 8000");
    } finally {
      setBusy(false);
    }
  }

  async function publish(post: Post) {
    const r = await fetch(`${ENGINE}/v1/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: company,
        product_name: product,
        channel: "file_export",
        approved: !!approved[post.id],
        post,
      }),
    });
    const data = await r.json().catch(() => ({}));
    setPublishState((s) => ({ ...s, [post.id]: r.ok ? data : { status: "blocked", detail: data.detail } }));
  }

  return (
    <div>
      <p className="lede">
        Give it a company and a domain. It writes the posts, renders the images, checks every line against the
        claim guardrails, and only pushes a package out after a human approves it.
      </p>
      <div className="studioform">
        <label>
          Company name
          <input value={company} onChange={(e) => setCompany(e.target.value)} />
        </label>
        <label>
          Product
          <input value={product} onChange={(e) => setProduct(e.target.value)} />
        </label>
        <label>
          Language
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="ar">Arabic</option>
            <option value="en">English</option>
          </select>
        </label>
        <label>
          Audience
          <select value={audience} onChange={(e) => setAudience(e.target.value)}>
            <option value="prospecting">Prospecting (B2B)</option>
            <option value="dealer_marketing">Dealer marketing (B2C)</option>
          </select>
        </label>
        <label>
          Posts
          <input type="number" min={1} max={4} value={count} onChange={(e) => setCount(Number(e.target.value))} />
        </label>
        <button className="primary" onClick={generate} disabled={busy}>
          {busy ? "Generating..." : "Generate campaign"}
        </button>
      </div>

      {error && <div className="alert">{error}</div>}

      {campaign && (
        <div className="postgrid">
          {campaign.posts.map((post: Post) => (
            <article key={post.id} className="postcard">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`${ENGINE}${post.image_url}`} alt={post.image.headline} />
              <div className="postbody">
                <div className="cardhead">
                  <strong>{post.pillar}</strong>
                  <span className={post.guardrail_ok ? "badge safe" : "badge danger"}>
                    {post.guardrail_ok ? "Guardrails: clean" : "Blocked"}
                  </span>
                </div>
                <p dir={language === "ar" ? "rtl" : "ltr"}>{post.body}</p>
                <p className="tags">{post.hashtags.join(" ")}</p>
                <label className="approve">
                  <input
                    type="checkbox"
                    checked={!!approved[post.id]}
                    onChange={(e) => setApproved((s) => ({ ...s, [post.id]: e.target.checked }))}
                  />
                  I approve pushing this post
                </label>
                <button className="primary" disabled={!approved[post.id]} onClick={() => publish(post)}>
                  Push publish package
                </button>
                {publishState[post.id] && (
                  <p className="publishresult">
                    {publishState[post.id].status}
                    {publishState[post.id].location ? `: ${publishState[post.id].location}` : ""}
                    {publishState[post.id].detail ? `: ${publishState[post.id].detail}` : ""}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
