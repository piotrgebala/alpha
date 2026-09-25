# KP1 — przegląd badań (workflow: 3 kierunki poszukiwań → weryfikacja źródeł → synteza), 2026-09-25

Surowy wynik syntezy (angielski, bez redakcji). Źródła odrzucone lub poprawione przez weryfikację — na końcu.

## mechanism_one_sentence

The kimchi premium mostly follows the BTC price rather than leading it. It rises after up-days and opens up during global rallies. Korea adds little to global price discovery, and since mid-2024 the premium is almost entirely the Korea-wide KRW-to-USDT on-ramp wedge (capital-control friction plus FX noise), not BTC-specific local demand. So there is no established channel by which a rising 7d-vs-90d premium should predict global BTC returns over the next week; at best it is a noisy, lagged proxy for short-term BTC momentum.

## sign_consensus

The sign is not identified. No verified source regresses future global BTC returns on the kimchi premium at horizons from 1 day to 1 month, in or out of sample.

The weak hints point in opposite directions:
(a) Contrarian on the LEVEL. Premium spikes marked tops in 2017-2019 (CoinDesk, Apr 2021; anecdotes picked after the fact). CryptoQuant's folklore threshold is a premium above 16%. Joint Coinbase and Korea spikes preceded falls in Mar 2024, Feb 2025 and Oct 2025 (BeInCrypto; 2-3 episodes). Kaiko claims the mirror image: discounts precede rallies (no numbers). In 2025 the correlation between premium level and forward returns was about -0.06 (CryptoSlate, in-sample, horizon not stated).
(b) Positive on the CHANGE near zero. In 2025, upward zero-crossings were followed by +1.7% at 7 days and +6.2% at 30 days (67-70% up). The article gives no event count and no test, and the data sit inside our sample. Against our own baseline of +0.40% per 7 days, the excess is only about +1.3 pp.

KP1 is a change rule, but it bets hardest at the extremes. There, the lore says contrarian. The mechanism evidence also argues against 'local demand leads': Makarov & Schoar (2019) find Korea's share of price discovery is smallest exactly when the premium is high, and Choi, Lehar & Stauffer find the premium follows the previous day's return.

Net: roughly a coin flip. There is a very mild contrarian lean at large excursions and a very mild positive lean around zero-crossings. Neither lean has significance testing or support from before or outside our sample.

## effect_prior

The evidence is too thin to anchor a published effect size. No published estimate exists for a weekly directional rule on the kimchi premium.

Honest prior:
- The signed expected effect is about 0.
- The plausible size, in either direction, is a Sharpe of 0 to 0.3, about 0-10%/yr at the rule's ~35%/yr volatility.
- The only number that can be converted is the in-sample 2025 correlation of about -0.06. It gives an annual Sharpe of roughly 0.35 at most for a weekly sign rule (0.06 × √52 × 0.8). That is a contrarian sign, from a single year inside our sample, before any shrinkage.
- After shrinking for publication and selection bias, and after removing the part that overlaps plain BTC time-series momentum, the incremental effect is likely below a Sharpe of 0.2.

Nothing supports the CP1 sibling either. CryptoSlate found Coinbase-premium flips gave flat returns in 2025 (~55% up). Kaiko reads a negative Coinbase premium as bullish, the opposite of CP1's sign. CP1's +32%/yr (Sharpe ~0.9) is a winner's-curse upper bound, not a prior for KP1.

## recommended_assumed_SR

0.15

## exceeds_instrument_threshold

No, on both counts. The prior of about Sharpe 0.15 (plausible range 0-0.3) is far below the half-width (Sharpe ≈ 0.9) and far below 1.4 × half-width (Sharpe ≈ 1.26).

What that means for detection:
- At Sharpe 0.15 over ~5.1 years, the expected t is about 0.34, and the chance of reaching |t| > 1.96 is about 3-4%. That is essentially the false-positive rate.
- Even at Sharpe 0.3, the expected t is about 0.7 and the chance of detection is about 10%.

Under rule 18, KP1 is NOT MEASURABLE with this instrument. A t near 2 in either direction would far more likely be noise or winner's curse than a true Sharpe of 0.9 or more.

## post_publication_evidence

There is essentially none.

- No out-of-sample or post-publication test of a directional signal built on the premium was found, academic or practitioner.
- The pre-2021 academic work (Makarov & Schoar 2019/2020; Choi, Lehar & Stauffer 2019; Borri & Shakhnov WP 2018) covers only mechanism and convergence between venues, not the direction of global BTC.
- The one later re-test found (Ok, Kim & Kim 2023) fails to confirm Eom's (2021) 'speculative bubble' result over time. That weakens the 'retail euphoria gauge' reading, but it concerns what drives the premium, not prediction.
- The only forward-return statistics (CryptoSlate, Oct 2025) are in-sample for 2025 and fall inside our sample.
- The CoinDesk article of 6 Apr 2021, published just before our sample, argued that the premium had lost its warning value because Korea's volume share had fallen from 7.9% to under 2%. BTC then fell about 40% within 7 weeks. That is one episode, picked after the fact.
- Later practitioner calls (Jan 2024 MAC_D, Oct 2025 BeInCrypto, Sep 2026 BTC Markets/10x) are untested anecdotes. The Jan 2024 call was issued after the correction had already begun.

## regime_changes_2021_2026

1. **Sample start (Apr-May 2021).** One huge episode dominates: premium 9.5% on 1 Apr, 13.1% on 15 Apr, peak 21.7% on 19 May (a global crash day), then decay to about 0 by August (researcher's own descriptive check). KP1's sign is positive in Apr-May 2021 and negative on every day of Jun-Aug 2021. A few weeks can drive the whole result.

2. **24 Sep 2021 (SFTA deadline).** Only 4 exchanges with real-name bank partners (Upbit, Bithumb, Coinone, Korbit) kept KRW markets; 24 others ended them. Upbit held about 85% share by May 2021 (Kaiko), so the first ~5 months of the sample come from before this consolidation.

3. **2018 real-name rule, in force all sample.** Foreigners are shut out by design, so arbitrage has to go through FX remittance or USDT.

4. **2021-22 remittance crackdown.** The FSS found $7.2bn of abnormal crypto-linked remittances and cracked down, which likely changed how fast the premium closes (not measured). The no-documentation remittance limit rose from $50k to $100k from mid-2023.

5. **Travel rule from 25 Mar 2022.** At launch Upbit allowed two-way transfers with foreign exchanges only for its own affiliates (secondary source).

6. **Upbit KRW-USDT listing, 7 Jun 2024.** After it, the BTC premium measured against DEXKOUS moves almost one-for-one with the USDT premium. The researcher's own check (unverified): correlation 0.999 in levels and 0.988 in daily changes; the BTC-specific residual has sd 0.08%. Kang, Kang, Kim & Sul (2025) find parity with a ~24-minute half-life. From here the signal is a Korea-wide inflow/FX wedge.

7. **Onshore FX trading to 02:00 KST from 1 Jul 2024.** This changes how FX is discovered relative to crypto closes.

8. **Martial law, 3 Dec 2024.** The dislocation stayed inside one UTC day and does not show at the 00:00 UTC close. It only leaves a roughly -2 pp FX-timing artifact in the DEXKOUS series. The later ~3% premium was won-weakness hedging, an FX effect.

9. **Phased corporate access from 2025.**

10. **ETF era 2024+.** US spot ETF flows dominate price discovery. Korea's volume share had already fallen from 7.9% (2017) to under 2% (2021).

11. **2026 regime.** More discount days than premium days (123 of 221), with a record 35-day discount streak in Jun-Jul 2026. The premium's mean moved from about +1.5% to about 0 (own 2026 H1 figure: mean +0.05%, 43% of days negative). Causes cited: money moving to Korean stocks, no onshore derivatives, and the coming crypto tax. A regulatory focus on Bithumb in Mar 2026 adds 'plumbing' noise.

Net: at least 3-4 structural breaks inside ~5 years. The effective number of independent episodes is small, and the 90-day baseline absorbs level shifts only partly.

## data_pitfalls

- Upbit day candles run from 00:00 UTC to the next 00:00 UTC (09:00 KST, no daylight saving), so they align with Binance daily closes. Bithumb v1 day candles start at 00:00 KST (15:00 UTC), 9 hours earlier, so never mix the two exchanges' daily bars. (The Bithumb timing was not re-verified.)
- Upbit creates a candle only when trades occur, so check for missing days. The KRW-BTC history starts 2017-09-25, which fully covers 2021-05..2026-06.
- DEXKOUS is the noon New York buying rate (16:00 UTC in summer, 17:00 UTC in winter), 7-8 hours before the 00:00 UTC close. Pair FX date d with the candle that closes at 00:00 UTC on d+1: that does not look ahead. Pairing it with the candle that closes on d does look ahead.
- DEXKOUS has no weekend values: Friday's rate covers the Saturday and Sunday closes (up to about 56 hours stale). There are about 56 empty rows on US holidays in 2021-05..2026-06 (researcher's count). Forward-filling puts FX-timing noise into the premium. Korean holidays are not gaps.
- DEXKOUS is released weekly, on Mondays at 4:15 p.m. ET. It works for a backtest, but a live paper journal would face up to about 10 days of lag, so it cannot compute KP1 on time without a different FX source (not yet chosen or verified).
- The choice of FX source defines the signal. Since 2024-06-07, using Upbit KRW-USDT instead of an official USD/KRW rate removes almost the whole premium (the BTC-specific residual has sd 0.08%). A DEXKOUS-based premium is really a USDT-on-ramp-plus-FX signal. USDT versus USD is a second, smaller wedge in the Binance denominator.
- The Dec 2024 martial-law crash (Upbit low -34% within the day, closing normal) is invisible at 00:00 UTC. The DEXKOUS premium still shows a roughly -2 pp artifact, because the FX rate was taken during the won shock and the crypto closes after normalization. In May 2021 Upbit hit a -12.5% discount during the crash (Coin Metrics); whether it shows at the daily close depends on timing.
- The premium is partly a lagged-return proxy: in Choi, Lehar & Stauffer the previous day's BTC return adds about +1.3 pp of premium per +10% move. Any KP1 'hit' must be checked for overlap with plain BTC time-series momentum.
- Published premium figures are not comparable with ours. Choi, Lehar & Stauffer use daily AVERAGE prices (Korbit/Bitstamp/OANDA). CryptoQuant uses VWAP across Korean exchanges. Kaiko and Coin Metrics use various bases (Coin Metrics' 20% martial-law figure is from 1-minute reference rates).
- Warm-up: the 90-day mean needs data from about Feb 2021, which is allowed (min_start 2021-01-01). The first signal weeks fall in the peak-and-decay episode of Apr-Aug 2021, where a few weeks can dominate.
- Seo, Koo & Yang (2024) find the premium is a random walk inside a no-arbitrage band. The researcher infers that most weekly 7d-vs-90d changes are noise inside that band. The information, if any, sits in a few large excursions, so the effective sample is much smaller than about 270 weeks.

## verified_sources

- Makarov, I. & Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. Journal of Financial Economics 135(2):293-319, doi 10.1016/j.jfineco.2019.07.001 (WP: LSE FMG DP 782, Dec 2018). KRW arbitrage beta 0.22, the highest of 17 currencies (the highest average premium is ZAR, not KRW); deviations predict only RELATIVE, venue-level returns.
- Makarov, I. & Schoar, A. (2019). Price Discovery in Cryptocurrency Markets. AEA Papers and Proceedings 109:97-99. Bithumb's loading on the efficient price is 0.09 (vs 0.42-0.54 for Bitfinex); Korea's share fell by more than half at the Dec 2017-Jan 2018 peak. Horizon: seconds to 6 hours. Table sample Sep 2017 - 15 Jan 2018.
- Choi, K.J., Lehar, A. & Stauffer, R. (2019). Bitcoin Microstructure and the Kimchi Premium. SSRN 3189051, Apr 2019 SNB version (revised Jan 2022; R&R at JFQA). The previous day's BTC return raises the premium: coef 0.135 (SE 0.059). Built from daily average prices; no forward-return test.
- Borri, N. & Shakhnov, K. (2023). Cryptomarket Discounts. J. International Money and Finance 139, 102963 (WP SSRN 3124394, Feb 2018). The expensive venue underperforms the cheap one; the ~500 bp/day long-short figure appears in the working paper only, not in the published abstract. A cross-venue effect, not a directional one.
- Kang, R., Hwang, S., Shin, J. & Yoo, Y. (2026). Cross-border interactions of cryptocurrency prices and news sentiment. European Journal of Finance 32(8):1006-1036, doi 10.1080/1351847X.2026.2652365. Korean news sentiment predicts returns, but the predictive power vanishes when KRW volume exceeds USD volume. Sign and horizon not verified.
- Chae, J., Bae, K., Kang, H.-G. & Koo, B. (2025). How does investor sentiment affect the Korean premium in the Bitcoin market? Investment Analysts Journal 54(3):456-487, doi 10.1080/10293523.2024.2417331. Chat emotions predict the next hour only.
- Eom, Y. (2021). Kimchi premium and speculative trading in bitcoin. Finance Research Letters 38, 101505; re-examined by Ok, H., Kim, J. & Kim, Y. (2023), Is the Kimchi premium a speculative bubble? FRL 57, 104207. The positive relationship is 'not robust over time'.
- Seo, M.H., Koo, B. & Yang, Y.F. (2024). Nonlinear dynamics of Kimchi premium. Economic Modelling 135, 106726. Steady state 1.24%; random walk inside a threshold band, mean reversion above it.
- Cho, D. & Lee, K. (2025). Economic policy uncertainty and the Kimchi premium in the cryptocurrency market. Southern Economic Journal 92(2):359-381, doi 10.1002/soej.12750. For policy-uncertainty shocks, the FX channel lowers the premium.
- Kang, C.-M., Kang, H.-G., Kim, D. & Sul, H.K. (2025). Stablecoin and cross-border crypto market integration. Economics Letters 257, 112704. BTC and USDT kimchi premiums are cointegrated at parity, with a ~24-minute half-life.
- Choi, I. (2026). Asymmetric and Time-Varying Lag Structures in Bitcoin's Kimchi Premium. Mathematics 14(9):1501, doi 10.3390/math14091501. Tests what drives the premium; nothing survives multiple-testing correction at panel level; premium-to-BTC direction not tested.
- Radmilac, A. (2025-10-14). Is the Korean Kimchi Premium still front-running Bitcoin price? CryptoSlate (CryptoQuant data, 1 Jan - 13 Oct 2025). Level correlation about -0.06; upward zero-crossings followed by +1.7% at 7d and +6.2% at 30d; no event count, no test.
- Godbole, O. (2021-04-06). Bitcoin Analysts Say 'Kimchi Premium' Isn't Distress Signal It Once Was. CoinDesk (Lunde / Arcane; Ki Young Ju / CryptoQuant). Peaks of 63% and 47% came before corrections; Korea's volume share fell from 7.9% to under 2%.
- CryptoQuant User Guide, Korea Premium Index (accessed 2026-09). 'Over 16 percent... local top or FOMO' is a folklore threshold, not tested.
- Williams, M. (undated, ~Oct 2024). Negative Kimchi Premium Suggests Upcoming Bitcoin (BTC) Rally. CryptoPotato, citing Kaiko. Contrarian claim with no numbers.
- Deka, C. (~Jan 2024). Korean 'Kimchi' and Coinbase Premiums Indicate Possible Bitcoin Correction. CryptoPotato, citing CryptoQuant analyst MAC_D. Rule: Korea premium above 3% with a negative Coinbase premium; issued after the fall had begun.
- Hoang, N. (2025-10-13). Coinbase-Kimchi Signal Just Flashed Again. BeInCrypto via Yahoo Finance. Two earlier episodes (Mar 2024, Feb 2025).
- Kaiko Research (2024-03-11). Bitcoin Can't Stop Climbing. Premium near 7% at the all-time high; 1.5% average in 2022.
- Malwa, S. (2025-02-03). Bitcoin's 'Kimchi Premium' Jumps to 10%... CoinDesk (Bradley Park, DNTV Research). The premium spiked during a sell-off as an FX/strong-dollar effect.
- Ramirez, V. (2024-12-10). Where in the World is Crypto Trading? Coin Metrics State of the Network #289. Premium 'mostly closed'; -12.5% Upbit discount in May 2021; up to 20% on 1-minute rates during martial law.
- Barakat, A. (2026-09-01). Bitcoin Price Gap Widens as Kimchi Premium and ETF Flows Take Center Stage. Cryptonews via Yahoo (quotes also in Bloomberg, 1 Sep 2026). Lucas: crossings 'historically preceded stronger returns', a 'small signal'.
- Matos, G. (2026-03-12). Why Bitcoin's kimchi premium is on life support after South Korea targets crypto exchange. CryptoSlate. Premium typically 2-3%; now reflects 'market plumbing and access friction'.
- Upbit Developer Center, List Day Candles (GET /v1/candles/days), plus a live API check on 2026-09-25. Day candles run 00:00-00:00 UTC; first KRW-BTC candle 2017-09-25; first KRW-USDT candle 2024-06-07.
- FRED DEXKOUS and Federal Reserve H.10 'About' page. Noon New York buying rates, certified by FRBNY, updated weekly on Mondays.
- Financial Services Commission (2018-01-23). Financial Measures to Curb Speculation in Cryptocurrency Trading. Real-name accounts required; foreigners barred.
- Financial Services Commission (2021-09-22). FSC and FSS Hold Meeting to Review Registration of VASPs. Four venues kept KRW markets; 24 ended KRW services.
- Kaiko Research (2023-10-26). Exploring the Korean Crypto Market. Upbit share about 85% by May 2021; BTC is about 9% of Upbit volume.
- Park, K. / TechCrunch (2022-09-22). South Korea finds more suspicious crypto-linked foreign exchange transactions. $7.2bn in abnormal remittances; related Korea Times (2022-07-20) and KED Global (2023-02-10) pieces.
- Godbole, O. / CoinDesk (2024-12-03). Signs of bottom-fishing on Upbit after the martial-law flash crash. Plus CoinDesk (2024-12-27): ~3% premium framed as protection against the falling won.
- BigGo Finance (2026-08-11), citing CryptoQuant. 'Reverse Kimchi Premium' streak of 35 days; 123 of 221 days of 2026 at a discount; the article calls it a structural shift.

## dropped_sources

- paperswithbacktest page for Kang, Hwang, Shin & Yoo (19.7%/yr, Sharpe 0.66, 2024-2026). Dropped: a third-party replication of unknown construction that also gets the volume condition backwards.
- Kang, Hwang, Shin & Yoo (EJF 2026), sign and horizon: the 'positive sentiment leads to higher returns' and 'daily' labels come only from that third-party page. The sign is treated as unverified; only the conditional, vanishing-predictability claim is kept.
- Kang, Kang, Kim & Sul (Econ Letters 2025), extra numbers: rho = 0.9992, the 1.31% mean and the Jan-Aug 2025 sample are not in the abstract, so they are dropped. Article number corrected to 112704. The claim that 'KP1 is an on-ramp wedge' rests on the researcher's own replication, not on the paper.
- Crépellière, Pelster & Zeisberger (J. Financial Markets 2023), on arbitrage shrinking after Apr 2018: verified only at snippet level, not used.
- spotedcrypto.com (26 Mar 2026) table of negative-premium episodes. Dropped for look-ahead: the episodes were chosen at price troughs.
- Tiger Research 'Kimchi Premium 101' and DeSpread (Oct 2024). Dropped: qualitative only. DeSpread's 'Oct 2023 discount, then BTC doubled' is a community member's post, not DeSpread's analysis.
- Cryptonews (Sep 2026), correction: it does NOT repeat the CryptoSlate crossing numbers. Lucas's crossing claim is reported speech (a direct quote only in Bloomberg); Thielen is paraphrased.
- Makarov & Schoar (JFE 2020), correction: KRW has the highest arbitrage beta but not the highest average premium (ZAR 8.1%, BRL 6.7%).
- Makarov & Schoar (AEA P&P 2019), correction: the table sample ends 15 Jan 2018, not Feb 2018.
- Borri & Shakhnov, correction: the portfolio return numbers exist in the 2018 working paper only; the published JIMF abstract reports a discount half-life of 1 day and SD 3.9%.
- Choi, Lehar & Stauffer, corrections: the premium uses daily MEAN prices, not closes; KRW volume is negative only in the multivariate models.
- Seo, Koo & Yang, correction: the word 'only' in the quote was added by the researcher. The claim that small 7d-vs-90d changes sit inside the band is an inference, not a result of the paper.
- Cho & Lee, correction: the FX-channel statement applies to policy-uncertainty shocks only. 'Most premium variation is FX' is an extrapolation.
- Choi (MDPI 2026), corrections: the omitted percentage-premium specification gives higher detection rates (59.1% Gold to Premium). Whether the premium predicts BTC was not tested.
- Coin Metrics #289, correction: 'less frequently and with reduced magnitude' is a paraphrase, not a quote.
- MAC_D / CryptoPotato, correction: the call dates to about 15 Jan 2024, after BTC had already fallen 10-11% from the ETF peak, so it was not a lead.
- Kaiko (2023), correction: Bithumb went from under 10% share in Jul 2023 to over 20% in Oct 2023.
- Chae et al., correction: published online 1 Jan 2025, not 2024.
- Researcher-computed post-event BTC moves (-40%, -19%, -15%, -26%), yearly premium statistics and the 0.999 BTC-USDT correlation. Not sources: after-the-fact, own descriptive checks, not independently verified (the price levels do match repo closes).

