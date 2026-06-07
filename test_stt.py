from core.stt_engine import stt

print('Speak now in English or Arabic (5 seconds)...')
result = stt.listen(duration=5)
print(f'Text: {result["text"]}')
print(f'Language: {result["language"]}')
print('STT Test Complete!')