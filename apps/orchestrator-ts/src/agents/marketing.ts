import { MarketingTools } from "../tools/marketingApis.js";

// Priority order (DECISIONS.md): campaign analysis, social drafting with
// approval, SEO and blog grounded in brand RAG, competitor research (phase 2).
export async function gatherMarketingContext(tools: MarketingTools, userId: string) {
  const metrics = await tools.fetchCampaignMetrics(userId);
  return { metrics };
}

export function classifyMarketingTask(prompt: string): string {
  const p = prompt.toLowerCase();
  if (p.includes("lead") && (p.includes("score") || p.includes("dealer") || p.includes("prospect"))) return "domain4s_lead_scoring";
  if (p.includes("maintenance due") || p.includes("reminder") || p.includes("retention") || p.includes("تذكير صيانة")) return "domain4s_retention_campaign";
  if (p.includes("content calendar") || p.includes("خطة محتوى")) return "domain4s_content_calendar";
  if (p.includes("jobcard") || p.includes("4s") || p.includes("workshop") || p.includes("ورشة")) return "domain4s_copy_generation";
  if (p.includes("analy") || p.includes("metric") || p.includes("roas") || p.includes("ctr") || p.includes("حلل")) return "campaign_analysis";
  if (p.includes("seo") || p.includes("blog") || p.includes("مقال")) return "seo_drafting";
  if (p.includes("competitor") || p.includes("منافس")) return "competitor_research";
  return "copy_generation";
}
