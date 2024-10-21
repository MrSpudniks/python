def convert(input, inputBase = 10, outputBase = 2):
    chars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e","f"]
    input = str(input)
    sum = 0
    for i in range(1, len(input)):
        sum += chars.index(input[len(input) - i]) * (inputBase ** i - 1)
    input = str(sum)
    sum = 0
    return input

print(convert("10"))