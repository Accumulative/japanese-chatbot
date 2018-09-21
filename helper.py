
def is_kata(word):
    for c in word:
        if not (12353 <= ord(c) <= 12799):
            return False
    return True

