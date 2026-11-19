import os
import json
import sys
import urllib.request
import urllib.error
import base64
import mimetypes
import time
import unicodedata

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()

def fix_korean_text(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).strip()

# key.txt 읽기 및 전처리
key_path = os.path.join(get_script_dir(), "key.txt")
if not os.path.exists(key_path):
    print(Fore.RED + f"[오류] key.txt 파일이 없습니다! 위치: {key_path}")
    input("\nEnter 키를 눌러 종료...")
    sys.exit()

with open(key_path, "r", encoding="utf-8-sig") as f:
    api_key = f.read().strip()

api_key = api_key.replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "").strip("'").strip('"')

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "Yeongjaewon Chatbot"
}

def print_banner(user_name, theme_name):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + Style.BRIGHT + "==========================================================================")
    print(Fore.MAGENTA + Style.BRIGHT + f"                   🤖 영재원 챗봇 ({user_name} / {theme_name} 모드)             ")
    print(Fore.CYAN + Style.BRIGHT + "==========================================================================")
    print(Fore.YELLOW + "  • 질문, 아이디어 정리, 코드, 데이터 분석 등 무엇이든 물어보세요.")
    print(Fore.GREEN + "  • 이미지 첨부: 이미지 파일 경로를 입력하거나 이 창으로 드래그해 오시면 됩니다.")
    print(Fore.RED + "  • 대화 종료: 'exit' 또는 '종료' 입력")
    print(Fore.CYAN + Style.BRIGHT + "==========================================================================" + Style.RESET_ALL)
    print()

def encode_image_to_url(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"
    with open(image_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"

print(Fore.CYAN + Style.BRIGHT + "==========================================")
user_name = input(Fore.YELLOW + Style.BRIGHT + "이름을 입력해 주세요: " + Fore.WHITE).strip()
if not user_name:
    user_name = "사용자"

print(Fore.CYAN + Style.BRIGHT + "\n대화 테마를 선택해 주세요:")
print(Fore.GREEN + "1. 논리적 (명확하고 객관적이며 결론 중심의 답변)")
print(Fore.GREEN + "2. 기본 (자연스럽고 균형 잡힌 친절한 답변)")
print(Fore.GREEN + "3. 감정적 (공감과 대화감을 더한 친근한 답변)")

theme_choice = input(Fore.YELLOW + Style.BRIGHT + "선택 (1/2/3, 엔터 시 기본): " + Fore.WHITE).strip()

base_instruction = f"당신은 영재원 챗봇입니다. 사용자의 이름은 '{user_name}'입니다. 절대로 제미나이(Gemini)나 구글(Google)이라는 명칭을 언급하거나 티내지 마세요."

if theme_choice == "1":
    theme_name = "논리적"
    system_prompt = f"{base_instruction} 불필요한 감정 표현이나 서두는 빼고, 명확하고 논리적이며 결론 중심의 객관적인 답변을 제공해 주세요."
elif theme_choice == "3":
    theme_name = "감정적"
    system_prompt = f"{base_instruction} 따뜻하고 친근하며, 사용자의 생각에 공감하고 대화하듯 편안한 어조로 답변해 주세요."
else:
    theme_name = "기본"
    system_prompt = f"{base_instruction} 자연스럽고 깔끔한 어조로 정돈된 답변을 제공해 주세요."

print_banner(user_name, theme_name)

messages = [{"role": "system", "content": system_prompt}]

while True:
    try:
        user_input_raw = input(Fore.GREEN + Style.BRIGHT + f"👤 {user_name} > " + Fore.WHITE).strip()
        user_input = fix_korean_text(user_input_raw)

        if user_input.lower() in ["exit", "quit", "종료", "q"]:
            print(Fore.MAGENTA + f"\n[영재원 챗봇] 대화를 종료합니다. 수고하셨습니다!\n")
            break

        if not user_input:
            continue

        clean_input = user_input.strip("'").strip('"')

        if os.path.isfile(clean_input) and clean_input.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
            try:
                img_url = encode_image_to_url(clean_input)
                print(Fore.YELLOW + f"📸 이미지 파일 확인됨: {os.path.basename(clean_input)}")
                prompt = input(Fore.GREEN + f"   └─ 이 이미지와 함께 물어볼 내용을 입력해 주세요: " + Fore.WHITE).strip()
                if not prompt:
                    prompt = "이 이미지를 자세히 설명하고 분석해 주세요."

                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": img_url}}
                    ]
                })
            except Exception as img_err:
                print(Fore.RED + f"[오류] 이미지 처리 실패: {img_err}\n")
                continue
        else:
            messages.append({"role": "user", "content": user_input})

        print(Fore.YELLOW + Style.BRIGHT + "\n🤖 [영재원 챗봇] ", end="")
        loading_text = "생각하는 중..."
        for char in loading_text:
            sys.stdout.write(Fore.CYAN + char)
            sys.stdout.flush()
            time.sleep(0.02)

        # OpenRouter 엔드포인트에 맞춘 Gemini Flash ID
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": messages,
            "max_tokens": 1000
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            bot_text = result["choices"][0]["message"]["content"]

            messages.append({"role": "assistant", "content": bot_text})

            sys.stdout.write("\r" + " " * 80 + "\r")
            print(Fore.BLUE + Style.BRIGHT + "🤖 [영재원 챗봇]")
            print(Fore.WHITE + bot_text)
            print(Fore.CYAN + "\n--------------------------------------------------------------------------\n")

    except urllib.error.HTTPError as e:
        sys.stdout.write("\r" + " " * 80 + "\r")
        error_msg = e.read().decode("utf-8")
        print(Fore.RED + f"\n[오류 발생 - 코드 {e.code}]")
        print(Fore.RED + f"상세 에러 내용: {error_msg}\n")
        if messages:
            messages.pop()
    except KeyboardInterrupt:
        print(Fore.MAGENTA + f"\n\n[영재원 챗봇] 대화를 종료합니다.")
        break
    except Exception as e:
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(Fore.RED + f"[기타 오류]: {e}\n")

input(Fore.YELLOW + "Enter 키를 눌러 창을 닫으세요...")