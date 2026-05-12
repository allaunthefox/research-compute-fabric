# Total Calculation Review

> Service / Category,Type,Jun 2026,Jul 2026,Aug 2026,Sep 2026,Oct 2026,Nov 2026,Dec 2026,Projected Total (H2)
ChatGPT Plus,Active Sub,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$148.40
Ollama,Active Sub,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Google Cloud / APIs,Variable Compute (Est.),$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Kimi.com,Affirm Loan (Est.),$37.67,$37.67,$37.67,$37.67,$37.67,$0.00,$0.00,$188.35
Wolfram Alpha,Affirm Loan (Est.),$10.55,$10.55,$10.55,$0.00,$0.00,$0.00,$0.00,$31.65
MONTHLY TOTAL,,$109.42,$109.42,$109.42,$98.87,$98.87,$61.20,$61.20,$648.40

**Claude and canceled items are not present** in this version.
One naming issue: **“Projected Total (H2)” is technically Jun–Dec**, which is 7 months. True H2 is usually **Jul–Dec**.
|---|---:|
| Jun–Dec 2026 | **$648.40** |
|---|---:|
| Jul–Dec 2026 | **$538.98** |
|---|---:|
| Google Cloud / APIs | $120.00 |
| **Total** | **$538.98** |
**Projected Total (Jun–Dec)**

Main read: your monthly cost stays at **$109.42** through August, drops to **$98.87** in September when Wolfram ends, then drops to **$61.20** in November when Kimi ends.
Download: [projected_monthly_costs_line_chart.png](sandbox:/mnt/data/projected_monthly_costs_line_chart.png)

I made **two charts**:
1. **All detected bills + projected subscriptions**
   Includes loans, storage, credit/card payments, subscriptions, hosting, software, etc.
   [Download full all-bills chart](sandbox:/mnt/data/all_detected_bills_line_chart_2026.png)
2. **Service/subscription-only view**
   Removes the big loan/card-payment lines so the smaller subscriptions are actually readable.
   [Download service/subscription chart](sandbox:/mnt/data/all_service_subscription_bills_line_chart_2026.png)
I also exported the monthly bill matrix as CSV:
[Download all detected bills monthly matrix](sandbox:/mnt/data/all_detected_bills_monthly_matrix_2026.csv)
I kept **Claude out** based on your earlier “remove Claude/canceled ones” instruction. The full detector found **36 bill groups** and a 2026 actual/projected total of **$6,257.59**.

- **Zoom / rotate / pan**
- **Click any line or point** to explain that bill
- **Details panel** with total, active months, peak month, average active month
- **Month-by-month breakdown**
- **Legend toggles** for every bill line
- Buttons for:
  - Show all
  - Services only
  - Repayments only
  - Top 10
  - Total only
- **Linear / log scale toggle** so smaller subscriptions are visible next to repayment spikes
Download/open it here:
[interactive_threejs_bill_lines_2026.html](sandbox:/mnt/data/interactive_threejs_bill_lines_2026.html)

[Download interactive_threejs_bill_lines_2026_v2.html](sandbox:/mnt/data/interactive_threejs_bill_lines_2026_v2.html)
- **All 37 bill lines are visible by default**
- Legend and details panels are now **collapsible**
- Chart has more usable space
- Click a **line** for the bill explanation
- Click a **point** for that specific month’s amount
- Added better filters:
  - Show all
  - Services only
  - Repayments only
  - Top 10
  - Total only
- Kept the **linear/log scale toggle** so tiny subscriptions do not get crushed by the giant repayment spikes

Assuming your June income is the usual **~$1,014**, and your real bill pattern looks like Jan–Apr, you’re likely short about:
# **~$360 in June**
That is **bills only**.
|---|---:|
| Avg all-bills month from Jan–Apr | **~$1,373** |
| Expected June income | **~$1,014** |
| Estimated June gap | **~$359 short** |
Important caveat: the clean projection table only shows **$109.42** for June, but that excludes the big recurring-looking stuff like storage, credit payments, Affirm/MyPay behavior, and card interest. So the realistic answer is **not $109.42**. It is closer to **$350–$400 short** unless some of those repayments/storage/card payments stop.

[Download june_2026_bill_shortfall_flat_breakout.png](sandbox:/mnt/data/june_2026_bill_shortfall_flat_breakout.png)
One correction to the earlier TL;DR: using the current June projection matrix, June only shows **$109.42** in bills, so against **$1,014 assumed income**, that is a **$904.58 surplus**, not a shortfall.
The earlier **~$360 short** estimate was based on averaging the heavy Jan–Apr bill pattern forward. This PNG uses the actual June projection matrix.

You’re right — the last PNG was wrong because it treated blank future months as **true $0 bills**. That is not a valid forecast.
I rebuilt it as a **June forecast** by carrying recurring bills forward.
|---|---:|---:|
| Fixed / recurring bills only | **$572.88** | **$441.12 surplus** |
| If Affirm/MyPay-style repayments repeat | **$1,426.78** | **$412.78 short** |
# **You are not short on fixed bills, but you are ~$413 short if the repayment pattern repeats.**
Corrected PNG:
[Download june_2026_corrected_bill_forecast_flat.png](sandbox:/mnt/data/june_2026_corrected_bill_forecast_flat.png)

Yep — that **$390 MyPay repayment was a bad forecast assumption**. It came from using the Jan–Apr MyPay repayment history as a median, but your current open exposure is much lower.
- Jan: **$420**
- Feb: **$360**
- Mar: **$480**
- Apr: **$200**
- May so far: **$0 repayment**, with an observed **$80 advance**
So I’m replacing the MyPay stress estimate with your real current estimate: **~$100 borrowed**, plus a small fee allowance.

You’re right — **MyPay should not be forecast at $390**.
|---|---:|---:|
| Fixed bills + corrected MyPay ~$100 | **$678.88** | **$335.12 surplus** |
| Fixed bills + corrected MyPay + Affirm repeat | **$1,133.27** | **$119.27 short** |
# **You are not short because of MyPay.**
# **You’re only short if the Affirm-style repayments also repeat.**
Updated PNG:
[Download june_2026_mypay_corrected_flat.png](sandbox:/mnt/data/june_2026_mypay_corrected_flat.png)

> Service / Category,Type,Jun 2026,Jul 2026,Aug 2026,Sep 2026,Oct 2026,Nov 2026,Dec 2026,Projected Total (H2)
ChatGPT Plus,Active Sub,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$148.40
Ollama,Active Sub,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Google Cloud / APIs,Variable Compute (Est.),$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Kimi.com,Affirm Loan,$37.67,$37.67,$37.67,$37.67,$37.67,$37.67,$37.67,$263.69
Wolfram Alpha,Affirm Loan,$10.55,$10.55,$10.55,$10.55,$10.55,$10.55,$10.55,$73.85
MONTHLY TOTAL,,$109.42,$109.42,$109.42,$109.42,$109.42,$109.42,$109.42,$765.94

> Service / Category,Type,Jun 2026,Jul 2026,Aug 2026,Sep 2026,Oct 2026,Nov 2026,Dec 2026,Projected Total (H2)
ChatGPT Plus,Active Sub,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$21.20,$148.40
Ollama,Active Sub,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Google Cloud / APIs,Variable Compute (Est.),$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$20.00,$140.00
Kimi.com,Affirm Loan,$37.67,$37.67,$37.67,$37.67,$37.67,$37.67,$37.67,$263.69
Wolfram Alpha,Affirm Loan,$10.55,$10.55,$10.55,$10.55,$10.55,$10.55,$10.55,$73.85
MONTHLY TOTAL,,$109.42,$109.42,$109.42,$109.42,$109.42,$109.42,$109.42,$765.94

The **big $454.39 Affirm risk layer was wrong** in the same way the MyPay estimate was wrong: it was a historical median artifact. Your actual Affirm schedule is:
|---|---:|
| **Actual Affirm loan layer** | **$48.22/mo** |
|---|---:|
| Fixed / recurring bills | $583.43 |
| **June bill total** | **$689.43** |
| **Remaining after bills** | **$324.57** |
# **You are not short.**
# **You have about $324.57 left after fixed bills plus ~$100 MyPay.**
Updated flat PNG:
[Download june_2026_affirm_corrected_final_flat.png](sandbox:/mnt/data/june_2026_affirm_corrected_final_flat.png)
Also: your uploaded LLM table totals **$765.94 for Jun–Dec**, or **$656.52 for true Jul–Dec H2**.

> One-time payment
-$28.50

Added **netcup GmbH** as a June payment-plan bill.
|---|---:|
| Previous fixed / recurring forecast | $583.43 |
| **June total** | **$717.93** |
| **Remaining after bills** | **$296.07** |
So you’re still **not short** under this corrected model.
Files:
[Download updated PNG](sandbox:/mnt/data/june_2026_forecast_with_netcup_flat.png)
[Download updated CSV](sandbox:/mnt/data/june_2026_forecast_with_netcup.csv)

Yes — **directionally, yes.** Under the assumptions you gave:
1. **No more MyPay / Affirm / emergency loans**
2. **CubeSmart gets canceled**
3. The current bill model is otherwise accurate
You should have enough room to start pulling ahead and potentially knock out **at least one smaller credit card**.
|---|---:|
| Current June total with netcup + MyPay | $717.93 |
| Remove CubeSmart estimate | -$124.49 |
| **New June bill total** | **$593.44** |
| **Remaining after listed bills** | **$420.56** |
**$296.07 remaining → $420.56 remaining**
If your smallest credit card payoff balance is **under ~$300–$400**, then yes, you may be able to kill one off in June **as long as normal life expenses do not eat the entire buffer**.
|---|---:|
| Keep emergency / food / gas buffer | $100–$150 |
| Put toward one card | **$250–$320** |
The main thing is: **do not pay a card down so aggressively that you need another short-term loan.** That would just move the debt sideways and add fees.
**Yes. If CubeSmart really drops and you stop taking new loans, you should finally have enough monthly slack to start killing a small card instead of just surviving the minimums.**

> - Payments & Credits $40.00
+ Purchases & Other Charges $0.00
+ FEES CHARGED $21.54
+ INTEREST CHARGED $17.39
= New Balance $615.48
QUESTIONS? Call 1-800-353-5920
Beaverton, OR 97076-4499
of up to $41. To cancel Overlimit Coverage, call us at 1-800-353-5920
P.O. Box 4477, Beaverton OR 97076-4477.
Late Payment Warning: If we do not receive your minimum
Minimum Payment Warning: If you make only the minimum
1-800-353-5920.
Notice: SEE REVERSE SIDE FOR MORE IMPORTANT INFORMATION
04/09 04/09 8534348FL00XSL38A PAYMENT RECEIVED - THANK YOU 40.00-
05/04 05/04 MONTHLY FEE 12.50
05/05 05/05 CREDIT PROTECTION FEES 9.04
Amount Enclosed: $
DES MOINES IA 50317-4023
Charlotte NC 28296-0541
Beaverton OR 97076-4477BRANDON SCHNEIDER Account number ending in 5655
05/05 05/05 Interest Charge on Purchases 17.39
05/05 05/05 Interest Charge on Cash Advances 0.00
Totals 2026 Year-to-Date
1-800-693-9571.
your last Billing Statement. The Monthly Fee is $12.50 ($150.00 annually). Please see the Monthly Fee on the back of the statement for additional renewal
Purchases 35.90% $581.38 $17.39
Cash Advances 35.90% $0.00 $0.00
(v) = variableBRANDON SCHNEIDER Account number ending in 5655

Yes — **this matches the forecast line I used for Concora.**
|---|---:|
| New balance | **$615.48** |
| Minimum due | **$40.00** |
| Due date | **June 4, 2026** |
| APR | **35.90%** |
```text
Previous balance     $616.55
- Payment             $40.00
+ Monthly fee         $12.50
+ Credit protection    $9.04
+ Interest            $17.39
= New balance        $615.48
```
So your **$40 Concora June bill** is correct.
|---|---:|
| **Total monthly drag** | **$38.93** |
```text
$40.00 - $38.93 = $1.07
```
Yes. This card is a strong payoff candidate, but **not quite a one-month kill** unless you have around **$615.48** available.
With the CubeSmart-canceled estimate, you were around **$420.56 remaining** before this new statement check. So you could likely make a major hit, but probably not fully erase Concora in June unless more cash frees up.
```text
June minimum required: $40
Real useful extra target: $250–$350+
Full payoff target: $615.48
```
Also: the statement shows **Credit Protection Fee = $9.04/month** and **Overlimit Coverage is on**. Those are worth reviewing because they are leak points. The overlimit coverage especially can expose you to a fee of up to **$41** if a transaction pushes the account over limit.

Yes — that logic is reasonable **if the loan charge is less than the card’s ongoing bleed** and you do not re-run the card balance afterward.
|---|---:|
| **Total current monthly drag** | **$38.93/mo** |
So every month you leave it mostly unpaid, it is basically punching you for **~$39** before your payment even matters.
## Break-even logic
The statement says minimum-only payoff would cost about **$836 total** on a **$615.48** balance.
```text
$836.00 - $615.48 = $220.52
```
So if eating loan charges costs you **less than ~$220** and lets you truly kill this card faster, it can be rational.
But the stronger short-term rule is:
```text
If the loan charge is less than 2–4 months of card bleed,
it may be worth it.
```
At **~$39/mo**, that means:
|---|---|
| $20–$40 | probably worth it |
| $50–$100 | maybe worth it if it fully kills the card |
| $150+ | only worth it if it prevents a long minimum-payment spiral |
| $220+ | probably not better than the card’s own warning math |
1. **Cancel credit protection** if you do not truly need it. That is **$9.04/mo**.
2. **Cancel overlimit coverage** so the card cannot smack you with an overlimit fee.
3. Ask Concora for the **exact payoff amount**.
4. Pay it to zero.
5. Strongly consider **closing it** or freezing it physically/digitally, because the statement says the **monthly fee continues unless you notify them to close the account**.
Yes: **eating a smaller loan charge to escape this card can be the correct move.**
The card is bleeding about **$39/month**, and minimum payments are almost useless. Just make sure the replacement loan is a one-time bridge, not the start of a new loop.

Yes — **keeping it open but dormant can make sense** because it preserves the open credit line and helps your utilization ratio.
But for **this specific Concora card**, there’s a trap:
# Dormant ≠ free
Your statement says the account has a **$12.50 monthly fee**, or **$150/year**, unless you close the account. So if you pay it off and leave it open, you may still be paying **$12.50/month just to keep the tradeline alive**.
|---|---|
| 1 | Pay it down/off aggressively |
| 2 | Cancel **credit protection** |
| 3 | Cancel **overlimit coverage** |
| 4 | Lock/freeze the card |
| 5 | Leave it open only if the credit-score benefit is worth the $12.50/mo fee |
```text
+ $700 credit limit helping utilization
+ older/open tradeline support
- $150/year monthly fee
- risk of accidental charges / fee spiral
```
```text
Keep dormant only while the credit buoyancy is worth $12.50/month.
Close it once better no-fee credit lines replace it.
```
Your instinct is good: **pay it off, freeze it, let it buoy your credit short-term.**
But I would not let this be a “forever” card. A card with **35.90% APR + monthly fee + overlimit coverage + credit protection fee** is basically a financial bear trap wearing a credit-score hat.

Exactly. Until the car is secured, the priority is **financial limb preservation**, not perfect optimization.
## 1. Do not create new short-term debt
|---|---|
| MyPay / cash advances | They create next-month holes |
| New Affirm/Klarna-style plans | They make fixed costs creep upward |
```text
Pay down/off → cancel credit protection → cancel overlimit coverage → freeze/lock card → leave dormant if useful
```
That preserves the credit-line benefit while reducing the ways it can bite you.
```text
$300–$500 “do not touch unless survival/car” buffer
```
```text
~$39/month in fee + protection + interest
```
But the trick is to kill the bleeding **without** replacing it with a worse loan cycle.
```text
Survive cleanly → stop new loans → cancel CubeSmart if possible → kill card bleed → preserve credit → get car
```

Yes — **waterfall is the correct shape here**, especially because you still have Credit One after Concora.
```text
Minimums on everything
↓
Keep survival / car buffer
↓
Extra goes to the worst bleeding card
↓
When that card is dead/dormant, roll its payment into the next card
```
|---:|---|---|
| 1 | Minimums on all cards/loans | Avoid late fees and credit damage |
| 2 | Do not take new loans | Prevent next-month hole |
| 3 | Cancel CubeSmart if possible | Frees about **$124/mo** |
| 4 | Kill / neuter Concora | Minimum barely moves balance |
|---|---:|
| **Total drag** | **$38.93** |
```text
$40.00 - $38.93 = $1.07
```
```text
~$68 payment
~$30 interest
≈ $38 actual balance reduction
```
|---|---:|
| With CubeSmart | **~$296** |
| Without CubeSmart | **~$421** |
I’d treat that **~$421** like this:
|---|---:|
| Car / emergency buffer | $100–$150 |
| Extra to Concora | **$250–$320** |
```text
June:
minimums paid
cancel CubeSmart if possible
cancel Concora credit protection
cancel Concora overlimit coverage
throw extra at Concora
do not touch new loans

July:
roll freed cash + normal surplus into Concora
then move waterfall to Credit One
```
Yes. **Waterfall Concora first, then Credit One.**

> Customer Email:ALLAUNJSILVERFOX@GMAIL.COMStatus:Customer CanceledConfirmation Number:89068177Cancellation Date:05/09/2026 11:38 PM EST
The Indigo Plantinum Mastercard is issued by Celtic Bank, a Utah-Chartered Industrial Bank, and serviced by Concora Credit Inc. Indigo is a registered trademark of Concora Credit Inc.
CA Collection Agency License #10739-99

Good — that is a **real win**.
|---|---|
| Program | Concora / Indigo Credit Protection |
| Status | **Customer Canceled** |
| Confirmation # | **89068177** |
| Cancellation date | **05/09/2026 11:38 PM EST** |
|---|---:|
| **Total drag** | **$38.93/mo** |
|---|---:|
| Credit protection | **$0.00** |
| **New drag estimate** | **~$29.89/mo** |
# **+$9.04/month**
Before:
```text
$40.00 payment - $38.93 drag = $1.07 progress
```
After:
```text
$40.00 payment - ~$29.89 drag = ~$10.11 progress
```
Now do the same kind of neutering for **overlimit coverage** if you have not already. That one is about preventing a surprise **up to $41** fee.
Keep that confirmation number somewhere safe. This is exactly the kind of tiny leak-plugging that makes the waterfall actually start working.

I get the instinct, but for **overlimit coverage**, the statement wording means the opposite of what you want.
Means:
```text
They may approve a transaction that pushes you over $700
→ then charge an overlimit fee up to $41
→ then your balance is even worse
```
So **ON = surprise over-the-limit can happen.**
Means:
```text
A transaction that would push you over limit is more likely to decline
→ no new overlimit fee from that transaction
→ the card stays neutered
```
So for your “avoid recursive surprise over-limit” goal, I would lean:
# **Turn overlimit coverage OFF.**
|---|---|
| Lock/freeze card | Prevent new charges |
| Remove it from Amazon/PayPal/Google/etc. | Prevent old autopays |
| Keep minimum/autopay active | Avoid late fee |
