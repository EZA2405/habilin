# Actionability research: which estate actions can software really execute?

Research date: 20 October 2026, Asia/Manila. Question: for before-death and after-death estate work, which steps can an agent execute against real institutions now or soon, in the Philippines and elsewhere? Sources are linked inline. Vendor and news pages establish availability claims, not performance.

## Finding

No country checked lets third-party software change a beneficiary, create a power of attorney or claim a death benefit through an open API. The person does it under their own login, often with witnesses. Singapore's CPF nomination is online but needs two witnesses. Philippine SSS beneficiary updates still need Form E-4 at a branch. The UK's LPA API exists only as a 2022 design proposal. This is a deliberate security boundary, not a temporary gap, so "agent prepares, person or professional executes on the official channel, agent verifies the result" is the durable model for those acts.

Software can execute directly in three areas: identity verification, financial data and payments (open banking), and death notification. Philippine rails for identity, document verification and e-notarization went live in 2025–2026. Philippine open finance remains a pilot.

## Philippines

| Rail | Status | What an agent can really do |
|---|---|---|
| PhilSys National ID Authentication Services | Live. 56,520,952 authentications and 87 onboarded relying parties as of 17 Sep 2025, including financial institutions. Some LGUs already use it to release death certificates. [PSA](https://philsys.gov.ph/56m-national-id-authentications-largest-use-cases-in-social-protection-financial-inclusion/) | Verify the owner, heirs and representative as an accredited relying party. Requires PSA onboarding. |
| PSA e-Certificate | Launched 25 Feb 2026 for birth, marriage and **death** certificates and CENODEATH. Verifiable by QR or by reference number plus authorization code on the portal. [PSAHelpline](https://psahelpline.ph/blogs/psa-launches-e-certificate-service) | Verify a reported death before handing control to a successor. Portal, not a published API. |
| Electronic notarization | Nationwide rollout 19 Oct 2026. Three accredited platforms: NotarizeIT, TWALA, QLegal. About 100 e-notaries. SC-LRA JMC No. 1-2026 governs acceptance at LRA and Registers of Deeds. Notarial wills and wet-signature/thumbmark documents are excluded. Abroad only inside a PH embassy or consulate. [ASTIG](https://astig.ph/supreme-court-e-notarization-land-business-documents-october-19-2026/), [ABS-CBN](https://www.abs-cbn.com/news/nation/2026/10/13/sc-inks-deal-with-lra-and-sec-for-implementation-of-enotarization-1649) | Prepare an affidavit, SPA or settlement document and route it to an accredited e-notary. Coverage of extrajudicial settlement deeds is not confirmed. |
| LRA eSerbisyo | Online request for certified true copies of titles. [LRA guide](https://www.eserbisyo.lra.gov.ph/documents/guides/Request_for_Certified_True_Copy.pdf) | Person requests the copy. Agent prefills the request and checks the returned title against intake. |
| SSS beneficiaries | Not online for existing members. E-4 plus documents at a branch. [Respicio](https://www.respicio.ph/commentaries/how-to-update-sss-beneficiaries-online-in-the-philippines), [SSS E-4](https://www.sss.gov.ph/wp-content/uploads/2024/10/E4-Member-Data-Change-Request.pdf) | Detect inconsistent beneficiaries across SSS, Pag-IBIG and insurance; prepare E-4. Handoff only. |
| BSP Open Finance | Pilot only. The first live pilot (Jul 2025) covers PERA account opening with KYC data sharing. [BusinessWorld](https://bworldonline.com/banking-finance/2025/08/05/689397/bsp-launches-open-finance-pilot-for-pera/), [BSP](https://www.bsp.gov.ph/Pages/InclusiveFinance/Open%20Finance/Open%20Finance.aspx) | Not usable for estate accounts yet. A future direct rail. |
| BIR eONETT / ePay | eONETT public page describes sale and donation; estate API unverified. BIR certifies Form 1801 software providers. See [HABILIN_EVIDENCE_REPORT.md](HABILIN_EVIDENCE_REPORT.md) section 5. | Person or certified provider files and pays; agent verifies receipt. |
| E-Governance Act (RA 12254, 2025) and eGov PH / eLGU | Law and super-app exist. [Manila Bulletin](https://mb.com.ph/2025/09/14/ra-12254-a-digital-future-for-good-governance), [PIA](https://pia.gov.ph/news/egov-ph-super-app-the-future-of-govt-services-at-your-fingertips/) | Real property tax e-payment availability varies by LGU and was not verified per LGU. |

## Other countries

| Country | Direct rails that exist | Still person-executed |
|---|---|---|
| United Kingdom | Open Banking passed one billion payments in 2026 ([Open Banking Ltd](https://www.openbanking.org.uk/insights/1-billion-payments-and-counting-for-uk-open-banking/)): consented account data for asset inventory and bank payments. Tell Us Once notifies government bodies of a death ([GOV.UK](https://www.gov.uk/after-a-death/organisations-you-need-to-contact-and-tell-us-once)). Private notification networks to companies exist ([Life Ledger](https://www.lifeledger.com/service-providers/)). Professionals apply for probate online through MyHMCTS ([GOV.UK](https://www.gov.uk/government/publications/myhmcts-how-to-apply-for-probate-online)). | LPA creation: third-party API only proposed ([OPG](https://docs.modernising.opg.service.justice.gov.uk/research-development/articles/opg-as-a-service/)). |
| Singapore | Singpass Myinfo API for consented government-verified data, with staging test personas ([Singpass docs](https://docs.developer.singpass.gov.sg/docs/testing/myinfo-test-personas)). LifeSG consolidates legacy planning ([LifeSG](http://www.life.gov.sg/pages/EbR1nJj9/legacy-planning)). | CPF nomination online by the member with two witnesses; without it, Public Trustee distribution can take up to six months and charges a fee ([CPF](https://www.cpf.gov.sg/member/account-services/providing-for-your-loved-ones/making-a-cpf-nomination)). |
| Australia | Consumer Data Right live for banking ([CDR](https://www.cdr.gov.au/rollout)). Australian Death Notification Service, run by NSW Customer Service, notifies participating organisations ([ADNS](https://deathnotification.gov.au/participating-organisations)). | Estate administration and tax returns. |
| Japan | Online application for inheritance registration and the legal heir information certificate system ([MOJ](https://houmukyoku.moj.go.jp/homu/fudosan_online03.html), [MOJ certificate](https://houmukyoku.moj.go.jp/homu/page7_000014.html)). Mandatory registration deadline for older unresolved inheritances: 31 Mar 2027 (see [ESTATE_OPPORTUNITY_RESEARCH.md](ESTATE_OPPORTUNITY_RESEARCH.md)). | Filing is by the heir or a judicial scrivener. |
| Estonia | Notary-run succession register and e-notary ([Notarite Koda](https://www.notar.ee/en/registers/succession-register/), [RIK](https://www.rik.ee/en/other-services/e-notary)). | Succession proceedings run through notaries. |

## Implications for Habilin

1. Two execution modes. **Direct:** the agent calls an authorized rail (identity check, open banking data or payment). **Handoff:** the agent prepares the exact submission, the authorized person or professional executes it on the official channel, and the agent verifies the returned evidence before advancing. Safety controls are identical in both.
2. Handoff is not a weakness for beneficiary, power-of-attorney and notarial acts; every country checked requires it. It also means the agent never holds government credentials.
3. Philippine rails are recent (PSA e-Certificate Feb 2026, e-notarization Oct 2026, PhilSys authentication scaling in 2025). A product that verifies through them can be credible near term. Open finance is the missing direct rail.
4. UK, Australia and Singapore already have direct data/payment/identity rails, but also incumbents (Life Ledger, Estateably and others). They are expansion candidates, not a validated market.

## Not verified

Whether e-notarization covers extrajudicial settlement deeds; whether PSA e-Certificate verification has an API; per-LGU real property tax e-payment; PhilSys relying-party onboarding cost and timeline for a startup; Singapore and UK incumbent coverage of the same controls.
