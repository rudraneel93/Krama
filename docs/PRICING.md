# Plans and pricing

| Plan | Price | Checks | Per minute |
|---|---|---|---|
| Free | ₹0 | 10 a day, up to 300 a month | 10 |
| Starter | ₹4,999 / month | 25,000 a month | 120 |
| Growth | ₹14,999 / month | 1,50,000 a month | 600 |
| Scale | ₹49,999 / month | 10,00,000 a month | 1,200 |
| Enterprise | contact us | custom, self-hosting available | custom |

**Pay as you go:** 500 checks for ₹299, 2,500 for ₹1,199, 10,000 for ₹3,999. Credits never expire and
are used only after your plan's daily or monthly allowance runs out.

- One check = one request of up to 1,000 values, from the website, Excel, the API or Python alike.
- Days and months reset at midnight India time.
- Checks that fail (invalid input, limits, time-outs, server busy) are refunded automatically.
- At the limit the API returns `429 quota_exceeded`. Responses carry `X-Daily-Remaining`,
  `X-Quota-Remaining` and `X-Credits-Remaining`.
- Billing is monthly in INR through Razorpay (cards, UPI, net banking); taxes as applicable.

Start free at [getkrama.vercel.app/app](https://getkrama.vercel.app/app).
