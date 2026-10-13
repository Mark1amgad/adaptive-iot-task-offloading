from offloading_rl.action import (
    ACTION_name,
    ACTION_NUMBER,
    normalize_mask,
)

print(ACTION_name)
print(ACTION_NUMBER)
print(normalize_mask())
print(normalize_mask([True, False, True]))