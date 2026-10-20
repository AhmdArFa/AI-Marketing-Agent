# Playbook: Periodic Maintenance Reminder

Audience: dealer marketing (car owners). Source: 4S PLUS Periodic Maintenance Service.

Trigger: months since last service reach the interval (default 6) or km since
last service reach the interval (default 10,000), and no JobCard is open.

Steps:
1. Python builds the maintenance_due segment nightly.
2. TypeScript prepares a WhatsApp reminder per customer, referencing their own
   last service date and their service history by chassis.
3. Human approves the batch. Nothing sends before approval.
4. Replies create an Appointment in the system. No shows get one follow up, then stop.

Message frame (Arabic first, simple):
"عربيتك ميعاد صيانتها الدورية قرب. آخر صيانة كانت من {months} شهور، وتاريخ
صيانة عربيتك محفوظ بالكامل عندنا. احجز ميعادك وسيب الباقي علينا."

KPI: appointments booked per 100 reminders. Guardrail: no invented discounts,
no percentages, no pressure language.
