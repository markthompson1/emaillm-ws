# PRD · EmailLM MVP (Windsurf Track)

## 1 · Executive Summary
EmailLM lets anyone send an email to **AnyTopic@emaillm.com** and receive an AI-generated reply—no app or login required.  
This track is built with **Windsurf** (agent-first IDE + one-click deploy) and GitHub CI.

### Success metrics
| Metric | Target |
| ------ | ------ |
| Median reply time | ≤ 6 s |
| Day-7 retention | ≥ 35 % |
| Cache hit rate | ≥ 60 % |

---

## 2 · Core capabilities (MVP)

1. **Inbound email reception** (SendGrid webhook)  
2. **Alias-based topic extraction + NL fallback**  
3. **Daily cache** `alias#YYYY-MM-DD#ctxHash`  
4. **GPT-4o-mini response generation**  
5. **Outbound email send** (SendGrid)  
6. **Freemium quota + Stripe billing**  
7. **Admin dashboard** (usage, resend, cache stats)

---

## 3 · Architecture

```mermaid
flowchart LR
    A[SendGrid Inbound] -->|POST /webhook/inbound| B(Parser & Cache)
    B -->|Cache hit| C[SendGrid Out]
    B -->|Cache miss| D[OpenAI GPT-4o]
    D --> E[Formatter]
    E --> C
    B --> F[Firestore Usage]
    G[Admin UI] --> F
```

## 4 · Prerequisites

- Windsurf account (or local CLI)
- GitHub repo with Actions
- SendGrid & OpenAI keys
- Stripe account (Price IDs per tier)

## 5 · Subscription Tiers & Billing

| Tier | Monthly quota (e-mails) | Extra capabilities | Included in MVP? |
| ---- | ----------------------- | ----------------- | ---------------- |
| Free | 10 / week (cap 40 / mo) | • GPT-4o-mini<br>• No login (email only)<br>• Rate-limit & abuse guard | Yes |
| Starter $10 | 100 / mo | • Prompt-enhancement pipeline<br>• Personal usage dashboard | Yes (pipeline stub + dashboard stub) |
| Premium $20 | 500 / mo | • Smart model picker (best LLM per topic)<br>• Faster processing queue | Yes (picker stub + queue priority) |
| Team $50 | 2,000 / mo (pooled) | • Team admin (invite/remove)<br>• Shared inbox & team dashboard<br>• Basic white-label ("From", logo) | Post-MVP |
| Business $100+ | ≥ 5,000 / mo (neg.) | • Advanced analytics & reporting<br>• Slack/Teams/Zapier hooks<br>• Full white-label (custom domains) | Post-MVP |
| Enterprise (Custom) | Negotiated | • Dedicated account team & support<br>• On-prem / VPC deploy<br>• Compliance (GDPR, SOC 2, …) | Post-MVP |

### 5.1 · Data-model additions (Firestore)
```
users/            email → tier, usage_month, usage_week, team_id?
subscriptions/    stripe_cust_id → tier, quota_month, quota_week, renew_date
teams/            team_id → name, owner, members[], plan_tier
pricing_plans/    tier → price, quota_month, quota_week, features[]
```

**Why pricing_plans?**  
Lets ops tweak quotas or prices from the Admin UI without redeploying.

### 5.2 · Quota & feature-flag middleware (flow)
1. Identify sender by e-mail address (no login for Free/Starter/Premium).
2. Fetch tier + quotas.
3. If usage > quota → send "Upgrade or wait" email; stop.
4. Tier-specific flags:
   - Starter + → run prompt_enhancer()
   - Premium + → call model_picker() and set high queue priority
5. Continue to cache & LLM stages.

### 5.3 · Prompt enhancer (Starter +)
Triggered when subject + body ≤ 4 words or blank.

| Alias category | Expansion template |
| -------------- | ------------------ |
| Sports team | Summarise latest news, match results, and upcoming fixtures for {team}. |
| Stock ticker | Give latest share price, day-change %, and headline news for {company}. |
| Weather | Provide today's forecast (temp, precipitation, wind) for {location}. |

Templates live in prompt_templates.json.

### 5.4 · Smart model picker (Premium +)
```javascript
model_by_topic = {
    "sports":  "gpt-4o-mini",
    "finance": "claude-3-haiku",
    "general": "llama-3-70b",
}
```
Later swap for latency/cost-aware logic.

### 5.5 · Admin dashboard (MVP widgets)
| Widget | Free | Starter | Premium |
| ------ | ---- | ------- | ------- |
| Personal usage vs quota | ✓ | ✓ | ✓ |
| Cost / profit graph | – | ✓ | ✓ |
| Plan upgrade button | – | ✓ | ✓ |

### 5.6 · Stripe checklist
- Price IDs created per tier.
- Webhooks handled:
  - customer.subscription.created / updated → set tier + quotas
  - invoice.payment_failed → grace-period notice
- Even Free tier creates a Stripe Customer (no card) for 1-click upgrades.

### 5.7 · New MVP tickets
| ID | Description |
| -- | ----------- |
| WS-05 | Seed pricing_plans data + admin toggle |
| WS-06 | Implement quota-enforcement middleware |
| WS-07 | Build prompt_enhancer() + unit tests |
| WS-08 | Add model_picker() stub + queue priority flag |
| WS-09 | Stripe webhook handler (/webhook/stripe) |

(Mirror as DB-05 … DB-09 in the Databutton track.)