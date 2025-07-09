from openai import OpenAI

client = OpenAI(api_key="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")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Bonjour"}]
)

print(response.choices[0].message.content)
