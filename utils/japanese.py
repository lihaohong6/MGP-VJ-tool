import functools
import re

hiragana_pattern = re.compile("[\u3041-\u3096]")
katakana_pattern = re.compile("[\u30A0-\u30FF]")
kanji_pattern = re.compile("[\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]")


def is_hiragana(c: str) -> bool:
    return not not hiragana_pattern.fullmatch(c)


def is_katakana(c: str) -> bool:
    return not not katakana_pattern.fullmatch(c)


def is_kana(c: str) -> bool:
    return is_hiragana(c) or is_katakana(c)


def is_kanji(c: str) -> bool:
    return c == "々" or not not kanji_pattern.fullmatch(c)


def is_japanese(c: str) -> bool:
    return is_kana(c) or is_kanji(c)


def furigana_local(lyrics: str) -> str:
    open_parentheses = ['(', '（']
    closing_parentheses = [')', '）']
    lines = lyrics.split("\n")
    result = []
    for line in lines:
        prev_end = 0
        line_result = []
        for index in range(len(line)):
            if index < prev_end:
                continue
            if line[index] not in open_parentheses or index == 0 or not is_kanji(line[index - 1]):
                continue
            symbol = closing_parentheses[open_parentheses.index(line[index])]
            close_index = line.find(symbol, index + 1)
            furigana = line[index + 1:close_index]
            if close_index == -1 or index + 1 == close_index or \
                    not functools.reduce(lambda a, b: a and b,
                                         [is_hiragana(c) for c in furigana]):
                continue
            kanji_start = index - 1
            while kanji_start >= 0 and is_kanji(line[kanji_start]):
                kanji_start -= 1
            kanji_start += 1
            if kanji_start > 0:
                line_result.append(line[prev_end:kanji_start])
            line_result.append(f"{{{{photrans|{line[kanji_start:index]}|{furigana}"
                               f"}}}}")
            prev_end = close_index + 1
        line_result.append(line[prev_end:])
        result.append("".join(line_result))
    return "\n".join(result)
