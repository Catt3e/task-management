import re
from datetime import datetime, time, timedelta
from dateparser import parse
from underthesea import word_tokenize

class PromptController:
    # -------------------------
    # UTILITIES
    # -------------------------
    LOCATION_PATTERNS = [
        # allow letters (ascii + unicode), digits, dot, dash, underscore
        re.compile(r"\b(phòng|p)\s*[\w\.\-_/]+\b", re.IGNORECASE | re.UNICODE),
        re.compile(r"\b[A-Za-z0-9]{1,5}\.[0-9]{1,4}\b"),   # HB.103, D5.201 ...
        re.compile(r"\b[A-Za-z0-9]+\-[0-9]{1,4}\b"),       # D5-201
        re.compile(r"\b(phòng|p)\s*\d+\b", re.IGNORECASE), # phòng 203
    ]

    default_time = {
        "sáng": time(9, 0),
        "trưa": time(12, 0),
        "chiều": time(15, 0),
        "tối": time(19, 0),
        "khuya": time(22, 0),
    }

    DATE_REGEX = re.compile(r"\b([0-3]?\d/[0-1]?\d(?:/[0-9]{2,4})?)\b")

    PATTERN_NEXT_WEEK = re.compile(r"\b(thứ|thu)\s*([2-7])\s*((tuần|tuan)\s*(sau|tới|toi))\b", re.IGNORECASE)
    PATTERN_NEXT_MONTH_DAY = re.compile(r"\b(ngày|ngay)\s*(\d{1,2})\s*((tháng|thang)\s*(sau|tới|toi))\b", re.IGNORECASE)
    PATTERN_CURRENT_MONTH_DAY = re.compile(r"\b((ngày|ngay)?)\s*(\d{1,2})\s*((tháng|thang)\s*(này|nay))\b", re.IGNORECASE)

    REPETITIVE_TASK = {
        ("mỗi ngày", "hang ngay", "hàng ngày", "hằng ngày", "moingay", "moingày"): 0,
        ("mỗi tuần", "hang tuan", "hàng tuần", "hằng tuần", "moituan", "moituần"): 1,
        ("mỗi tháng", "hang thang", "hàng tháng", "hằng tháng", "moithang", "moitháng"): 2,
        ("mỗi năm", "hang nam", "hàng năm", "hằng năm", "moinam", "moinăm"): 3,
    }

    RELATIVE_DATES = {
        ("hôm nay", "hnay", "ngày hôm nay", "bữa nay", "sáng nay", "trưa nay", "chiều nay", "tối nay", "khuya nay"): "hôm nay",
        ("hom nay", "ngay hom nay", "bua nay", "sang nay", "trua nay", "chieu nay", "toi nay", "khuya nay"): "hôm nay",
        ("mai", "ngày mai", "bữa mai", "sáng mai", "trưa mai", "chiều mai", "tối mai", "khuya mai"): "mai",
        ("hom mai", "ngay mai", "bua mai", "sang mai", "trua mai", "chieu mai", "toi mai", "khuya mai"): "mai",
        ("mốt", "ngày mốt", "bữa mốt", "sáng mốt", "trưa mốt", "chiều mốt", "tối mốt", "khuya mốt"): "mốt",
        ("mot", "ngay mot", "bua mot", "sang mot", "trua mot", "chieu mot", "toi mot", "khuya mot"): "mốt",
    }

    RELATIVE_DATE_OFFSETS = {
        "hôm nay": 0,
        "mai": 1,
        "mốt": 2,
    }

    TIME_MODIFIERS = {
        "sáng": "am",
        "sang": "am",
        "am": "am",
        "trưa": "noon",
        "trua": "noon",
        "chiều": "pm",
        "chieu": "pm",
        "pm": "pm",
        "tối": "pm",
        "toi": "pm",
        "đêm": "pm",
        "dem": "pm",
        "khuya": "pm",
    }

    RAW_WEEKDAYS = {
        ("thứ 2", "thứ hai", "t2", "th2", "thứ2", "t.2", "thu 2", "thu hai"): "thứ 2",
        ("thứ 3", "thứ ba",  "t3", "th3", "thứ3", "t.3", "thu 3", "thu ba"): "thứ 3",
        ("thứ 4", "thứ tư",  "t4", "th4", "thứ4", "t.4", "thu 4", "thu tư"): "thứ 4",
        ("thứ 5", "thứ năm", "t5", "th5", "thứ5", "t.5", "thu 5", "thu năm"): "thứ 5",
        ("thứ 6", "thứ sáu", "t6", "th6", "thứ6", "t.6", "thu 6", "thu sáu"): "thứ 6",
        ("thứ 7", "thứ bảy", "t7", "th7", "thứ7", "t.7", "thu 7", "thu bảy"): "thứ 7",
        ("chủ nhật", "cn", "chu nhat", "chunhat"): "chủ nhật",
    }

    # flatten
    WEEKDAY_MAP = {}
    for keys, val in RAW_WEEKDAYS.items():
        for k in keys:
            norm = k.strip().lower()
            WEEKDAY_MAP[norm] = val




    # TOKENIZE

    @staticmethod
    def tokenize(text: str) -> list[str]:
        print("\n",f"Tokenizing text: {text}")
        return word_tokenize(text, format="text").split()



    # CHUẨN HÓA VĂN BẢN
    # -----------------------------------------------------------------------------------------

    # Chuẩn hóa thời gian

    @staticmethod
    def _normalize_time_text(text: str) -> str:
        t = text.lower()
        t = re.sub(r"\b(\d)\s*h\b", r"\1h", t)   # "10 h" -> "10h"
        t = re.sub(r"\b(\d)\s*giờ\b", r"\1giờ", t)
        t = re.sub(r"\b(\d)\s*g\b", r"\1g", t)
        # unify minutes shorthand
        t = re.sub(r"\b([0-5]?\d)\s*p\b", r"\1p", t)
        t = re.sub(r"\bphút\b", "p", t)
        # normalize apostrophe minute 15' -> 15p
        t = re.sub(r"\'", "p", t)
        # normalize multiple spaces
        t = re.sub(r"\s+", " ", t).strip()
        return t

    # Chuẩn hóa ngày trong tuần

    @classmethod
    def normalize_weekday(cls, text: str) -> str:
        lowered = text.lower()
        print("\nBefore weekday normalization:", lowered)

        # Lặp từng nhóm alias
        for aliases, unified in cls.RAW_WEEKDAYS.items():
            # Tạo regex cho toàn bộ alias trong nhóm bằng (alias1|alias2|alias3...)
            group_pattern = r"\b(" + "|".join(map(re.escape, aliases)) + r")\b"
            lowered_new = re.sub(group_pattern, unified, lowered, flags=re.IGNORECASE)

            if lowered_new != lowered:
                print(f"Replaced {aliases} → '{unified}': {lowered_new}")

            lowered = lowered_new

        lowered = re.sub(r"\s+", " ", lowered).strip()
        print("After weekday normalization:", lowered)
        return lowered


    # Chuẩn hóa ngày với từ khóa tương đối

    @classmethod
    def normalize_relative(cls, text: str) -> str:
        lowered = text.lower()
        print("\nBefore relative dates normalization:", lowered)

        for aliases, unified in cls.RELATIVE_DATES.items():
            pattern = r"\b(" + "|".join(map(re.escape, aliases)) + r")\b"
            lowered_new = re.sub(pattern, unified, lowered, flags=re.IGNORECASE)

            if lowered_new != lowered:
                print(f"Replaced {aliases} → '{unified}': {lowered_new}")

            lowered = lowered_new

        lowered = re.sub(r"\s+", " ", lowered).strip()
        print("After relative dates normalization:", lowered)
        return lowered





    # NHẬN BIẾT THÔNG TIN TỪ VĂN BẢN
    # --------------------------------------------------


    # Nhận biết hôm sau/tuần sau/ngày XX tháng này

    @classmethod
    def detect_complex_date(cls, text: str):

        m = cls.PATTERN_NEXT_WEEK.search(text)
        if m:
            print(m.group(0))
            weekday = int(m.group(2))
            today = datetime.today()
            # map: thứ 2 -> python weekday 0
            target_weekday = weekday - 2
            next_week = today + timedelta(days=7)
            days_ahead = (target_weekday - next_week.weekday()) % 7
            target_date = next_week + timedelta(days=days_ahead)
            return m.group(0), target_date

        m = cls.PATTERN_NEXT_MONTH_DAY.search(text)
        if m:
            print(m.group(0))
            day = int(m.group(2))
            today = datetime.today()
            month = today.month + 1
            year = today.year
            if month > 12:
                month = 1
                year += 1
            try:
                target_date = datetime(year, month, day)
            except ValueError:
                print(f"Invalid date for next month day pattern: {day}/{month}/{year}")
                return m.group(0), None
            return m.group(0), target_date
        
        m = cls.PATTERN_CURRENT_MONTH_DAY.search(text)
        if m:
            print(m.group(0))
            day = int(m.group(3))
            today = datetime.today()
            month = today.month
            year = today.year
            try:
                target_date = datetime(year, month, day)
            except ValueError:
                print(f"Invalid date for current month day pattern: {day}/{month}/{year}")
                return m.group(0), None
            return m.group(0), target_date

        return None, None



    # Nhận biết ngày
    
    @classmethod
    def detect_date(cls, text: str):

        lowered = text.lower()
        print(f"Lowered text for date detection: {lowered}")

        # 2. Check tuần sau/tháng sau patterns
        raw_complex, complex_dt = cls.detect_complex_date(text)
        if raw_complex and complex_dt:
            print(f"Detected complex date: {raw_complex} -> {complex_dt}")
            return raw_complex, complex_dt
        else:
            print("Date detection: no complex patterns (Tuần sau/tháng sau) matched.")

        # Check ngày trong tuần
        for weekday_name in cls.WEEKDAY_MAP.values():
            if re.search(r"\b" + re.escape(weekday_name) + r"\b", lowered):
                today = datetime.today()
                target_weekday = list(cls.WEEKDAY_MAP.values()).index(weekday_name)
                days_ahead = (target_weekday - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7  # next week
                dt = today + timedelta(days=days_ahead)
                print(f"Detected weekday date: {weekday_name} -> {dt}")
                return weekday_name, dt

        # 3. Check relative keywords
        for rel_word, offset in cls.RELATIVE_DATE_OFFSETS.items():
            if re.search(r"\b" + re.escape(rel_word) + r"\b", lowered):
                dt = datetime.today() + timedelta(days=offset)
                print(f"Detected relative date: {rel_word} -> {dt}")
                return rel_word, dt

        # 4. Check format dd/mm/yyyy
        m = cls.DATE_REGEX.search(text)
        if m:
            raw = m.group(1)
            parsed = parse(raw, languages=["vi"])
            print(f"Detected date regex: {raw} -> {parsed}")
            return raw, parsed

        # 5. Check lại lần nữa bằng dateparser
        parsed = parse(text, languages=["vi"])
        if parsed:
            print(f"Detected date fallback: {text} -> {parsed}")
            return str(parsed.date()), parsed

        return None, None


    # Nhận biết lặp lại công việc
    @classmethod
    def detect_repetitive_task(cls, text: str):
        text = text.lower()

        prefix = r"(lặp lại|lap lai|lặp|lap|mỗi|moi)"
        
        for aliases, rec_type in cls.REPETITIVE_TASK.items():
            # ví dụ aliases = ("hàng ngày", "mỗi ngày", "daily")
            cycle_pattern = r"(" + "|".join(map(re.escape, aliases)) + r")"
            
            # pattern: có prefix + chu kỳ
            pattern = rf"{prefix}(?:\s+\w+){{0,2}}\s*{cycle_pattern}"

            if re.search(pattern, text, flags=re.IGNORECASE):
                return rec_type

        return -1


        # Nhận biết thời gian
    @classmethod
    def detect_time(cls, raw_text: str):
        text = cls._normalize_time_text(raw_text)
        results = []

        # Regex patterns
        patterns = [
            # 4. HH h kém MM
            (4, re.compile(r"\b([01]?\d|2[0-3])\s*(?:h|giờ|gio|g)\s*(?:kém|kem)\s*([0-5]?\d)\s*(?:p|phút|phut|')?\b",re.IGNORECASE)),
            # 5. HH rưỡi/nửa
            (5, re.compile(r"\b([01]?\d|2[0-3])(?:\s*(?:h|giờ|gio|g))?\s*(?:rưỡi|ruoi|nửa|nua)\b",re.IGNORECASE)),
            # 1. HH:MM or HH.MM
            (1, re.compile(r"\b([01]?\d|2[0-3])[:\.]([0-5]\d)\b")),
            # 2. HH h MM
            (2, re.compile(r"\b([01]?\d|2[0-3])\s*(?:h|giờ|gio|g)\s*([0-5]?\d)\s*(?:p|phút|'|phut)?\b", re.IGNORECASE)),
            # 3. HH h (đúng) — minute = 0
            (3, re.compile(r"\b([01]?\d|2[0-3])\s*(?:h|giờ|gio|g)(?:\s*(?:đúng|dung))?\b", re.IGNORECASE)),
        ]

        modifier_regex = re.compile(r"(sáng|trưa|chiều|tối|đêm|khuya|am|pm|sang|trua|chieu|toi|dem)\b", re.IGNORECASE)

        checked = set()

        def apply_modifier(hour, modifier):
            if not modifier:
                return hour

            mod = modifier.lower()

            if mod in ("sáng", "am", "sang"):
                return 0 if hour == 12 else hour
            if mod in ("chiều", "pm", "tối", "đêm", "khuya", "chieu", "toi", "dem"):
                return hour + 12 if hour < 12 else hour
            return hour
        
        checked_spans = []

        for pat_id, pat in patterns:
            for m in pat.finditer(text):
                span = m.span()
                if span in checked:
                    continue
                checked.add(span)

                raw = m.group(0)
                g = m.groups()

                # Parse hour/minute depending on pattern
                if pat_id in (1, 2):
                    print(f"Matched pattern {pat_id} with groups: {g}")
                    hour = int(g[0])
                    minute = int(g[1])

                elif pat_id == 3:
                    print(f"Matched pattern {pat_id} with groups: {g}")
                    hour = int(g[0])
                    minute = 0

                elif pat_id == 4:
                    print(f"Matched pattern {pat_id} with groups: {g}")
                    base_hour = int(g[0])
                    minus_m = int(g[1])
                    hour = (base_hour - 1) if (base_hour - 1) >= 0 else 23
                    minute = 60 - minus_m

                elif pat_id == 5:
                    print(f"Matched pattern {pat_id} with groups: {g}")
                    hour = int(g[0])
                    minute = 30

                else:
                    continue

                print(f"Extracted time: {hour}:{minute}")

                # Look for modifiers
                around = text[max(span[0]-20, 0): span[1]+20]
                mod_match = modifier_regex.search(around)
                modifier = mod_match.group(1) if mod_match else None

                # Apply modifier
                hour = apply_modifier(hour, modifier)

                hour %= 24
                minute %= 60

                iso = f"{hour:02d}:{minute:02d}"

                results.append({
                    "raw": raw,
                    "hour": hour,
                    "minute": minute,
                    "iso_time": iso,
                    "modifier": modifier
                })

        # Deduplicate
        seen = set()
        unique = []
        for r in results:
            key = (r["raw"], r["iso_time"])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        first = unique[0] if unique else None
        actual_time = (
            datetime.strptime(first["iso_time"], "%H:%M").time()
            if first else None
        )

        return first, unique if unique else actual_time





    # MAIN
    # --------------------------------------------------
    @classmethod
    def extract(cls, prompt: str):
        
        # Text used explicitly for date detection
        date_text = prompt

        date_text = cls.normalize_weekday(date_text)
        date_text = cls.normalize_relative(date_text)
        print(f"Text after normalization: {date_text}")


        tokens = cls.tokenize(prompt)
        text = " ".join(tokens)
        
        # Detect time
        raw_time, time_val = cls.detect_time(text)
        print("\n",f"Time detected(extract): {raw_time} -> Time_val: {time_val}")

        if not time_val:
            # If no time detected, try to assign default time based on keywords
            for keyword, def_time in cls.default_time.items():
                if re.search(r"\b" + re.escape(keyword) + r"\b", text.lower()):
                    time_val = def_time
                    raw_time = keyword
                    print(f"Default time assigned based on keyword '{keyword}': {time_val}")
                    break
            if not time_val:
                time_val = [
                    {
                        "raw": "default",
                        "hour": cls.default_time["sáng"].hour,
                        "minute": cls.default_time["sáng"].minute,
                        "iso_time": cls.default_time["sáng"].strftime("%H:%M"),
                        "modifier": "am"
                    }
                ]
                raw_time = ["default"]
                print(f"No time keyword found. Defaulting to: {time_val}")

        # Detect date
        raw_date, date_val = cls.detect_date(date_text)
        print("\n",f"Date detected: {raw_date} -> {date_val}")


        result = {}

        # Only add fields that actually exist

        print("\n\n", "Final extraction results:")
        if raw_date:
            result["date_raw"] = raw_date
            result["date"] = date_val
            print(f"Date: {raw_date} -> {date_val}")

        if raw_time:
            result["time_raw"] = raw_time
            result["time"] = time_val
            print(f"Time: {raw_time} -> {time_val}")

        repetitive_task = cls.detect_repetitive_task(text)
        if repetitive_task != -1:
            result["repetitive_task"] = repetitive_task
            print(f"Repetitive task detected: {repetitive_task}")

        # Extract title
        title = cls.extract_title(date_text, result)
        title = cls.extract_title(cls._normalize_time_text(prompt), result)
        result["title"] = title

        return cls.clean_output(result)

    


    # HELPERS
    # --------------------------------------------------------------------------------
    # Chuẩn hóa kết quả trích lọc và trả về định dạng cuối cùng
    @classmethod
    def clean_output(cls, raw):
        print("\n\n", "Cleaning output:", raw, "\n")
        date_raw = raw.get("date_raw")
        date = raw.get("date")
        time_raw = raw.get("time_raw")
        time_info = raw.get("time")
        loc = raw.get("location")

        # chuẩn hóa date
        if isinstance(date, datetime):
            date_only = date.date()
            print(f"Date is datetime, extracted date only: {date_only}")
        else:
            date_only = date
            print(f"Final date only: {date_only}")

        # chuẩn hóa time
        if isinstance(time_info, list) and time_info:
            time_str = time_info[0].get("iso_time")
            print(f"Time is list, extracted first iso_time: {time_str}")
        
        elif isinstance(time_info, dict):
            time_str = time_info.get("iso_time")
            print(f"Time is dict, extracted iso_time: {time_str}")
        else:
            time_str = None
            print("No valid time string found.")

        # convert time string
        time_obj = None
        if time_str:
            time_obj = datetime.strptime(time_str, "%H:%M").time()

        # verify
        final_dt, msg = cls.verify_time_set(date_only, time_obj)

        return {
            "date": date_only,
            "time": time_str,
            "datetime": final_dt,
            "location": loc,
            "raw": {
                "date": raw.get("date_raw"),
                "time": raw.get("time_raw"),
                "location": raw.get("location")
            },
            "repetitive_task": raw.get("repetitive_task"),
            "message": msg,
            "datetime": final_dt,
            "title": raw.get("title")
        }



    @classmethod
    def verify_time_set(cls, date, time):
        if not date or not time:
            return None, None

        dt_combined = datetime.combine(date, time)
        now = datetime.now()
        message = "Không có tin nhắn."

        if dt_combined <= now:
            message = (
                "Kiếm tra thấy thời gian đặt task đã qua. Task đã được tạo, "
                "tuy nhiên vui lòng kiểm tra và điều chỉnh thời gian nếu cần thiết."
            )

            # move to next month, keep same time
            year = dt_combined.year
            month = dt_combined.month + 1

            if month > 12:
                month = 1
                year += 1

            try:
                dt_combined = dt_combined.replace(year=year, month=month)
            except ValueError:
                # ngày 31 + next month (30 ngày) gây crash
                # fallback thành ngày 1 tháng sau
                dt_combined = dt_combined.replace(
                    year=year, month=month, day=1
                )

        return dt_combined, message
    


    # Trích lọc tiêu đề task

    # Xóa các phần đã trích lọc được khỏi văn bản gốc

    @classmethod
    def strip_known_chunks(cls, text: str, extraction_result: dict):
        cleaned = text

        # 1. Xóa raw date
        if extraction_result.get("date_raw"):
            cleaned = cleaned.replace(extraction_result["date_raw"], "")

        # 2. Xóa raw time
        raw_time = extraction_result.get("time_raw")
        if isinstance(raw_time, dict):
            cleaned = cleaned.replace(raw_time["raw"], "")
        elif isinstance(raw_time, str):
            cleaned = cleaned.replace(raw_time, "")

        # 3. Xóa từ khóa lặp lại nếu có
        rep_type = extraction_result.get("repetitive_type")
        if rep_type not in (-1, None):
            for aliases in cls.REPETITIVE_TASK.keys():
                for word in aliases:
                    cleaned = re.sub(r"\b" + re.escape(word) + r"\b", "", cleaned, flags=re.IGNORECASE)

            # xóa prefix lặp lại
            cleaned = re.sub(r"\b(lặp lại|lap lai|lặp|lap)\b", "", cleaned, flags=re.IGNORECASE)

        return cleaned
    
    STOPWORD_TRASH = [
    "nhắc", "nhắc tôi", "nhớ", "giúp", "giúp tao", "giúp tôi",
    "tạo", "tạo task", "thêm task", "giùm", "làm ơn", "please",
    "một cái", "cho tao", "cho tôi", "cho mình", "giùm tao", "giùm tôi", "giùm mình",
    "nhac toi", "nho", "giup", "giup tao", "giup toi",
    "tao", "tao task", "them task", "lam on",
    ]

    # Xóa các từ rác không cần thiết khỏi tiêu đề

    @classmethod
    def strip_trash_words(cls, text: str):
        cleaned = text
        for w in cls.STOPWORD_TRASH:
            cleaned = re.sub(r"\b" + re.escape(w) + r"\b", "", cleaned, flags=re.IGNORECASE)

        if cleaned.endswith("nha."):
            cleaned = cleaned[:-4]
        elif cleaned.endswith("nha"):
            cleaned = cleaned[:-3]
        return cleaned

    # Chuẩn hóa tiêu đề

    @classmethod
    def cleanup_title(cls, text: str):
        text = re.sub(r"[.,;:!?]+$", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # Trích lọc tiêu đề từ prompt và kết quả trích lọc thông tin
    @classmethod
    def extract_title(cls, prompt: str, extraction_result: dict):
        stripped = cls.strip_known_chunks(prompt, extraction_result)
        stripped = cls.strip_trash_words(stripped)
        cleaned = cls.cleanup_title(stripped)

        if cleaned == "":
            cleaned = "Task mới"
        return cleaned