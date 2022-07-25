import sys
import json

if __name__ == "__main__":
    # option 파일 선택
    if len(sys.argv) == 1:
        option_file = "./options_standalone.json"
    else:
        option_file = sys.argv[1]

    # config.json 에서 options 항목 읽기
    with open("config.json") as f:
        Options = json.load(f)["options"]

    # 로그 파일 경로 변경
    Options["log"]["filename"] = "./log/sds_wallpad.log"

    # 파일 생성
    with open(option_file, "w") as f:
        json.dump(Options, f, indent="\t")
