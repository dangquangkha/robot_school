import speech_recognition as sr

print("--- DANH SÁCH MICROPHONE ---")
mics = sr.Microphone.list_microphone_names()

for index, name in enumerate(mics):
    print(f"ID: {index} - Tên: {name}")

print("----------------------------")
print("Hãy tìm ID của thiết bị có tên là Microphone/Tai nghe bạn đang dùng.")