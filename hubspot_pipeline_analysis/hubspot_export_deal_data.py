from openai import OpenAI

# Dein API-Key direkt hier einfügen (nur für Tests!)

# Eine einfache Anfrage an GPT-4
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Was ist EBITDA?"}]
)

# Ausgabe der Antwort
print(response.choices[0].message.content)
