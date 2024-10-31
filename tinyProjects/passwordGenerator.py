#!/usr/local/bin/python3
# Password Generator Project
import random
import math

l_lettr = 'abcdefghijklmnopqrstuvwxyz'
u_lettr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
numbers = '0123456789'
symbols = '!#$%&()*+'

print("Password Generator:")
total_length = int(input("Length?\n"))

# Set a minimum length of 8
if total_length < 8:
    print("No! Too short!\nDefaulting to 8.")
    total_length = 8

min_per_category = max(1, total_length // 4)
remaining_length = total_length - (min_per_category * 4)

# Randomly distribute remaining length
nr_l_letters = min_per_category + random.randint(0, remaining_length)
nr_u_letters = min_per_category + random.randint(0, remaining_length - (nr_l_letters - min_per_category))
nr_numbers = min_per_category + random.randint(0, remaining_length - (nr_l_letters + nr_u_letters - min_per_category * 2))
nr_symbols = total_length - (nr_l_letters + nr_u_letters + nr_numbers)

# Build password
password_list = []
password_list += random.choices(l_lettr, k=nr_l_letters)
password_list += random.choices(u_lettr, k=nr_u_letters)
password_list += random.choices(numbers, k=nr_numbers)
password_list += random.choices(symbols, k=nr_symbols)

random.shuffle(password_list)
final_password = "".join(password_list)
print("\nGenerated Password:", final_password)

# Calculate password entropy
character_pool_size = len(l_lettr) + len(u_lettr) + len(numbers) + len(symbols)  # 71 total
entropy = total_length * math.log2(character_pool_size)
print(f"\nPassword Entropy: {entropy:.2f} bits\n")

# Calculate approx. brute force times
def format_time(seconds):
    years, remainder = divmod(seconds, 60 * 60 * 24 * 365.25)
    days, remainder = divmod(remainder, 60 * 60 * 24)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(years)} years, {int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

guess_rates = {
    "1,000 guesses/s": 1_000,
    "1 billion guesses/s": 1_000_000_000,
    "100 trillion guesses/s": 100_000_000_000_000
}

print("Expected Brute-Force Time:")
for rate_desc, rate in guess_rates.items():
    time_seconds = (2 ** (entropy - 1)) / rate
    formatted_time = format_time(time_seconds)
    print(f" - {rate_desc}: ~{formatted_time}")
