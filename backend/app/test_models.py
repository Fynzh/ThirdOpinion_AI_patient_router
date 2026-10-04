import os
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

giga = GigaChat(
    credentials=GIGACHAT_KEY,
    scope="GIGACHAT_API_PERS",
    model="GigaChat-2",          # временно, чтобы клиент создался
    verify_ssl_certs=False,
)

print("Доступные модели:")
for model in giga.get_models().data:
    print(f"  - {model.id_}")