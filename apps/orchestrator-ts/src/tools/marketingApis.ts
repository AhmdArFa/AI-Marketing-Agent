// Marketing tool interfaces. Publishing always requires an approval first.

export interface CampaignMetricRow {
  campaign: string;
  channel?: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface MarketingTools {
  fetchCampaignMetrics(userId: string): Promise<CampaignMetricRow[]>;
  scheduleDraft(userId: string, draft: string, topic: string): Promise<void>;
}

export const demoMarketingTools: MarketingTools = {
  async fetchCampaignMetrics() {
    return [
      { campaign: "Search A", channel: "google_ads", spend: 420.5, impressions: 24500, clicks: 890, conversions: 28, revenue: 1680 },
      { campaign: "Social B", channel: "meta_ads", spend: 310.0, impressions: 19200, clicks: 740, conversions: 31, revenue: 620 },
      { campaign: "Retargeting C", channel: "meta_ads", spend: 150.0, impressions: 8200, clicks: 410, conversions: 22, revenue: 990 },
    ];
  },
  async scheduleDraft() {
    throw new Error("Mutating tool: must go through ApprovalGate, never called directly");
  },
};
