from app.services.risk_engine.risk_engine import analyze_materials, get_category_checks

materials = ['lana', 'botones', 'cera']
risks = analyze_materials(materials)
checks = get_category_checks('textile')

print('=== ANALISIS: Bufanda de lana con botones + vela ===')
for r in risks:
    desc = r['hazard_description'][:60]
    print(f"[{r['risk_level'].upper()}] {r['hazard_type']}: {desc}... (score: {r['risk_score']})")

print()
print('=== CHECKS OBLIGATORIOS (Textile) ===')
for c in checks:
    print(f'  - {c}')
